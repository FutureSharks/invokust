# -*- coding: utf-8 -*-

import os

from locust.main import load_locustfile


def create_settings(from_environment=False, locustfile=None,
        classes=None, host=None, num_requests=None, num_clients=None,
        hatch_rate=None):
    '''
    Returns a settings object to be used by a LocalLocustRunner.

    Arguments

        from_environment: get settings from environment variables
        locustfile: locustfile to use for loadtest
        classes: locust classes to use for load test
        host: host for load testing
        num_requests: number of requests to send
        num_clients: number of clients to simulate in load test
        hatch_rate: number of clients per second to start

    If from_environment is set to True then this function will attempt to set
    the attributes from environment variables. The environment variables are
    named LOCUST_ + attribute name in upper case.
    '''

    settings = type('', (), {})()

    settings.from_environment = from_environment
    settings.locustfile = locustfile
    settings.classes = classes
    settings.host = host
    settings.num_requests = num_requests
    settings.num_clients = num_clients
    settings.hatch_rate = hatch_rate

    # Default settings that are not to be changed
    settings.no_web = True
    settings.master = False
    settings.show_task_ratio_json = False
    settings.list_commands = False
    settings.loglevel = 'INFO'
    settings.slave = False
    settings.only_summary = True
    settings.logfile = None
    settings.show_task_ratio = False
    settings.print_stats = False

    if from_environment:
        for attribute in ['locustfile', 'classes', 'host', 'num_requests', 'num_clients', 'hatch_rate']:
            var_name = 'LOCUST_{0}'.format(attribute.upper())
            var_value = os.environ.get(var_name)
            setattr(settings, attribute, var_value)

    if settings.locustfile is None and settings.classes is None:
        raise Exception('One of locustfile or classes must be specified')

    if settings.locustfile and settings.classes:
        raise Exception('Only one of locustfile or classes can be specified')

    if settings.locustfile:
        docstring, classes = load_locustfile(settings.locustfile)
        settings.classes = [classes[n] for n in classes]
    else:
        if isinstance(settings.classes, str):
            settings.classes = settings.classes.split(',')
            for idx, val in enumerate(settings.classes):
                # This needs fixing
                settings.classes[idx] = eval(val)

    for attribute in ['classes', 'host', 'num_requests', 'num_clients', 'hatch_rate']:
        val = getattr(settings, attribute, None)
        if not val:
            raise Exception('configuration error, attribute not set: {0}'.format(attribute))

        if isinstance(val, str) and val.isdigit():
            setattr(settings, attribute, int(val))

    return settings
