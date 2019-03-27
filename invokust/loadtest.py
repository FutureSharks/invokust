# -*- coding: utf-8 -*-

import sys
import gevent
import json
import signal
import logging
import time
from locust import runners, events
from locust.util.time import parse_timespan

logger = logging.getLogger(__name__)


class LocustLoadTest(object):
    '''
    Runs a Locust load test and returns statistics
    '''

    def __init__(self, settings):
        self.settings = settings
        self.start_time = None
        self.end_time = None
        gevent.signal(signal.SIGTERM, self.sig_term_handler)

    def stats(self):
        '''
        Returns the statistics from the load test in JSON
        '''
        statistics = {
            'requests': {},
            'failures': {},
            'num_requests': runners.locust_runner.stats.num_requests,
            'num_requests_fail': runners.locust_runner.stats.num_failures,
            'locust_host': runners.locust_runner.host,
            'start_time': self.start_time,
            'end_time': self.end_time
        }

        for name, value in runners.locust_runner.stats.entries.items():
            locust_task_name = '{0}_{1}'.format(name[1], name[0])
            statistics['requests'][locust_task_name] = {
                'request_type': name[1],
                'num_requests': value.num_requests,
                'min_response_time': value.min_response_time,
                'median_response_time': value.median_response_time,
                'avg_response_time': value.avg_response_time,
                'max_response_time': value.max_response_time,
                'response_times': value.response_times,
                'response_time_percentiles': {
                    55: value.get_response_time_percentile(0.55),
                    65: value.get_response_time_percentile(0.65),
                    75: value.get_response_time_percentile(0.75),
                    85: value.get_response_time_percentile(0.85),
                    95: value.get_response_time_percentile(0.95)
                },
                'total_rps': value.total_rps,
                'total_rpm': value.total_rps * 60
            }

        for id, error in runners.locust_runner.errors.items():
            error_dict = error.to_dict()
            locust_task_name = '{0}_{1}'.format(error_dict['method'],
                                                error_dict['name'])
            statistics['failures'][locust_task_name] = error_dict

        return statistics

    def sig_term_handler(self, signum, frame):
        logger.info("Received sigterm, exiting")
        logger.info(json.dumps(self.stats()))
        sys.exit(0)

    def run(self):
        '''
        Run the load test.
        '''
        if self.settings.run_time:
            try:
                self.settings.run_time = parse_timespan(self.settings.run_time)
            except ValueError:
                logger.error("Valid --run-time formats are:")
                logger.error("20, 20s, 3m, 2h, 1h20m, 3h30m10s, etc.")
                sys.exit(1)
            self.run_time = self.settings.run_time
            logger.info("Run time limit set to %s seconds" % self.run_time)

            def timelimit_stop():
                logger.info("Time limit reached. Stopping Locust.")
                logger.info(json.dumps(self.stats()))
                logger.info("Run time limit reached: {0} seconds".format(
                    self.run_time))
                runners.locust_runner.quit()

            gevent.spawn_later(self.run_time, timelimit_stop)
        try:
            logger.info("Starting Locust with settings {0}".format(
                vars(self.settings)))
            runners.locust_runner = runners.LocalLocustRunner(
                self.settings.classes, self.settings)
            runners.locust_runner.start_hatching(wait=True)
            self.start_time = time.time()
            runners.locust_runner.greenlet.join()
            self.end_time = time.time()
            logger.info('Locust completed {0} requests with {1} errors'.format(
                runners.locust_runner.stats.num_requests,
                len(runners.locust_runner.errors)))

        except Exception as e:
            logger.error("Locust exception {0}".format(repr(e)))

        finally:
            events.quitting.fire()
