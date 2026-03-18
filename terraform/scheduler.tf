# Scheduler IAM Role
resource "aws_iam_role" "scheduler_lambda" {
  name = "${var.project_name}-scheduler-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "scheduler_policy" {
  name = "${var.project_name}-scheduler-policy"
  role = aws_iam_role.scheduler_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "ec2:StartInstances",
          "ec2:StopInstances",
          "ec2:DescribeInstances"
        ]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

data "archive_file" "scheduler_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/scheduler_handler.py"
  output_path = "${path.module}/scheduler_deploy.zip"
}

resource "aws_lambda_function" "scheduler" {
  filename      = data.archive_file.scheduler_zip.output_path
  function_name = "${var.project_name}-scheduler-${var.environment}"
  role          = aws_iam_role.scheduler_lambda.arn
  handler       = "scheduler_handler.handler"
  runtime       = "python3.12"
  timeout       = 30

  source_code_hash = data.archive_file.scheduler_zip.output_base64sha256
}

# EB Scheduler Role
resource "aws_iam_role" "eb_scheduler" {
  name = "${var.project_name}-eb-scheduler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "scheduler.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "eb_scheduler_invoke" {
  name = "${var.project_name}-eb-scheduler-invoke"
  role = aws_iam_role.eb_scheduler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "lambda:InvokeFunction"
      Resource = aws_lambda_function.scheduler.arn
    }]
  })
}

# Rules
resource "aws_scheduler_schedule" "stop_staging" {
  name       = "${var.project_name}-stop-staging"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression          = "cron(0 19 ? * MON-FRI *)"
  schedule_expression_timezone = "UTC"

  target {
    arn      = aws_lambda_function.scheduler.arn
    role_arn = aws_iam_role.eb_scheduler.arn
    input    = jsonencode({ "action": "STOP" })
  }
}

resource "aws_scheduler_schedule" "start_staging" {
  name       = "${var.project_name}-start-staging"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression          = "cron(0 6 ? * MON-FRI *)"
  schedule_expression_timezone = "UTC"

  target {
    arn      = aws_lambda_function.scheduler.arn
    role_arn = aws_iam_role.eb_scheduler.arn
    input    = jsonencode({ "action": "START" })
  }
}
