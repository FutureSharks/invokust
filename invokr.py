#!/usr/bin/env python3

import argparse
import logging
import sys
import json
from invokust.aws_lambda import LambdaLoadTest, results_aggregator


def print_stat(type, name, req_count, median, avg, min, max, rps):
    return "%-7s %-50s %10s %9s %9s %9s %9s %10s" % (
        type,
        name,
        req_count,
        median,
        avg,
        min,
        max,
        rps,
    )


def parse_arguments():
    p = argparse.ArgumentParser(
        description="Runs a Locust load tests on AWS Lambda in parallel"
    )
    p.add_argument("-n", "--function_name", help="Lambda function name", required=True)
    p.add_argument("-f", "--locust_file", help="Locust file", required=True)
    p.add_argument("-o", "--locust_host", help="Locust host", required=True)
    p.add_argument(
        "-u", "--locust_users", help="Number of Locust users", default=20, type=int
    )
    p.add_argument(
        "-r", "--ramp_time", help="Ramp up time (seconds)", default=0, type=int
    )
    p.add_argument(
        "-t", "--threads", help="Threads to run in parallel", default=1, type=int
    )
    p.add_argument(
        "-l", "--time_limit", help="Time limit for run time (seconds)", type=int
    )
    return p.parse_args()


def print_stats_exit(load_test_state):
    summ_stats = load_test_state.get_summary_stats()
    agg_results = results_aggregator(load_test_state.get_locust_results())
    agg_results["request_fail_ratio"] = summ_stats["request_fail_ratio"]
    agg_results["invocation_error_ratio"] = summ_stats["invocation_error_ratio"]
    agg_results["locust_settings"] = load_test_state.lambda_payload
    agg_results["lambda_function_name"] = load_test_state.lambda_function_name
    agg_results["threads"] = load_test_state.threads
    agg_results["ramp_time"] = load_test_state.ramp_time
    agg_results["time_limit"] = load_test_state.time_limit
    logging.info("Aggregated results: {0}".format(json.dumps(agg_results)))

    logging.info(
        "\n============================================================"
        f"\nRamp up time: {agg_results['ramp_time']}s"
        f"\nStarted ramp down after {agg_results['time_limit']}s (time_limit)"
        f"\nThread count: {agg_results['threads']}"
        f"\nLambda invocation count: {agg_results['lambda_invocations']}"
        f"\nLambda invocation error ratio: {agg_results['invocation_error_ratio']}"
        f"\nCumulative lambda execution time: {agg_results['total_lambda_execution_time']}ms"
        f"\nTotal requests sent: {agg_results['num_requests']}"
        f"\nTotal requests failed: {agg_results['num_requests_fail']}"
        f"\nTotal request failure ratio: {agg_results['request_fail_ratio']}\n"
    )
    logging.info(
        "==========================================================================================================================="
    )
    logging.info(
        print_stat(
            "TYPE", "NAME", "#REQUESTS", "MEDIAN", "AVERAGE", "MIN", "MAX", "#REQS/SEC"
        )
    )
    logging.info(
        "==========================================================================================================================="
    )

    reqs = agg_results["requests"]
    for k in reqs.keys():
        k_arr = k.split("_")
        type = k_arr[0]
        del k_arr[0]
        name = "_".join(k_arr)
        logging.info(
            print_stat(
                type,
                name,
                reqs[k]["num_requests"],
                round(reqs[k]["median_response_time"], 2),
                round(reqs[k]["avg_response_time"], 2),
                round(reqs[k]["min_response_time"], 2),
                round(reqs[k]["max_response_time"], 2),
                round(reqs[k]["total_rps"], 2),
            )
        )

    logging.info("Exiting...")
    sys.exit(0)


if __name__ == "__main__":
    args = parse_arguments()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-6s %(threadName)-11s %(message)s",
    )

    # AWS Lambda has a maximum execution time ("timeout"). We limit the execution time to 3 minutes if the overall
    # load test time is longer, to make sure the lambda will not exceed the timeout.

    lambda_runtime = f"{args.time_limit}s" if args.time_limit < 180 else "3m"
    lambda_payload = {
        "locustfile": args.locust_file,
        "host": args.locust_host,
        "num_users": args.locust_users,
        "spawn_rate": 10,
        "run_time": lambda_runtime,
    }

    load_test_state = LambdaLoadTest(
        args.function_name,
        args.threads,
        args.ramp_time,
        args.time_limit,
        lambda_payload,
    )

    try:
        load_test_state.run()

    except KeyboardInterrupt:
        print_stats_exit(load_test_state)
    else:
        print_stats_exit(load_test_state)
