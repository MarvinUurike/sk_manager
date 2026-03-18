resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "photos" {
  bucket = "${var.project_name}-photos-${var.environment}-${random_id.bucket_suffix.hex}"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "photos" {
  bucket = aws_s3_bucket.photos.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_cors_configuration" "photos" {
  bucket = aws_s3_bucket.photos.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE", "HEAD"]
    allowed_origins = ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# DynamoDB Tables
resource "aws_dynamodb_table" "equipment" {
  name           = "${var.project_name}-equipment-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "equipment_id"

  attribute {
    name = "equipment_id"
    type = "S"
  }

  tags = {
    Name        = "${var.project_name}-equipment-table"
    Environment = var.environment
  }
}

resource "aws_dynamodb_table" "lending" {
  name           = "${var.project_name}-lending-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "lending_id"

  attribute {
    name = "lending_id"
    type = "S"
  }

  attribute {
    name = "equipment_id"
    type = "S"
  }

  global_secondary_index {
    name               = "EquipmentIndex"
    hash_key           = "equipment_id"
    projection_type    = "ALL"
  }

  tags = {
    Name        = "${var.project_name}-lending-table"
    Environment = var.environment
  }
}
