# -*- coding: utf-8 -*-

import sys
import gevent
import json
import signal
import logging
import time
from locust.env import Environment
from locust.log import setup_logging
from locust.stats import stats_printer
from locust.util.timespan import parse_timespan

setup_logging("INFO", None)
logger = logging.getLogger(__name__)


def sig_term_handler():
    logger.info("Got SIGTERM signal")
    sys.exit(0)


class LocustLoadTest(object):
    """
    Runs a Locust load test and returns statistics
    """

    def __init__(self, settings):
        self.settings = settings
        self.start_time = None
        self.end_time = None
        gevent.signal_handler(signal.SIGTERM, sig_term_handler)

    def stats(self):
        """
        Returns the statistics from the load test in JSON
        """
        statistics = {
            "requests": {},
            "failures": {},
            "num_requests": self.env.runner.stats.num_requests,
            "num_requests_fail": self.env.runner.stats.num_failures,
            "start_time": self.start_time,
            "end_time": self.end_time,
        }

        for name, value in self.env.runner.stats.entries.items():
            locust_task_name = "{0}_{1}".format(name[1], name[0])
            statistics["requests"][locust_task_name] = {
                "request_type": name[1],
                "num_requests": value.num_requests,
                "min_response_time": value.min_response_time,
                "median_response_time": value.median_response_time,
                "avg_response_time": value.avg_response_time,
                "max_response_time": value.max_response_time,
                "response_times": value.response_times,
                "response_time_percentiles": {
                    55: value.get_response_time_percentile(0.55),
                    65: value.get_response_time_percentile(0.65),
                    75: value.get_response_time_percentile(0.75),
                    85: value.get_response_time_percentile(0.85),
                    95: value.get_response_time_percentile(0.95),
                },
                "total_rps": value.total_rps,
                "total_rpm": value.total_rps * 60,
            }

        for _, error in self.env.runner.errors.items():
            error_dict = error.serialize()
            locust_task_name = "{0}_{1}".format(
                error_dict["method"], error_dict["name"]
            )
            statistics["failures"][locust_task_name] = error_dict

        return statistics

    def set_run_time_in_sec(self, run_time_str):
        try:
            self.run_time_in_sec = parse_timespan(run_time_str)
        except ValueError:
            logger.error(
                "Invalid format for `run_time` parameter: '%s', "
                "Valid formats are: 20s, 3m, 2h, 1h20m, 3h30m10s, etc." % run_time_str
            )
            sys.exit(1)
        except TypeError:
            logger.error(
                "`run_time` must be a string, not %s. Received value: % "
                % (type(run_time_str), run_time_str)
            )
            sys.exit(1)

    def run(self):
        """
        Run the load test.
        """

        if self.settings.run_time:
            self.set_run_time_in_sec(run_time_str=self.settings.run_time)

            logger.info("Run time limit set to %s seconds" % self.run_time_in_sec)

            def timelimit_stop():
                logger.info(
                    "Run time limit reached: %s seconds. Stopping Locust Runner."
                    % self.run_time_in_sec
                )
                self.env.runner.quit()
                self.end_time = time.time()
                logger.info(
                    "Locust completed %s requests with %s errors"
                    % (self.env.runner.stats.num_requests, len(self.env.runner.errors))
                )
                logger.info(json.dumps(self.stats()))

            gevent.spawn_later(self.run_time_in_sec, timelimit_stop)

        try:
            logger.info("Starting Locust with settings %s " % vars(self.settings))

            self.env = Environment(
                user_classes=self.settings.classes,
                host=self.settings.host,
                tags=self.settings.tags,
                exclude_tags=self.settings.exclude_tags,
                reset_stats=self.settings.reset_stats,
                stop_timeout=self.settings.stop_timeout,
            )

            self.env.create_local_runner()
            gevent.spawn(stats_printer(self.env.stats))

            self.env.runner.start(
                user_count=self.settings.num_users, spawn_rate=self.settings.spawn_rate
            )

            self.start_time = time.time()
            self.env.runner.greenlet.join()

        except Exception as e:
            logger.error("Locust exception {0}".format(repr(e)))

        finally:
            self.env.events.quitting.fire()
