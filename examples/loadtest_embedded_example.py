import invokust
import logging

from locust import HttpUser, task, between

logging.basicConfig(level=logging.DEBUG)


class WebsiteUser(HttpUser):
    wait_time = between(0, 0)

    @task()
    def my_task(self):
        self.client.get("/")


settings = invokust.create_settings(
    classes=[WebsiteUser],
    host="http://example.com",
    num_users=1,
    spawn_rate=1,
    run_time="10s",
)

loadtest = invokust.LocustLoadTest(settings)
loadtest.run()
loadtest.stats()
