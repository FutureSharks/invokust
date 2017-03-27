# -*- coding: utf-8 -*-

import os
import gevent
import json
import signal
import logging

from locust import runners, events


logger = logging.getLogger(__name__)


class TimeOutException(Exception): pass


class LoadTest(object):
    '''
    The LoadTest runs the load test and returns statistics
    '''
    def __init__(self, settings):
        self.settings = settings
        signal.signal(signal.SIGALRM, self.sig_alarm_handler)
        gevent.signal(signal.SIGTERM, self.sig_term_handler)

    def stats(self):
        '''
        Returns the statistics from the load test in JSON
        '''
        statistics = {
            'success': {},
            'fail': {},
            'num_requests': runners.locust_runner.stats.num_requests,
            'num_requests_success': 0,
            'num_requests_fail': 0,
            'locust_host': runners.locust_runner.host
        }

        for name, value in runners.locust_runner.stats.entries.items():
            statistics['success'][name[0]] = {
                'request_type': name[1],
                'num_requests': value.num_requests,
                'min_response_time': value.min_response_time,
                'median_response_time': value.median_response_time,
                'max_response_time': value.max_response_time,
                'total_rps': value.total_rps,
                'total_rpm': value.total_rps * 60
            }

        for id, error in runners.locust_runner.errors.viewitems():
            statistics['fail'][error.name] = error.to_dict()

        statistics['num_requests_success'] = sum(
            [statistics['success'][req]['num_requests'] for req in statistics['success']])
        statistics['num_requests_fail'] = sum(
            [statistics['fail'][req]['occurences'] for req in statistics['fail']])

        return json.dumps(statistics)

    def sig_term_handler(self, signum, frame):
        logger.info("Received sigterm, exiting")
        logger.info(self.stats())
        sys.exit(0)

    def sig_alarm_handler(self, signum, frame):
        '''
        This handler is used when a run time limit is set
        '''
        raise TimeOutException

    def run(self, timeout=None):
        '''
        Run the load test. Optionally a timeout can be set to limit the run time
        of the load test
        '''
        if timeout:
            self.timeout = timeout
            signal.alarm(timeout)
        try:
            logger.info("Starting Locust with and settings {0}".format(
                vars(self.settings)))
            runners.locust_runner = runners.LocalLocustRunner(self.settings.classes,
                self.settings)
            runners.locust_runner.start_hatching(wait=True)
            runners.locust_runner.greenlet.join()
            logger.info('Locust completed {0} requests with {1} errors'.format(
                self.settings.num_requests,
                len(runners.locust_runner.errors)))

        except TimeOutException:
            events.quitting.fire()
            logger.info(self.stats())
            logger.info("Run time limit reached: {0} seconds".format(self.timeout))

        except Exception as e:
            events.quitting.fire()
            logger.error("Locust exception {0}".format(repr(e)))
