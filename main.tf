# Example terraform configuration for a lambda function that uses invokust to run locust

provider "aws" {
  region = "eu-west-1"
}

resource "aws_iam_role" "lambda_basic_execution" {
  name               = "lambda_basic_execution"
  path               = "/service-role/"
  assume_role_policy = "${data.aws_iam_policy_document.lambda_basic_execution_assume_role.json}"
}

data "aws_iam_policy_document" "lambda_basic_execution_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "lambda_basic_execution" {
  statement {
    effect  = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "lambda_basic_execution" {
  name        = "lambda_basic_execution"
  description = "Basic execution policy for a Lambda function"
  policy      =  "${data.aws_iam_policy_document.lambda_basic_execution.json}"
}

resource "aws_iam_policy_attachment" "lambda_basic_execution" {
  name       = "lambda_basic_execution"
  roles      = ["${aws_iam_role.lambda_basic_execution.name}"]
  policy_arn = "${aws_iam_policy.lambda_basic_execution.arn}"
}

resource "aws_lambda_function" "lambda_locust" {
  filename      = "lambda_locust.zip"
  function_name = "lambda_locust"
  role          = "${aws_iam_role.lambda_basic_execution.arn}"
  handler       = "lambda_locust.handler"
  runtime       = "python3.7"
  timeout       = 300
  description   = "A function that runs a locust load test"
  environment {
    variables = {
      LOCUST_RUN_TIME = "3m"
      LOCUST_LOCUSTFILE="locustfile_example.py"
      LOCUST_HOST="http://example.com"
      LOCUST_HATCH_RATE="1"
      LOCUST_NUM_CLIENTS="1"
    }
  }
}
