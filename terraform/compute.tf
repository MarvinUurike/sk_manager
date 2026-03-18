# Lambda IAM Role
resource "aws_iam_role" "lambda_exec" {
  name = "${var.project_name}-lambda-role-${var.environment}"

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

resource "aws_iam_role_policy_attachment" "lambda_policy" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_role_policy" "lambda_custom" {
  name = "${var.project_name}-lambda-custom-policy"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["dynamodb:*"]
        Resource = [
          aws_dynamodb_table.equipment.arn,
          aws_dynamodb_table.lending.arn,
          "${aws_dynamodb_table.lending.arn}/index/*"
        ]
      },
      {
        Effect   = "Allow"
        Action   = ["s3:*"]
        Resource = [
          aws_s3_bucket.photos.arn,
          "${aws_s3_bucket.photos.arn}/*"
        ]
      }
    ]
  })
}

# Main API Lambda
data "archive_file" "dummy" {
  type        = "zip"
  output_path = "${path.module}/dummy_lambda.zip"
  source {
    content  = "def handler(event, context): return {'statusCode': 200, 'body': 'Hello'}"
    filename = "lambda_handler.py"
  }
}

resource "aws_lambda_function" "api" {
  filename      = data.archive_file.dummy.output_path
  function_name = "${var.project_name}-api-${var.environment}"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "lambda_handler.handler"
  runtime       = "python3.12"
  timeout       = 20

  vpc_config {
    subnet_ids         = aws_subnet.private[*].id
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      EQUIPMENT_TABLE = aws_dynamodb_table.equipment.name
      LENDING_TABLE   = aws_dynamodb_table.lending.name
      PHOTOS_BUCKET   = aws_s3_bucket.photos.id
      DB_HOST         = aws_db_instance.history.address
      DB_NAME         = var.db_name
      DB_USER         = var.db_username
      DB_PASS         = var.db_password
      DB_PORT         = "5432"
      REGION          = var.aws_region
    }
  }
}

# API Gateway
resource "aws_apigatewayv2_api" "main" {
  name          = "${var.project_name}-api-${var.environment}"
  protocol_type = "HTTP"
  
  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization"]
  }
}

resource "aws_apigatewayv2_stage" "main" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "v1"
  auto_deploy = true
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"

  connection_type    = "INTERNET"
  integration_method = "POST"
  integration_uri    = aws_lambda_function.api.invoke_arn
}

resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}
