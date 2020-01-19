# -*- coding: utf-8 -*-

from locust import HttpLocust, TaskSet, task, between


class GetHomePageTask(TaskSet):
    @task()
    def get_home_page(self):
        '''
        Gets /
        '''
        self.client.get("/")
    
    @task()
    def get_another_page(self):
        '''
         Post /
        '''
        response=self.client.post("/post", {"username":"password"})


class WebsiteUser(HttpLocust):
    task_set = GetHomePageTask
    wait_time = between(0, 0)
