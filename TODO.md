To do

- `LOCUST_CLASSES` environment variable does not work
- `results_aggregator` changes:
  - Create timechart data of RPS from each element of results
  - Reduce amount of buckets in data returned by `_merge_response_times`
  - Aggregate response_time_percentiles but how?
- Document `results_aggregator`
- `LambdaLoadTest` changes:
  - RPM reported when ramping up is incorrect due to sleep_time
  - Update to be able to target a specific RPM
  - Add an interactive mode where threads can be started/stopped while load test is running
  - When time limit is reached, collect last results before exiting
- Occasional Lambda error message "RequestId: xxxxx-3f19-11e7-a1d1-xxxxxxx Process exited before completing request"
