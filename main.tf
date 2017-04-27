# Example terraform configuration for a lambda function that uses invokust to run locust

data "aws_caller_identity" "current" {}

resource "aws_lambda_function" "invokust_example" {
  filename      = "invokust_example.zip"
  function_name = "invokust_example"
  role          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/service-role/lambda_basic_execution"
  handler       = "aws_lambda_example.lambda_handler"
  runtime       = "python2.7"
  timeout       = 300
  description   = "A function that runs a locust load test"
  environment {
    variables = {
      LOCUST_NUM_REQUESTS="10"
      LOCUST_LOCUSTFILE="locustfile_example.py"
      LOCUST_HOST="http://example.com"
      LOCUST_HATCH_RATE="1"
      LOCUST_NUM_CLIENTS="1"
    }
  }
}
