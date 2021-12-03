# -*- coding: utf-8 -*-

import os
import json
import time
import logging
import threading
from boto3.session import Session
from botocore.client import Config

logger = logging.getLogger(__name__)

logging.getLogger("botocore").setLevel(logging.CRITICAL)

session = Session()
config = Config(
    connect_timeout=os.environ.get('BOTO_CONFIG_CONNECT_TIMEOUT', 10),
    read_timeout=os.environ.get('BOTO_CONFIG_READ_TIMEOUT', 310),
    retries=json.loads(
        os.environ.get('BOTO_CONFIG_RETRIES', '{"max_attempts": 3}')
    )
)
client = session.client("lambda", config=config)


class LambdaLoadTest(object):
    """
    An object to run and collect statistics and results from multiple parallel locust load
    tests running on AWS Lambda
    """

    def __init__(
        self,
        lambda_function_name,
        threads,
        ramp_time,
        time_limit,
        lambda_payload,
        lambda_timeout=300000,
    ):
        self.lock = threading.Lock()
        self.start_time = time.time()
        self.logger = logging.getLogger()
        self.threads = threads
        self.ramp_time = ramp_time
        self.time_limit = (
            time_limit  # don't start new threads after {time_limit} seconds
        )
        self.lambda_function_name = lambda_function_name
        self.lambda_payload = lambda_payload
        self.lambda_invocation_errors = 0
        self.lambda_invocation_count = 0
        self.lambda_invocation_error_threshold = 20
        self.lambda_total_execution_time = 0
        self.requests_fail = 0
        self.request_fail_ratio_threshold = 0.5
        self.requests_total = 0
        self.locust_results = []
        self.thread_data = {}
        self.print_stats_delay = 3
        self.exit_threads = False
        self.lambda_timeout = lambda_timeout

    def update_thread_data(self, thread_id, key, value):
        """
        Receives data from threads and stores in the thread_data dict
        """
        with self.lock:
            if thread_id not in self.thread_data:
                self.thread_data[thread_id] = {}
            self.thread_data[thread_id][key] = value

    def get_thread_count(self):
        """
        Returns number of load test threads running
        """
        return len([t for t in threading.enumerate() if t.getName() != "MainThread"])

    def get_time_elapsed(self):
        """
        Returns elapsed time in seconds since starting the load test
        """
        return round(time.time() - self.start_time)

    def increase_lambda_invocation_error(self):
        """
        Increases Lambda invocation error count
        """
        with self.lock:
            self.lambda_invocation_errors += 1

    def increase_lambda_invocation_count(self):
        """
        Increases Lambda invocation count
        """
        with self.lock:
            self.lambda_invocation_count += 1

    def get_invocation_error_ratio(self):
        """
        Returns ratio of Lambda invocations to invocation errors
        """
        try:
            return self.lambda_invocation_errors / float(self.lambda_invocation_count)
        except ZeroDivisionError:
            return 0

    def increase_requests_total(self, requests):
        """
        Increases total request count
        """
        with self.lock:
            self.requests_total += requests

    def increase_requests_fail(self, requests):
        """
        Increases total request fail count
        """
        with self.lock:
            self.requests_fail += requests

    def get_request_fail_ratio(self):
        """
        Returns ratio of failed to total requests
        """
        try:
            return self.requests_fail / float(self.requests_total)
        except ZeroDivisionError:
            return 0

    def append_locust_results(self, results):
        """
        Logs results from a locust execution. All results needs to be aggregated in order to show meaningful statistics of the whole load test
        """
        with self.lock:
            self.locust_results.append(results)

    def get_summary_stats(self):
        """
        Returns summary statistics in a dict
        """
        return {
            "lambda_invocation_count": self.lambda_invocation_count,
            "total_lambda_execution_time": self.lambda_total_execution_time,
            "requests_total": self.requests_total,
            "request_fail_ratio": self.get_request_fail_ratio(),
            "invocation_error_ratio": self.get_invocation_error_ratio(),
        }

    def get_stats(self):
        """
        Returns current statistics in a dict
        """
        return {
            "thread_count": self.get_thread_count(),
            "rpm": self.calculate_rpm(),
            "time_elapsed": self.get_time_elapsed(),
            "requests_total": self.requests_total,
            "request_fail_ratio": self.get_request_fail_ratio(),
            "invocation_error_ratio": self.get_invocation_error_ratio(),
        }

    def get_locust_results(self):
        """
        Returns a list of locust results
        """
        return self.locust_results

    def increase_lambda_execution_time(self, time):
        """
        Add Lambda execution time to the total
        """
        with self.lock:
            self.lambda_total_execution_time += time

    def calculate_rpm(self):
        """
        Returns current total request per minute across all threads
        """
        return round(
            sum(
                self.thread_data[thread_id]["rpm"]
                for thread_id in self.thread_data
                if "rpm" in self.thread_data[thread_id]
            )
        )

    def check_error_threshold(self):
        """
        Checks if the current Lambda and request fail ratios are within thresholds
        """

        if self.lambda_invocation_errors > self.lambda_invocation_error_threshold:
            self.logger.error(
                f"Error limit reached. invocation error count/threshold: "
                f"{self.lambda_invocation_errors}/{self.lambda_invocation_error_threshold}"
            )
            return True
        elif self.get_request_fail_ratio() > self.request_fail_ratio_threshold:
            self.logger.error(
                f"Error limit reached. requests failed ratio/threshold: "
                f"{self.get_request_fail_ratio()}/{self.request_fail_ratio_threshold}"
            )
            return True
        else:
            return False

    def thread_required(self):
        """
        Returns True if a new thread should be started when ramping up over time
        """
        result = False
        if self.get_thread_count() < self.threads:
            next_thread_interval = (
                self.ramp_time / self.threads
            ) * self.get_thread_count()
            if self.get_time_elapsed() > next_thread_interval:
                result = True
        return result

    def stop_threads(self):
        """
        Sets a boolean to stop threads
        """
        with self.lock:
            self.exit_threads = True

    def start_new_thread(self):
        """
        Creates a new load test thread
        """
        t_name = "thread_{0}".format(threading.activeCount())
        t = threading.Thread(name=t_name, target=self.thread)
        t.daemon = True
        t.start()

    def thread(self):
        """
        This method is a single thread and performs the actual execution of the Lambda function and logs the statistics/results
        """
        self.logger.info("thread started")
        thread_start_time = time.time()
        thread_id = threading.current_thread().getName()
        self.update_thread_data(thread_id, "start_time", thread_start_time)
        while True:
            thread_run_time = time.time() - thread_start_time

            if self.exit_threads:
                break

            if self.ramp_time in [0.0, 0]:
                sleep_time = 0
            else:
                sleep_time = round(max(0, self.ramp_time - thread_run_time) / 30)

            function_start_time = time.time()

            try:
                self.logger.info("Invoking lambda...")
                response = client.invoke(
                    FunctionName=self.lambda_function_name,
                    Payload=json.dumps(self.lambda_payload),
                )
            except Exception as e:
                self.logger.critical("Lambda invocation failed: {0}".format(repr(e)))
                time.sleep(2)
                continue

            function_end_time = time.time()

            self.increase_lambda_invocation_count()

            if "FunctionError" in response:
                logger.error(
                    "error {0}: {1}".format(
                        response["FunctionError"], response["Payload"].read()
                    )
                )
                self.increase_lambda_invocation_error()
                time.sleep(2)
                continue

            payload = response["Payload"].read()
            payload_json_str = json.loads(payload.decode("utf-8"))

            if not payload_json_str:
                logger.error("No results in payload")
                self.increase_lambda_invocation_error()
                time.sleep(2)
                continue

            results = json.loads(payload_json_str)
            function_duration = function_end_time - function_start_time
            total_rpm = results["num_requests"] / (function_duration / 60)
            lambda_execution_time = self.lambda_timeout - results["remaining_time"]

            self.append_locust_results(results)
            self.increase_requests_fail(results["num_requests_fail"])
            self.increase_requests_total(results["num_requests"])
            self.update_thread_data(thread_id, "rpm", total_rpm)
            self.update_thread_data(
                thread_id, "lambda_execution_time", lambda_execution_time
            )
            self.increase_lambda_execution_time(lambda_execution_time)

            logger.info(
                "Lambda invocation complete. Requests (errors): {0} ({1}), execution time: {2}ms, sleeping: {3}s".format(
                    results["num_requests"],
                    results["num_requests_fail"],
                    lambda_execution_time,
                    sleep_time,
                )
            )
            time.sleep(sleep_time)

        self.logger.info("thread finished")

    def run(self):
        """
        Starts the load test, periodically prints statistics and starts new threads
        """
        self.logger.info(
            "\nStarting load test..."
            f"\nFunction name: {self.lambda_function_name}"
            f"\nRamp time: {self.ramp_time}s"
            f"\nThreads: {self.threads}"
            f"\nLambda payload: {self.lambda_payload}"
            f"\nStart ramping down after: {self.time_limit}s"
        )

        self.start_new_thread()

        while True:
            self.logger.info(
                "threads: {thread_count}, rpm: {rpm}, time elapsed: {time_elapsed}s, total requests from finished threads: {requests_total}, "
                "request fail ratio: {request_fail_ratio}, invocation error ratio: {invocation_error_ratio}".format(
                    **self.get_stats()
                )
            )

            if self.thread_required():
                self.start_new_thread()

            if self.check_error_threshold():
                self.stop_threads()
                self.logger.info("Waiting for threads to exit...")
                while self.get_thread_count() > 0:
                    time.sleep(1)
                else:
                    break

            if self.time_limit and self.get_time_elapsed() > self.time_limit:
                self.logger.info("Time limit reached. Starting ramp down...")
                self.stop_threads()

                self.logger.info(
                    "Waiting for all Lambdas to return. This may take up to {0}.".format(
                        self.lambda_payload["run_time"]
                    )
                )
                while self.get_thread_count() > 0:
                    time.sleep(1)
                else:
                    break

            time.sleep(self.print_stats_delay)
