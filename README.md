# invokust

A tool for running [Locust](http://locust.io/) load tests from within Python without the need to use the locust command line. This gives more flexibility for automation such as QA/CI/CD tests and also makes it possible to run locust on [AWS Lambda](https://aws.amazon.com/lambda/) for ultimate scalability.

## Installation

Install via pip:

```
pip3 install invokust
```

## Examples

Running a load test using a locust file:

```python
import invokust

settings = invokust.create_settings(
    locustfile='locustfile_example.py',
    host='http://example.com',
    num_clients=1,
    hatch_rate=1,
    run_time='3m'
    )

loadtest = invokust.LocustLoadTest(settings)
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
    num_clients=1,
    hatch_rate=1,
    run_time='3m'
    )

loadtest = invokust.LocustLoadTest(settings)
loadtest.run()
loadtest.stats()
'{"num_requests_fail": 0, "num_requests": 10, "success": {"/": {"median_response_time": 330, "total_rpm": 40.53552561950598, "request_type": "GET", "min_response_time": 208, "response_times": {"230": 1, "1000": 1, "780": 1, "330": 1, "1100": 1, "210": 3, "790": 1, "670": 1}, "num_requests": 10, "response_time_percentiles": {"65": 780, "95": 1100, "75": 790, "85": 1000, "55": 670}, "total_rps": 0.6755920936584331, "max_response_time": 1111, "avg_response_time": 552.8}}, "locust_host": "http://example.com", "fail": {}, "num_requests_success": 10}'
```

## Running Locust on AWS Lambda

<img src="http://d0.awsstatic.com/Graphics/lambda-icon-smallr1.png" alt="Lambda logo" height="100"><img src="http://locust.io/static/img/logo.png" alt="Locust logo" height="100">

[AWS Lambda](https://aws.amazon.com/lambda/) is a great tool for load testing as it is very cheap (or free) and highly scalable.

There are many load testing tools such as [ab](https://httpd.apache.org/docs/2.4/programs/ab.html) and [wrk](https://github.com/wg/wrk). Then there are other cloud based load testing options such as [BlazeMeter](https://www.blazemeter.com/) or [Loader](https://loader.io/) and some more DIY solutions that use AWS Lambda too such as [Goad](https://goad.io/) or [serverless-artillery](https://github.com/Nordstrom/serverless-artillery). But these all have the same drawback: They are too simplistic. They can perform simple GET or POST requests but can't accurately emulate more complex behaviour. e.g. browsing a website, selecting random items, filling a shopping cart and checking out. But with [Locust](http://locust.io/) this is possible.

Included is an example function for running Locust on AWS Lambda, `lambda_locust.py`.

### Creating a Lambda function

The process for running a locust test on Lambda involves [creating a zip file](http://docs.aws.amazon.com/lambda/latest/dg/lambda-python-how-to-create-deployment-package.html) of the locust load test, creating a Lambda function and then triggering the function.

Install invokust (and its dependencies) python packages locally:

```
pip3 install invokust --target=python-packages
```

Or if running on a Mac (python packages need to be compiled for 64 bit Linux) you can use docker:

```
docker run -it --volume=$PWD/python-packages:/python-packages python:3.6 bash -c "pip install invokust --target=/python-packages"
```

Create the zip file:

```
zip -q -r lambda_locust.zip lambda_locust.py locustfile_example.py python-packages
```

Then create the Lambda function using using the AWS CLI:

```
aws lambda create-function --function-name lambda_locust --timeout 300 --runtime python3.6 --role arn:aws:iam::9999999999:role/lambda_basic_execution --handler lambda_locust.handler --zip-file fileb://lambda_locust.zip
```

Or [Terraform](https://www.terraform.io/) and the example [main.tf](main.tf) file:

```
terraform apply
...
```

### Invoking the function

The Locust settings can be passed to the Lambda function or can be set from environment variables. The environment variables are:

  - LOCUST_LOCUSTFILE: Locust file to use for the load test
  - LOCUST_CLASSES: Names of locust classes to use for the load test (instead of a locustfile). If more than one, separate with comma.
  - LOCUST_HOST: The host to run the load test against
  - LOCUST_NUM_CLIENTS: Number of clients to simulate
  - LOCUST_HATCH_RATE: Number of clients per second to start
  - LOCUST_RUN_TIME: The time the test should run for
  - LOCUST_LOGLEVEL: Level of logging

[AWS CLI](https://aws.amazon.com/cli/) example with Locust settings in a payload:

```
aws lambda invoke --function-name lambda_locust --invocation-type RequestResponse --payload '{"locustfile": "locustfile_example.py", "host":"https://example.com", "num_requests":"20", "num_clients": "1", "hatch_rate": "1", "run_time":"3m"}' output.txt
{
    "StatusCode": 200
}
cat output.txt
"{\"success\": {\"GET_/\": {\"request_type\": \"GET\", \"num_requests\": 20, \"min_response_time\": 86, \"median_response_time\": 93 ...
```

Python boto3 example:

```python
import json
from boto3.session import Session
from botocore.client import Config

session = Session()
config = Config(connect_timeout=10, read_timeout=310)
client = session.client('lambda', config=config)

lambda_payload = {
    'locustfile': 'locustfile_example.py',
    'host': 'https://example.com',
    'num_clients': '1',
    'hatch_rate': 1,
    'run_time':'3m'
}

response = client.invoke(FunctionName='lambda_locust', Payload=json.dumps(lambda_payload))
json.loads(response['Payload'].read())
'{"success": {"GET_/": {"request_type": "GET", "num_requests": 20, "min_response_time": 87, "median_response_time": 99, "avg_response_time": 97.35 ...
```

### Running a real load test

Lambda function execution time is limited to a maximum of 5 minutes. To run a real load test the function will need to be invoked repeatedly and likely in parallel to generate enough load. To manage this there is a class called `LambdaLoadTest` that can manage invoking the function in parallel loops and collecting the statistics.

```python
import logging
from invokust.aws_lambda import LambdaLoadTest

logging.basicConfig(level=logging.INFO)

lambda_payload = {
    'locustfile': 'locustfile_example.py',
    'host': 'https://example.com',
    'num_clients': '1',
    'hatch_rate': 1,
    'run_time':'3m'
}

load_test = LambdaLoadTest(
  lambda_function_name='lambda_locust',
  threads=2,
  ramp_time=0,
  time_limit=30,
  lambda_payload=lambda_payload
)

load_test.run()
print(load_test.get_summary_stats())
```

The output:
```
INFO:root:
Starting load test...
Function name: lambda_locust
Ramp time: 0s
Threads: 2
Lambda payload: {'locustfile': 'locustfile_example.py', 'host': 'https://example.com', 'num_clients': '1', 'hatch_rate': 1, 'run_time': '3m'}
Start ramping down after: 30s
INFO:root:thread started
INFO:root:Invoking lambda...
INFO:root:threads: 1, rpm: 0, time elapsed: 0s, total requests from finished threads: 0, request fail ratio: 0, invocation error ratio: 0
INFO:root:threads: 1, rpm: 0, time elapsed: 3s, total requests from finished threads: 0, request fail ratio: 0, invocation error ratio: 0
INFO:root:thread started
INFO:root:Invoking lambda...
INFO:root:threads: 2, rpm: 0, time elapsed: 6s, total requests from finished threads: 0, request fail ratio: 0, invocation error ratio: 0
INFO:root:threads: 2, rpm: 0, time elapsed: 9s, total requests from finished threads: 0, request fail ratio: 0, invocation error ratio: 0
INFO:root:threads: 2, rpm: 0, time elapsed: 12s, total requests from finished threads: 0, request fail ratio: 0, invocation error ratio: 0
INFO:root:threads: 2, rpm: 0, time elapsed: 15s, total requests from finished threads: 0, request fail ratio: 0, invocation error ratio: 0
INFO:root:threads: 2, rpm: 0, time elapsed: 18s, total requests from finished threads: 0, request fail ratio: 0, invocation error ratio: 0
INFO:root:threads: 2, rpm: 0, time elapsed: 21s, total requests from finished threads: 0, request fail ratio: 0, invocation error ratio: 0
INFO:root:threads: 2, rpm: 0, time elapsed: 24s, total requests from finished threads: 0, request fail ratio: 0, invocation error ratio: 0
INFO:root:threads: 2, rpm: 0, time elapsed: 27s, total requests from finished threads: 0, request fail ratio: 0, invocation error ratio: 0
INFO:root:threads: 2, rpm: 0, time elapsed: 30s, total requests from finished threads: 0, request fail ratio: 0, invocation error ratio: 0
INFO:root:threads: 2, rpm: 0, time elapsed: 33s, total requests from finished threads: 0, request fail ratio: 0, invocation error ratio: 0
INFO:root:Time limit reached. Starting ramp down...
INFO:root:Waiting for all Lambdas to return. This may take up to 3m.
INFO:invokust.aws_lambda.lambda_load_test:Lambda invocation complete. Requests (errors): 1867 (0), execution time: 180066ms, sleeping: 0s
INFO:root:thread finished
INFO:invokust.aws_lambda.lambda_load_test:Lambda invocation complete. Requests (errors): 1884 (0), execution time: 180065ms, sleeping: 0s
INFO:root:thread finished
{'lambda_invocation_count': 2, 'total_lambda_execution_time': 360131, 'requests_total': 3751, 'request_fail_ratio': 0.0, 'invocation_error_ratio': 0.0}
```

There is also an example CLI tool for running a load test, `invokr.py`:

```
$ .invokr.py --function_name=lambda_locust --locust_file=locustfile_example.py --locust_host=https://example.com --threads=1 --time_limit=30 --locust_clients=20
2020-06-06 19:41:01,476 INFO   MainThread
Starting load test...
Function name: lambda_locust
Ramp time: 0s
Threads: 1
Lambda payload: {'locustfile': 'locustfile_example.py', 'host': 'https://example.com', 'num_clients': 20, 'hatch_rate': 10, 'run_time': '10s'}
Start ramping down after: 30s
2020-06-06 19:41:01,476 INFO   thread_1    thread started
2020-06-06 19:41:01,476 INFO   thread_1    Invoking lambda...
2020-06-06 19:41:01,482 INFO   MainThread  threads: 1, rpm: 0, time elapsed: 0s, total requests from finished threads: 0, request fail ratio: 0, invocation error ratio: 0
2020-06-06 19:41:04,488 INFO   MainThread  threads: 1, rpm: 0, time elapsed: 3s, total requests from finished threads: 0, request fail ratio: 0, invocation error ratio: 0
2020-06-06 19:41:07,490 INFO   MainThread  threads: 1, rpm: 0, time elapsed: 6s, total requests from finished threads: 0, request fail ratio: 0, invocation error ratio: 0
2020-06-06 19:41:10,491 INFO   MainThread  threads: 1, rpm: 0, time elapsed: 9s, total requests from finished threads: 0, request fail ratio: 0, invocation error ratio: 0
2020-06-06 19:41:13,492 INFO   MainThread  threads: 1, rpm: 0, time elapsed: 12s, total requests from finished threads: 0, request fail ratio: 0, invocation error ratio: 0
2020-06-06 19:41:13,569 INFO   thread_1    Lambda invocation complete. Requests (errors): 267 (0), execution time: 10273ms, sleeping: 0s
2020-06-06 19:41:13,569 INFO   thread_1    Invoking lambda...
2020-06-06 19:41:16,493 INFO   MainThread  threads: 1, rpm: 1325, time elapsed: 15s, total requests from finished threads: 267, request fail ratio: 0.0, invocation error ratio: 0.0
2020-06-06 19:41:19,499 INFO   MainThread  threads: 1, rpm: 1325, time elapsed: 18s, total requests from finished threads: 267, request fail ratio: 0.0, invocation error ratio: 0.0
2020-06-06 19:41:22,501 INFO   MainThread  threads: 1, rpm: 1325, time elapsed: 21s, total requests from finished threads: 267, request fail ratio: 0.0, invocation error ratio: 0.0
2020-06-06 19:41:24,006 INFO   thread_1    Lambda invocation complete. Requests (errors): 276 (0), execution time: 10399ms, sleeping: 0s
2020-06-06 19:41:24,006 INFO   thread_1    Invoking lambda...
2020-06-06 19:41:25,504 INFO   MainThread  threads: 1, rpm: 1587, time elapsed: 24s, total requests from finished threads: 543, request fail ratio: 0.0, invocation error ratio: 0.0
2020-06-06 19:41:28,505 INFO   MainThread  threads: 1, rpm: 1587, time elapsed: 27s, total requests from finished threads: 543, request fail ratio: 0.0, invocation error ratio: 0.0
2020-06-06 19:41:31,507 INFO   MainThread  threads: 1, rpm: 1587, time elapsed: 30s, total requests from finished threads: 543, request fail ratio: 0.0, invocation error ratio: 0.0
2020-06-06 19:41:34,349 INFO   thread_1    Lambda invocation complete. Requests (errors): 278 (0), execution time: 10313ms, sleeping: 0s
2020-06-06 19:41:34,349 INFO   thread_1    Invoking lambda...
2020-06-06 19:41:34,508 INFO   MainThread  threads: 1, rpm: 1613, time elapsed: 33s, total requests from finished threads: 821, request fail ratio: 0.0, invocation error ratio: 0.0
2020-06-06 19:41:34,508 INFO   MainThread  Time limit reached. Starting ramp down...
2020-06-06 19:41:34,508 INFO   MainThread  Waiting for all Lambdas to return. This may take up to 10s.
2020-06-06 19:41:44,926 INFO   thread_1    Lambda invocation complete. Requests (errors): 284 (0), execution time: 10460ms, sleeping: 0s
2020-06-06 19:41:44,926 INFO   thread_1    thread finished
2020-06-06 19:41:45,542 INFO   MainThread  Aggregated results: {"requests": {"GET_/": {"median_response_time": 390.0, "total_rps": 27.009331465404667, "avg_response_time": 476.0309271870121, "max_response_time": 2320.3701972961426, "min_response_time": 161.10563278198242, "response_times": {"histogram": [397, 565, 68, 14, 11, 5, 11, 12, 13, 9], "bins": [160.0, 374.0, 588.0, 802.0, 1016.0, 1230.0, 1444.0, 1658.0, 1872.0, 2086.0, 2300.0]}, "total_rpm": 1620.55988792428, "num_requests": 1105}}, "failures": {}, "num_requests": 1105, "num_requests_fail": 0, "total_lambda_execution_time": 41445, "lambda_invocations": 4, "approximate_cost": 8.691200000000001e-05, "request_fail_ratio": 0.0, "invocation_error_ratio": 0.0, "locust_settings": {"locustfile": "locustfile_example.py", "host": "https://example.com", "num_clients": 20, "hatch_rate": 10, "run_time": "10s"}, "lambda_function_name": "lambda_locust", "threads": 1, "ramp_time": 0, "time_limit": 30}
2020-06-06 19:41:45,542 INFO   MainThread
============================================================
Ramp up time: 0s
Started ramp down after 30s (time_limit)
Thread count: 1
Lambda invocation count: 4
Lambda invocation error ratio: 0.0
Cumulative lambda execution time: 41445ms
Total requests sent: 1105
Total requests failed: 0
Total request failure ratio: 0.0

2020-06-06 19:41:45,542 INFO   MainThread  ===========================================================================================================================
2020-06-06 19:41:45,543 INFO   MainThread  TYPE    NAME                                                #REQUESTS    MEDIAN   AVERAGE       MIN       MAX  #REQS/SEC
2020-06-06 19:41:45,543 INFO   MainThread  ===========================================================================================================================
2020-06-06 19:41:45,543 INFO   MainThread  GET     /                                                        1105     390.0    476.03    161.11   2320.37      27.01
2020-06-06 19:41:45,543 INFO   MainThread  Exiting...