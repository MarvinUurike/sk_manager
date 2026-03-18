variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-north-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "sk-manager"
}

variable "environment" {
  description = "Environment"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "sk_manager_history"
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "sk_admin"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
  default     = "SecurePass123!ChangeMe"
}
