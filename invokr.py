#!/usr/bin/env python3

import argparse
import logging
import sys
import json
from invokust import LambdaLoadTest, results_aggregator

def parse_arguments():
    p = argparse.ArgumentParser(description='Runs a Locust load tests on AWS Lambda in parallel')
    p.add_argument('-n', '--function_name', help='Lambda function name', required=True)
    p.add_argument('-f', '--locust_file', help='Locust file', required=True)
    p.add_argument('-o', '--locust_host', help='Locust host', required=True)
    p.add_argument('-e', '--locust_requests', help='Locust requests amount', default=1000, type=int)
    p.add_argument('-c', '--locust_clients', help='Locust clients', default=20, type=int)
    p.add_argument('-r', '--ramp_time', help='Ramp up time (seconds)', default=0, type=int)
    p.add_argument('-t', '--threads', help='Threads to run in parallel', default=1, type=int)
    p.add_argument('-l', '--time_limit', help='Time limit for run time (seconds)', default=0, type=int)
    return p.parse_args()

def print_stats_exit(load_test_state):
    summ_stats = load_test_state.get_summary_stats()
    agg_results = results_aggregator(load_test_state.get_locust_results())
    agg_results['request_fail_ratio'] = summ_stats['request_fail_ratio']
    agg_results['invocation_error_ratio'] = summ_stats['invocation_error_ratio']
    agg_results['locust_settings'] = load_test_state.lambda_payload
    agg_results['lambda_function_name'] = load_test_state.lambda_function_name
    agg_results['threads'] = load_test_state.threads
    agg_results['ramp_time'] = load_test_state.ramp_time
    agg_results['time_limit'] = load_test_state.time_limit
    logging.info('Aggregated results: {0}'.format(json.dumps(agg_results)))
    logging.info('Exiting...')
    sys.exit(0)

if __name__ == '__main__':
    args = parse_arguments()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-6s %(threadName)-11s %(message)s')

    lambda_payload = {
        'locustfile': args.locust_file,
        'host': args.locust_host,
        'num_requests': args.locust_requests,
        'num_clients': args.locust_clients,
        'hatch_rate': 10
    }

    load_test_state = LambdaLoadTest(
        args.function_name,
        args.threads,
        args.ramp_time,
        args.time_limit,
        lambda_payload
    )

    try:
        load_test_state.run()

    except KeyboardInterrupt:
        print_stats_exit(load_test_state)
    else:
        print_stats_exit(load_test_state)
