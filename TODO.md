# To do

- `LOCUST_CLASSES` as environment variable does not work
- Add Terraform code for running Lambda in a VPC with NAT instance to get a fixed/known source IP address

- `results_aggregator` changes:
  - Create timechart data of RPS from each element of results
  - How to aggregate response_time_percentiles?

- Show an example for `results_aggregator`

- `LambdaLoadTest` changes:
  - RPM reported when ramping up is incorrect due to sleep_time
  - Update to be able to target a specific RPM
  - Add an interactive mode where threads can be started/stopped while load test is running

- Occasional Lambda error messages:
  - "RequestId: xxxxx-3f19-11e7-a1d1-xxxxxxx Process exited before completing request"
  - Lambda invocation failed: LoopExit('This operation would block forever', <Hub at 0x7f8710791e88 epoll pending=0 ref=0 fileno=67 resolver=<gevent.resolver_thread.Resolver at 0x7f87106deba8 pool=<ThreadPool at 0x7f87106debe0 0/1/10>> threadpool=<ThreadPool at 0x7f87106debe0 0/1/10>>)
