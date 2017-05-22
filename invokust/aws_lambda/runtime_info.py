# -*- coding: utf-8 -*-

def get_lambda_runtime_info(context):
    '''
    Returns a dictionary of information about the AWS Lambda function invocation

    Arguments

    context: The context object from AWS Lambda.
    '''

    runtime_info = {
        'remaining_time': context.get_remaining_time_in_millis(),
        'function_name': context.function_name,
        'function_version': context.function_version,
        'invoked_function_arn': context.invoked_function_arn,
        'memory_limit': context.memory_limit_in_mb,
        'aws_request_id': context.aws_request_id,
        'log_group_name': context.log_group_name,
        'log_stream_name': context.log_stream_name
    }

    return runtime_info
