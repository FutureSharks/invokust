import invokust
import logging


logging.basicConfig(level=logging.DEBUG)


settings = invokust.create_settings(
    locustfile="locustfile_example.py",
    host="http://example.com",
    num_users=1,
    spawn_rate=1,
    run_time="10s",
    loglevel="DEBUG",
)

loadtest = invokust.LocustLoadTest(settings)
loadtest.run()
loadtest.stats()
