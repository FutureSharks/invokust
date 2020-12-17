# -*- coding: utf-8 -*-

import os

from locust.main import load_locustfile


def create_settings(
    from_environment=False,
    locustfile=None,
    classes=None,
    host=None,
    num_users=None,
    spawn_rate=None,
    reset_stats=False,
    run_time="3m",
    loglevel="INFO",
):
    """
    Returns a settings object to configure the locust load test.

    Arguments

        from_environment: get settings from environment variables
        locustfile: locustfile to use for loadtest
        classes: locust classes to use for load test
        host: host for load testing
        num_users: number of users to simulate in load test
        spawn_rate: number of users per second to start
        reset_stats: Whether to reset stats after all users are hatched
        run_time: The length of time to run the test for. Cannot exceed the duration limit set by lambda

    If from_environment is set to True then this function will attempt to set
    the attributes from environment variables. The environment variables are
    named LOCUST_ + attribute name in upper case.
    """

    settings = type("", (), {})()

    settings.from_environment = from_environment
    settings.locustfile = locustfile

    # parameters needed to create the locust Environment object
    settings.classes = classes
    settings.host = host
    settings.tags = None
    settings.exclude_tags = None
    settings.reset_stats = reset_stats
    settings.step_load = False
    settings.stop_timeout = None

    # parameters to configure test
    settings.num_users = num_users
    settings.run_time = run_time
    settings.spawn_rate = spawn_rate

    if from_environment:
        for attribute in [
            "locustfile",
            "classes",
            "host",
            "run_time",
            "num_users",
            "spawn_rate",
            "loglevel",
        ]:
            var_name = "LOCUST_{0}".format(attribute.upper())
            var_value = os.environ.get(var_name)
            if var_value:
                setattr(settings, attribute, var_value)

    if settings.locustfile is None and settings.classes is None:
        raise Exception("One of locustfile or classes must be specified")

    if settings.locustfile and settings.classes:
        raise Exception("Only one of locustfile or classes can be specified")

    if settings.locustfile:
        docstring, classes, shape_class = load_locustfile(settings.locustfile)
        settings.classes = [classes[n] for n in classes]
    else:
        if isinstance(settings.classes, str):
            settings.classes = settings.classes.split(",")
            for idx, val in enumerate(settings.classes):
                # This needs fixing
                settings.classes[idx] = eval(val)

    for attribute in ["classes", "host", "num_users", "spawn_rate"]:
        val = getattr(settings, attribute, None)
        if not val:
            raise Exception(
                "configuration error, attribute not set: {0}".format(attribute)
            )

        if isinstance(val, str) and val.isdigit():
            setattr(settings, attribute, int(val))

    return settings
