# -*- coding: utf-8 -*-

import sys
sys.path.insert(0, "python-packages")

import logging
import invokust

logging.basicConfig(level=logging.INFO)

def lambda_handler(event=None, context=None):
    try:
        settings = invokust.create_settings(from_environment=True)
        loadtest = invokust.LoadTest(settings)
        loadtest.run(timeout=298)

    except Exception as e:
        logging.error("Locust exception {0}".format(repr(e)))

    else:
        locust_stats = loadtest.stats()
        lambda_runtime_info = invokust.get_lambda_runtime_info(context)
        loadtest_results = locust_stats.copy()
        loadtest_results.update(lambda_runtime_info)

        return loadtest_results
