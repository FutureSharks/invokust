# invokust

A small wrapper for [locust](http://locust.io/) to enable invoking locust load tests from within Python. This gives more flexibility for automation such as QA/CI/CD tests and also makes it possible to run locust on [AWS Lambda](https://aws.amazon.com/lambda/).

## Installation

Install via pip:

```
pip install invokust
```

## Examples

Running a load test using a locust file:

```python
import invokust

settings = invokust.create_settings(
    locustfile='locustfile_example.py',
    host='http://example.com',
    num_requests=10,
    num_clients=1,
    hatch_rate=1
    )

loadtest = invokust.LoadTest(settings)
loadtest.run()
loadtest.stats()
'{"num_requests_fail": 0, "num_requests": 10, "success": {"/": {"median_response_time": 210, "total_rpm": 48.13724156297892, "request_type": "GET", "min_response_time": 210, "response_times": {"720": 1, "210": 7, "820": 1, "350": 1}, "num_requests": 10, "response_time_percentiles": {"65": 210, "95": 820, "75": 350, "85": 720, "55": 210}, "total_rps": 0.802287359382982, "max_response_time": 824, "avg_response_time": 337.2}}, "locust_host": "http://example.com", "fail": {}, "num_requests_success": 10}'
```

Running a load test without locust file:

```python
import invokust

from locust import HttpLocust, TaskSet, task

class Task(TaskSet):
    @task()
    def get_home_page(self):
        '''
        Gets /
        '''
        self.client.get("/")

class WebsiteUser(HttpLocust):
    task_set = Task

settings = invokust.create_settings(
    classes=[WebsiteUser],
    host='http://example.com',
    num_requests=10,
    num_clients=1,
    hatch_rate=1
    )

loadtest = invokust.LoadTest(settings)
loadtest.run()
loadtest.stats()
'{"num_requests_fail": 0, "num_requests": 10, "success": {"/": {"median_response_time": 330, "total_rpm": 40.53552561950598, "request_type": "GET", "min_response_time": 208, "response_times": {"230": 1, "1000": 1, "780": 1, "330": 1, "1100": 1, "210": 3, "790": 1, "670": 1}, "num_requests": 10, "response_time_percentiles": {"65": 780, "95": 1100, "75": 790, "85": 1000, "55": 670}, "total_rps": 0.6755920936584331, "max_response_time": 1111, "avg_response_time": 552.8}}, "locust_host": "http://example.com", "fail": {}, "num_requests_success": 10}'
```

## Running on AWS Lambda

<img src="http://d0.awsstatic.com/Graphics/lambda-icon-smallr1.png" alt="Lambda logo" height="100"><img src="http://locust.io/static/img/logo.png" alt="Locust logo" height="100">

[AWS Lambda](https://aws.amazon.com/lambda/) is a great tool for load testing as it is very cheap and highly scalable.

When calling the `create_settings` function, an argument can be passed to get the settings from environment variables. This allows the load test settings to be changed using the environment variables of the Lambda function:

```python
settings = invokust.create_settings(from_environment=True)
```

The environment variables are:

  - LOCUST_LOCUSTFILE: Locust file to use for the load test
  - LOCUST_CLASSES: Names of locust classes to use for the load test (instead of a locustfile). If more than one, separate with comma.
  - LOCUST_HOST: The host to run the load test against
  - LOCUST_NUM_REQUESTS: Total number of requests to make
  - LOCUST_NUM_CLIENTS: Number of clients to simulate
  - LOCUST_HATCH_RATE: Number of clients per second to start

A time limit can also be placed on the load test to suit the Lambda execution time limit of 300 seconds. This will ensure you get the statistics even if the load test doesn't fully complete within 300 seconds:

```python
loadtest.run(timeout=298)
```

The load test statistics can be logged using standard python logging. The statistics are then recorded in [Cloudwatch Logs](https://eu-central-1.console.aws.amazon.com/cloudwatch/home?region=eu-central-1#logs) for summing, parsing or processing:

```python
logger.info(loadtest.stats())
```

A full example is in [aws_lambda_example.py](aws_lambda_example.py).

### Creating a Lambda function

The process for running a locust test on Lambda involves [creating a zip file](http://docs.aws.amazon.com/lambda/latest/dg/lambda-python-how-to-create-deployment-package.html) of the locust load test, creating a Lambda function and then triggering the function.

Install invokust (and its dependencies) python packages locally:

```
pip install invokust --target=python-packages
```

Or if running on a Mac (python packages need to be compiled for 64 bit Linux) you can use docker:

```
docker run -it --volume=$PWD/python-packages:/python-packages python:2.7 bash -c "pip install invokust --target=/python-packages"
```

Create the zip file:

```
zip -q -r invokust_example.zip aws_lambda_example.py locustfile_example.py python-packages
```

Then create the Lambda function using [Terraform](https://www.terraform.io/) and the example [main.tf](main.tf) file:

```
terraform apply
...
```

Finally invoke the function using the [AWS CLI](https://aws.amazon.com/cli/) (or use the [Lambda console](https://eu-central-1.console.aws.amazon.com/lambda/home?region=eu-central-1#/functions)):

```
aws lambda invoke --function-name invokust_example lambda_output
{
    "StatusCode": 200
}

cat lambda_output
{"num_requests_fail": 0, "num_requests": 10, "success": {"/": {"median_response_time": 120, "total_rpm": 58.08219539770968, "request_type": "GET", "min_response_time": 102, "response_times": {"120": 8, "100": 2}, "num_requests": 10, "response_time_percentiles": {"65": 120, "95": 120, "75": 120, "85": 120, "55": 120}, "total_rps": 0.9680365899618281, "max_response_time": 120, "avg_response_time": 115.1}}, "memory_limit": "128", "remaining_time": 287401, "function_version": "$LATEST", "function_name": "invokust_example", "locust_host": "http://example.com", "log_group_name": "/aws/lambda/invokust_example", "fail": {}, "num_requests_success": 10, "invoked_function_arn": "arn:aws:lambda:eu-central-1:111111111111:function:invokust_example", "log_stream_name": "2017/04/27/[$LATEST]f730a111b1404e4511185f2e85775704", "aws_request_id": "d63ed907-1b1a-11e7-ad79-e1b811d67f11"}
```

Or you can also pass settings directly to the function:

```
aws lambda invoke --function-name invokust_example --payload '{"locustfile": "locustfile_example.py", "host": "http://example.com", "num_requests": "10", "num_clients": "1", "hatch_rate": "1"}' lambda_output
{
    "StatusCode": 200
}
```
