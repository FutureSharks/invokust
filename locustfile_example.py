# -*- coding: utf-8 -*-

import logging

from locust import HttpLocust, TaskSet, task

logger = logging.getLogger(__name__)

class Task(TaskSet):
    @task()
    def get_home_page(self):
        '''
        Gets /
        '''
        self.client.get("/")

class WebsiteUser(HttpLocust):
    task_set = Task
