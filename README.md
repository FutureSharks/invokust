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
  - LOCUST_RUN_TIME: The time the test should run for.

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
INFO:root:
Starting load test
Function: lambda_locust
Ramp time: 0
Threads: 2
Lambda payload: {'locustfile': 'locustfile_example.py', 'host': 'https://example.com', 'run_time': '30s', 'num_clients': '1', 'hatch_rate': 1, 'run_time':'3m'}

INFO:root:thread started
INFO:root:threads: 1, rpm: 0, run_time: 0, requests_total: 0, request_fail_ratio: 0, invocation_error_ratio: 0
INFO:root:threads: 1, rpm: 0, run_time: 3, requests_total: 0, request_fail_ratio: 0, invocation_error_ratio: 0
INFO:root:thread started
INFO:invokust.aws_lambda.lambda_load_test:Invocation complete. Requests (errors): 20 (0), execution time: 2982, sleeping: 0
INFO:root:threads: 2, rpm: 368, run_time: 6, requests_total: 20, request_fail_ratio: 0.0, invocation_error_ratio: 0.0
INFO:invokust.aws_lambda.lambda_load_test:Invocation complete. Requests (errors): 20 (0), execution time: 2896, sleeping: 0
INFO:invokust.aws_lambda.lambda_load_test:Invocation complete. Requests (errors): 20 (0), execution time: 3023, sleeping: 0
INFO:root:threads: 2, rpm: 770, run_time: 9, requests_total: 60, request_fail_ratio: 0.0, invocation_error_ratio: 0.0
INFO:invokust.aws_lambda.lambda_load_test:Invocation complete. Requests (errors): 20 (0), execution time: 3041, sleeping: 0
INFO:invokust.aws_lambda.lambda_load_test:Invocation complete. Requests (errors): 20 (0), execution time: 3071, sleeping: 0
INFO:root:threads: 2, rpm: 768, run_time: 12, requests_total: 100, request_fail_ratio: 0.0, invocation_error_ratio: 0.0
INFO:invokust.aws_lambda.lambda_load_test:Invocation complete. Requests (errors): 20 (0), execution time: 3031, sleeping: 0
INFO:invokust.aws_lambda.lambda_load_test:Invocation complete. Requests (errors): 20 (0), execution time: 2965, sleeping: 0
INFO:root:threads: 2, rpm: 782, run_time: 15, requests_total: 140, request_fail_ratio: 0.0, invocation_error_ratio: 0.0
INFO:invokust.aws_lambda.lambda_load_test:Invocation complete. Requests (errors): 20 (0), execution time: 2957, sleeping: 0
INFO:invokust.aws_lambda.lambda_load_test:Invocation complete. Requests (errors): 20 (0), execution time: 3069, sleeping: 0
INFO:root:threads: 2, rpm: 779, run_time: 18, requests_total: 180, request_fail_ratio: 0.0, invocation_error_ratio: 0.0
INFO:invokust.aws_lambda.lambda_load_test:Invocation complete. Requests (errors): 20 (0), execution time: 3015, sleeping: 0
INFO:invokust.aws_lambda.lambda_load_test:Invocation complete. Requests (errors): 20 (0), execution time: 3018, sleeping: 0
INFO:root:threads: 2, rpm: 771, run_time: 21, requests_total: 220, request_fail_ratio: 0.0, invocation_error_ratio: 0.0
INFO:invokust.aws_lambda.lambda_load_test:Invocation complete. Requests (errors): 20 (0), execution time: 3055, sleeping: 0
INFO:invokust.aws_lambda.lambda_load_test:Invocation complete. Requests (errors): 20 (0), execution time: 3015, sleeping: 0
INFO:root:threads: 2, rpm: 771, run_time: 24, requests_total: 260, request_fail_ratio: 0.0, invocation_error_ratio: 0.0
INFO:invokust.aws_lambda.lambda_load_test:Invocation complete. Requests (errors): 20 (0), execution time: 3007, sleeping: 0
INFO:invokust.aws_lambda.lambda_load_test:Invocation complete. Requests (errors): 20 (0), execution time: 3012, sleeping: 0
INFO:root:threads: 2, rpm: 779, run_time: 27, requests_total: 300, request_fail_ratio: 0.0, invocation_error_ratio: 0.0
INFO:invokust.aws_lambda.lambda_load_test:Invocation complete. Requests (errors): 20 (0), execution time: 3029, sleeping: 0
INFO:invokust.aws_lambda.lambda_load_test:Invocation complete. Requests (errors): 20 (0), execution time: 3037, sleeping: 0
INFO:root:threads: 2, rpm: 773, run_time: 30, requests_total: 340, request_fail_ratio: 0.0, invocation_error_ratio: 0.0
INFO:invokust.aws_lambda.lambda_load_test:Invocation complete. Requests (errors): 20 (0), execution time: 3078, sleeping: 0
INFO:invokust.aws_lambda.lambda_load_test:Invocation complete. Requests (errors): 20 (0), execution time: 3100, sleeping: 0
INFO:root:threads: 2, rpm: 758, run_time: 33, requests_total: 380, request_fail_ratio: 0.0, invocation_error_ratio: 0.0
INFO:root:Time limit reached
INFO:root:Waiting for threads to exit...
INFO:invokust.aws_lambda.lambda_load_test:Invocation complete. Requests (errors): 20 (0), execution time: 2965, sleeping: 0
INFO:root:thread finished
INFO:invokust.aws_lambda.lambda_load_test:Invocation complete. Requests (errors): 20 (0), execution time: 3033, sleeping: 0
INFO:root:thread finished

