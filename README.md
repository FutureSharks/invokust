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
'{"fail": {}, "locust_host": "http://example.com", "num_requests": 10, "success": {"/": {"num_requests": 10, "total_rps": 0.9611445710106717, "median_response_time": 110, "total_rpm": 57.6686742606403, "request_type": "GET", "min_response_time": 107, "max_response_time": 143}}}'
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
'{"fail": {}, "locust_host": "http://example.com", "num_requests": 10, "success": {"/": {"num_requests": 10, "total_rps": 0.9806702027934636, "median_response_time": 110, "total_rpm": 58.84021216760782, "request_type": "GET", "min_response_time": 105, "max_response_time": 140}}}'
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
aws lambda invoke --function-name invokust_example output.log
{
    "StatusCode": 200
}

cat output.log
"{\"num_requests_fail\": 0, \"num_requests\": 10, \"success\": {\"/\": {\"num_requests\": 10, \"total_rps\": 1.0718836271241832, \"median_response_time\": 99, \"total_rpm\": 64.31301762745099, \"request_type\": \"GET\", \"min_response_time\": 95, \"max_response_time\": 100}}, \"locust_host\": \"http://example.com\", \"fail\": {}, \"num_requests_success\": 10}"
```
