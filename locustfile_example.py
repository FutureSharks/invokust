# -*- coding: utf-8 -*-

from locust import HttpLocust, TaskSet, task, between


class HomePageTaskSet(TaskSet):
    @task()
    def get_home_page(self):
        '''
        Gets /
        '''
        self.client.get("/")

    @task()
    def login(self):
        '''
        Posts to /post
        '''
        response=self.client.post("/post", {"username":"password"})


class WebsiteUser(HttpLocust):
    task_set = HomePageTaskSet
    wait_time = between(0, 0)