load_test.get_summary_stats()
{'lambda_invocation_count': 21, 'total_lambda_execution_time': 63399, 'requests_total': 420, 'request_fail_ratio': 0.0, 'invocation_error_ratio': 0.0}
```

There is also an example CLI tool for running a load test, `invokr.py`:

```
$ ./invokr.py --function_name=lambda_locust --locust_file=locustfile_example.py --locust_host=https://example.com --threads=1 --time_limit=30 --locust_requests=20
2017-05-22 20:16:22,432 INFO   MainThread
Starting load test
Function: lambda_locust
Ramp time: 0
Threads: 1
Lambda payload: {'locustfile': 'locustfile_example.py', 'host': 'https://example.com', 'num_requests': 20, 'num_clients': 20, 'hatch_rate': 10, 'run_time':'3m'}

2017-05-22 20:16:22,432 INFO   thread_1    thread started
2017-05-22 20:16:22,436 INFO   MainThread  threads: 1, rpm: 0, run_time: 0, requests_total: 0, request_fail_ratio: 0, invocation_error_ratio: 0
2017-05-22 20:16:25,440 INFO   MainThread  threads: 1, rpm: 0, run_time: 3, requests_total: 0, request_fail_ratio: 0, invocation_error_ratio: 0
2017-05-22 20:16:27,983 INFO   thread_1    Invocation complete. Requests (errors): 20 (0), execution time: 5186, sleeping: 0
2017-05-22 20:16:28,446 INFO   MainThread  threads: 1, rpm: 216, run_time: 6, requests_total: 20, request_fail_ratio: 0.0, invocation_error_ratio: 0.0
2017-05-22 20:16:31,448 INFO   MainThread  threads: 1, rpm: 216, run_time: 9, requests_total: 20, request_fail_ratio: 0.0, invocation_error_ratio: 0.0
2017-05-22 20:16:32,860 INFO   thread_1    Invocation complete. Requests (errors): 20 (0), execution time: 4798, sleeping: 0
2017-05-22 20:16:34,453 INFO   MainThread  threads: 1, rpm: 246, run_time: 12, requests_total: 40, request_fail_ratio: 0.0, invocation_error_ratio: 0.0
2017-05-22 20:16:37,454 INFO   MainThread  threads: 1, rpm: 246, run_time: 15, requests_total: 40, request_fail_ratio: 0.0, invocation_error_ratio: 0.0
2017-05-22 20:16:38,110 INFO   thread_1    Invocation complete. Requests (errors): 20 (0), execution time: 5176, sleeping: 0
2017-05-22 20:16:40,458 INFO   MainThread  threads: 1, rpm: 229, run_time: 18, requests_total: 60, request_fail_ratio: 0.0, invocation_error_ratio: 0.0
2017-05-22 20:16:43,072 INFO   thread_1    Invocation complete. Requests (errors): 20 (0), execution time: 4882, sleeping: 0
2017-05-22 20:16:43,464 INFO   MainThread  threads: 1, rpm: 242, run_time: 21, requests_total: 80, request_fail_ratio: 0.0, invocation_error_ratio: 0.0
2017-05-22 20:16:46,466 INFO   MainThread  threads: 1, rpm: 242, run_time: 24, requests_total: 80, request_fail_ratio: 0.0, invocation_error_ratio: 0.0
2017-05-22 20:16:48,237 INFO   thread_1    Invocation complete. Requests (errors): 20 (0), execution time: 5041, sleeping: 0
2017-05-22 20:16:49,467 INFO   MainThread  threads: 1, rpm: 232, run_time: 27, requests_total: 100, request_fail_ratio: 0.0, invocation_error_ratio: 0.0
2017-05-22 20:16:52,468 INFO   MainThread  threads: 1, rpm: 232, run_time: 30, requests_total: 100, request_fail_ratio: 0.0, invocation_error_ratio: 0.0
2017-05-22 20:16:53,347 INFO   thread_1    Invocation complete. Requests (errors): 20 (0), execution time: 5041, sleeping: 0
2017-05-22 20:16:55,468 INFO   MainThread  threads: 1, rpm: 235, run_time: 33, requests_total: 120, request_fail_ratio: 0.0, invocation_error_ratio: 0.0
2017-05-22 20:16:55,468 INFO   MainThread  Time limit reached
2017-05-22 20:16:55,468 INFO   MainThread  Waiting for threads to exit...
2017-05-22 20:16:58,666 INFO   thread_1    Invocation complete. Requests (errors): 20 (0), execution time: 5209, sleeping: 0
2017-05-22 20:16:58,667 INFO   thread_1    thread finished
2017-05-22 20:16:59,484 INFO   MainThread  Load test finished. lambda_invocation_count: 7, total_lambda_execution_time: 35333, requests_total: 140, request_fail_ratio: 0.0, invocation_error_ratio: 0.0
2017-05-22 20:16:59,484 INFO   MainThread  Aggregated results: {'success': {'GET_/': {'median_response_time': 285.7142857142857, 'total_rps': 19.753860147907517, 'avg_response_time': 615.4214285714286, 'max_response_time': 1703, 'min_response_time': 100, 'response_times': {'1100': 6, '1400': 9, '120': 2, '140': 14, '960': 3, '180': 9, '160': 11, '260': 6, '300': 3, '1200': 6, '340': 3, '200': 12, '1700': 2, '220': 9, '1300': 10, '380': 3, '440': 5, '240': 5, '1000': 2, '480': 2, '1600': 2, '1500': 9, '100': 1, '360': 1, '540': 1, '940': 1, '280': 1, '320': 1, '400': 1}, 'total_rpm': 1185.231608874451}}, 'fail': {}, 'num_requests': 140, 'num_requests_fail': 0, 'num_requests_success': 140, 'total_time': 35333, 'invocations': 7, 'approximate_cost': 7.4824e-05}
2017-05-22 20:16:59,484 INFO   MainThread  Exiting...
```
