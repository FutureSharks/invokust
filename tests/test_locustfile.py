from locust import HttpUser, task, between


class WebsiteUser(HttpUser):
    wait_time = between(0, 0)

    @task()
    def get_home_page(self):
        """
        Gets /
        """
        self.client.get("/")
