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

resource "aws_instance" "frontend" {
  ami           = data.aws_ami.amazon_linux_2023.id
  instance_type = "t3.micro"
  subnet_id     = aws_subnet.public[0].id
  key_name      = aws_key_pair.frontend.key_name
  
  vpc_security_group_ids = [aws_security_group.frontend.id]
  associate_public_ip_address = true
  iam_instance_profile        = aws_iam_instance_profile.frontend_profile.name

  user_data = <<-EOF
              #!/bin/bash
              dnf update -y
              dnf install -y nginx
              systemctl start nginx
              systemctl enable nginx
              
              cat <<HTML > /usr/share/nginx/html/index.html
              <!DOCTYPE html>
              <html>
              <head><title>SK Manager - EC2</title></head>
              <body><h1>SK Manager Frontend (EC2)</h1><p>Running on awsa-rds instance</p></body>
              </html>
              HTML
              EOF

  tags = {
    Name        = "awsa-rds"
    Project     = var.project_name
    Environment = "staging"
  }
}
