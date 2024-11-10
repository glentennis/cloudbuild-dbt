Configuration and helper scripts for cloud build deployment of dbt.

- Each yaml file in jobs/ is equivalent to a "Job" in dbtCloud
- Every yaml file should contain the "setup" and "post_run" steps
    - setup: pulls artifacts from the last run, required for deferred runs and partial parsing
    - post_run: writes artifacts to google cloud storage. Enables deferral and emulates
        dbtCloud's artifact storage/download features
- Triggers are managed on the Google-side. All we need to do here is define the set of jobs.
    We can set multiple triggers (schedules, webhooks, manual, ci) for a single job.
    