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
        return loadtest.stats()
