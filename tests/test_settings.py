import os

from typing import List
from unittest import TestCase
from invokust.settings import create_settings
from locust import HttpUser, task, between


class TestCreateSettings(TestCase):
    def test_non_changeable_params(self):
        settings = create_settings(
            locustfile="tests/test_locustfile.py",
            host="http://dummy.host",
            num_users=2,
            spawn_rate=1,
        )

        assert settings.tags == None
        assert settings.exclude_tags == None
        assert settings.reset_stats == False
        assert settings.stop_timeout == None

    def test_not_from_environment_works(self):

        settings = create_settings(
            locustfile="tests/test_locustfile.py",
            host="http://dummy.host",
            num_users=2,
            spawn_rate=1,
        )

        assert isinstance(settings.classes, List)
        assert settings.host == "http://dummy.host"
        assert settings.num_users == 2
        assert settings.spawn_rate == 1

        assert settings.from_environment == False
        assert settings.tags == None
        assert settings.exclude_tags == None
        assert settings.reset_stats == False
        assert settings.step_load == False
        assert settings.stop_timeout == None

    def test_throw_exception_when_missing_params(self):

        with self.assertRaises(Exception):
            create_settings(
                locustfile="tests/test_locustfile.py", num_users=2, spawn_rate=1
            )

        with self.assertRaises(Exception):
            create_settings(
                locustfile="tests/test_locustfile.py",
                host="http://dummy.host",
                spawn_rate=1,
            )

        with self.assertRaises(Exception):
            create_settings(
                locustfile="tests/test_locustfile.py",
                host="http://dummy.host",
                num_users=2,
            )

        with self.assertRaises(Exception):
            create_settings(
                locustfile="tests/test_locustfile.py",
            )

    def test_from_env(self):

        os.environ["LOCUST_HOST"] = "http://dummy.host"
        os.environ["LOCUST_LOCUSTFILE"] = "tests/test_locustfile.py"
        os.environ["LOCUST_NUM_USERS"] = "2"
        os.environ["LOCUST_SPAWN_RATE"] = "1"

        settings = create_settings(from_environment=True)

        assert settings.host == "http://dummy.host"
        assert isinstance(settings.classes, List)
        assert settings.num_users == 2
        assert settings.spawn_rate == 1

    def test_classes_passed(self):
        class WebsiteUser(HttpUser):
            wait_time = between(0, 0)

            @task()
            def get_home_page(self):

                self.client.get("/")

        settings = create_settings(
            classes=[WebsiteUser], host="http://dummy.host", num_users=2, spawn_rate=1
        )

        assert isinstance(settings.classes, List)
        assert settings.classes[0] == WebsiteUser

    def test_locustfile_and_classes_missing(self):
        with self.assertRaises(Exception):
            create_settings(
                num_users=2,
                spawn_rate=1,
                host="http://dummy.host",
            )

    def test_fails_as_both_locustfile_and_classes_specified(self):
        class WebsiteUser(HttpUser):
            wait_time = between(0, 0)

            @task()
            def get_home_page(self):

                self.client.get("/")

        with self.assertRaises(Exception):
            create_settings(
                classes=[WebsiteUser],
                locustfile="tests/test_locustfile.py",
                num_users=2,
                spawn_rate=1,
                host="http://dummy.host",
            )
