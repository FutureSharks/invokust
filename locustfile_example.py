# -*- coding: utf-8 -*-

from locust import HttpLocust, TaskSet, task

class GetHomePageTask(TaskSet):
    @task()
    def get_home_page(self):
        '''
        Gets /
        '''
        self.client.get("/")

class WebsiteUser(HttpLocust):
    task_set = GetHomePageTask
    min_wait = 0
    max_wait = 0
