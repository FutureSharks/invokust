import invokust
import logging

from locust import HttpLocust, TaskSet, task, between

logging.basicConfig(level=logging.DEBUG)

class Task(TaskSet):
    @task()
    def get_home_page(self):
        '''
        Gets /
        '''
        self.client.get("/")

class WebsiteUser(HttpLocust):
    task_set = Task
    wait_time = between(0, 0)

settings = invokust.create_settings(
    classes=[WebsiteUser],
    host='http://example.com',
    num_clients=1,
    hatch_rate=1,
    run_time='10s'
)

loadtest = invokust.LocustLoadTest(settings)
loadtest.run()
loadtest.stats()
