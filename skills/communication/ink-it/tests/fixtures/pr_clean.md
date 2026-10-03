fix/acme-412-retry-budget

- capping checkout retries at 3 (ACME-412)
- logging `RetryBudgetExceeded` when the cap hits
- touches services/checkout/retry.py and services/checkout/metrics.py; café fixture names untouched
