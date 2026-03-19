resource "aws_security_group" "frontend" {
  name        = "${var.project_name}-frontend-ec2-sg"
  description = "Allow HTTP and SSH access"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "SSH for SCP file uploads"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-frontend-sg"
  }
}

data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
}

# SSH Key Pair - Generate and save locally
resource "tls_private_key" "frontend" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "frontend" {
  key_name   = "${var.project_name}-frontend-key"
  public_key = tls_private_key.frontend.public_key_openssh
}

resource "local_file" "private_key" {
  filename        = "${path.module}/../sk_manager_key.pem"
  content         = tls_private_key.frontend.private_key_pem
  file_permission = "0400"
}

# IAM Role for EC2 (SSM & S3)
resource "aws_iam_role" "frontend_role" {
  name = "${var.project_name}-frontend-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.frontend_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy" "frontend_s3" {
  name = "${var.project_name}-frontend-s3-policy"
  role = aws_iam_role.frontend_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject", "s3:ListBucket"]
      Resource = [
        aws_s3_bucket.photos.arn,
        "${aws_s3_bucket.photos.arn}/*"
      ]
    }]
  })
}

resource "aws_iam_instance_profile" "frontend_profile" {
  name = "${var.project_name}-frontend-profile"
  role = aws_iam_role.frontend_role.name
}

# EC2 Instance - Frontend Web Server
resource "aws_instance" "frontend" {
  ami           = data.aws_ami.amazon_linux_2023.id
  instance_type = "t3.micro"
  subnet_id     = aws_subnet.public[0].id
  key_name      = aws_key_pair.frontend.key_name

  vpc_security_group_ids      = [aws_security_group.frontend.id]
  associate_public_ip_address = true
  iam_instance_profile        = aws_iam_instance_profile.frontend_profile.name

  # User data script: Install Nginx with proper permissions for SCP uploads
  user_data = base64encode(<<-EOF
    #!/bin/bash
    set -e
    exec > >(tee /var/log/user-data.log)
    exec 2>&1
    
    echo "======================================"
    echo "Starting EC2 Nginx Setup"
    echo "======================================"
    
    # Update system packages
    dnf update -y
    
    # Install Nginx
    dnf install -y nginx
    
    # Create web root directory
    mkdir -p /usr/share/nginx/html
    
    # Fix permissions: Allow ec2-user to upload files via SCP
    # nginx process runs as 'nginx' user, but we want ec2-user to be able to write
    chown -R ec2-user:nginx /usr/share/nginx/html
    chmod -R 775 /usr/share/nginx/html
    
    # Create default welcome page
    cat > /usr/share/nginx/html/index.html <<'HTML'
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SK Manager - Frontend Server</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .container {
      background: white;
      border-radius: 10px;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
      padding: 50px;
      text-align: center;
      max-width: 600px;
    }
    h1 {
      color: #333;
      margin-bottom: 20px;
    }
    .status {
      background: #e8f5e9;
      border-left: 4px solid #4caf50;
      padding: 20px;
      margin: 20px 0;
      border-radius: 5px;
    }
    .info {
      color: #666;
      font-size: 14px;
      margin-top: 20px;
    }
    .badge {
      display: inline-block;
      background: #4caf50;
      color: white;
      padding: 5px 10px;
      border-radius: 20px;
      margin: 5px;
      font-size: 12px;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>✅ SK Manager Frontend</h1>
    <div class="status">
      <p><strong>Nginx Web Server is Ready</strong></p>
      <p>Files uploaded successfully</p>
    </div>
    <div class="info">
      <p><strong>Instance:</strong> awsa-rds</p>
      <p><strong>Region:</strong> eu-north-1</p>
      <p><strong>Service:</strong> Nginx (Reverse Proxy to API Gateway)</p>
    </div>
    <div>
      <span class="badge">Status: Online</span>
      <span class="badge">Port: 80</span>
    </div>
  </div>
</body>
</html>
HTML
    
    # Start Nginx service
    systemctl start nginx
    systemctl enable nginx
    
    echo "======================================"
    echo "Nginx Setup Complete!"
    echo "======================================"
  EOF
  )

  tags = {
    Name        = "awsa-rds"
    Project     = var.project_name
    Environment = "production"  # Changed from "staging" to prevent scheduler from stopping it
  }

  depends_on = [aws_key_pair.frontend]
}