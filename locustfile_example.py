# -*- coding: utf-8 -*-

from locust import HttpUser, task, between


class WebsiteUser(HttpUser):
    wait_time = between(0, 0)

    @task(3)
    def get_home_page(self):
        """
        Gets /
        """
        self.client.get("/")

    @task(1)
    def get_about(self):
        """
        Gets /about
        """
        response = self.client.get("/about")
