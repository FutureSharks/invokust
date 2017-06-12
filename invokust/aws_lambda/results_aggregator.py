# -*- coding: utf-8 -*-

from numpy import histogram

def results_aggregator(results):
    '''
    Takes a list of many individual results and returns a dictionary of aggregated
    data.

    arguments

    results: A list of results from LocustLoadTest.stats()
    '''

    def _flatten_unique(list_of_lists):
        l_flat = sum(list_of_lists, [])
        l_unique = list(set(l_flat))
        return l_unique

    def _mean(numbers):
        return float(sum(numbers)) / max(len(numbers), 1)

    def _merge_response_times(response_times):
        flat_list = []
        for r_time in response_times:
            for key, value in r_time.items():
                flat_list.extend([int(key)] * value)
        hist, bins = histogram(flat_list)
        return {
            'histogram': hist.tolist(),
            'bins': bins.tolist(),
        }

    def _get_min(data, key):
        try:
            return min([r[key] for r in data if r[key] is not None])
        except ValueError:
            return 0

    def _get_max(data, key):
        try:
            return max([r[key] for r in data if r[key] is not None])
        except ValueError:
            return 0

    def _calculate_aws_lambda_cost(total_execution_time, memory_limit, invocation_count):
        dollar_cost_per_128mb_100ms = 0.000000208
        dollar_cost_per_invocation = 0.0000002
        memory_cost_multiplier = int(memory_limit) / 128.0
        time_in_100ms_lots = int(total_time / 100.0)
        invocation_cost = invocation_count * 0.0000002
        execution_time_cost = time_in_100ms_lots * dollar_cost_per_128mb_100ms * memory_cost_multiplier
        return (invocation_cost + execution_time_cost)

    successful_tasks = _flatten_unique([list(stat['success'].keys()) for stat in results])
    failed_tasks = _flatten_unique([list(stat['fail'].keys()) for stat in results])
    total_time = sum([(300000 - stat['remaining_time']) for stat in results])
    memory_limit = _get_max(results, 'memory_limit')

    agg_results = {
        'success': dict.fromkeys(successful_tasks, {}),
        'fail': dict.fromkeys(failed_tasks, {}),
        'num_requests': sum([stat['num_requests'] for stat in results]),
        'num_requests_fail': sum([stat['num_requests_fail'] for stat in results]),
        'num_requests_success': sum([stat['num_requests_success'] for stat in results]),
        'total_time': total_time,
        'invocations': len(results),
        'approximate_cost': _calculate_aws_lambda_cost(total_time, memory_limit, len(results))
    }

    for task in successful_tasks:
        task_data_results = [stat['success'][task] for stat in results if task in stat['success']]

        for mean_stat in ['median_response_time', 'total_rps', 'avg_response_time']:
            agg_results['success'][task][mean_stat] = _mean([data[mean_stat] for data in task_data_results])

        agg_results['success'][task]['max_response_time'] = _get_max(task_data_results, 'max_response_time')
        agg_results['success'][task]['min_response_time'] = _get_min(task_data_results, 'min_response_time')
        agg_results['success'][task]['response_times'] = _merge_response_times([data['response_times'] for data in task_data_results if data['response_times'] is not None])
        agg_results['success'][task]['total_rpm'] = agg_results['success'][task]['total_rps'] * 60

    for task in failed_tasks:
        task_data_results = [stat['fail'][task] for stat in results if task in stat['fail']]
        agg_results['fail'][task] = task_data_results[0]
        agg_results['fail'][task]['occurences'] = sum([stat['occurences'] for stat in task_data_results])

    return agg_results
