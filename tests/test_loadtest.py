import os
from unittest import TestCase
from invokust.settings import create_settings
from invokust import LocustLoadTest
from locust import HttpUser, between, task


class WebsiteUser(HttpUser):
    wait_time = between(1, 3)

    @task()
    def get_home_page(self):
        """
        Gets /
        """
        self.client.get("/")


class TestLocustLoadTest(TestCase):
    def test_basic_load_test(self):
        settings = create_settings(
            classes=[WebsiteUser],
            host="https://github.com",
            num_users=1,
            spawn_rate=1,
            run_time="1m",
        )

        loadtest = LocustLoadTest(settings)
        loadtest.run()
        stats = loadtest.stats()

        assert stats["num_requests"] > 10
        assert stats["end_time"] > stats["start_time"]
        assert stats["requests"]["GET_/"]["total_rpm"] > 0
