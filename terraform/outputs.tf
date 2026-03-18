# REST API URL
output "api_url" {
  description = "URL of the API Gateway"
  value       = aws_apigatewayv2_stage.main.invoke_url
}

# S3 Photos Bucket
output "photos_bucket_name" {
  description = "Name of the photos S3 bucket"
  value       = aws_s3_bucket.photos.id
}

# EC2 Frontend
output "frontend_public_ip" {
  description = "Public IP of the awsa-rds frontend instance"
  value       = aws_instance.frontend.public_ip
}

# PostgreSQL Database
output "rds_endpoint" {
  description = "Endpoint of the RDS instance"
  value       = aws_db_instance.history.endpoint
}
