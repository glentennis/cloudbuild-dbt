# dbt on Google Cloud Build

This repo provides a relatively turnkey way to run dbt on Google Cloud Build (GCB), providing a similar experience to dbtCloud.

# How does this compare to dbtCloud?

## Advantages

- Avoid dbtCloud subscription fees if you're running a tight ship 🚢
- Slack alerts on dbt failures are more descriptive, and link directly to the compiled SQL of the failed model/test
- All dbt invocations and Slack messages are logged to BigQuery, allowing you to analyze error rates and run times in BQ
- Almost everything is version controlled (some configuration is required in GCB)

## Disadvantages

- As constructed, this only works on BigQuery. It would take some adjustment to the python adapters to run on another engine
- dbt Docs are not implemented (although [this repo](https://github.com/C00ldudeNoonan/simple-dbt-runner/blob/main/save_and_publish_docs.sh) provides a good starting point)
- And much more, as dbtLabs is always adding to their product!

Finally, cloudbuild-dbt has a much slower, and less friendly customer support staff than dbtCloud.

# Setup

Now that you're sold, here are instructions on how to spin this up:

## 1) Activate GCP APIs

## 2) IAM Requirements

## 3) Create Secrets
- Project Name
- Region (use us-central1)
- Bucket Names
- ARTIFACTS_BUCKET
- CLOUD_BUILD_DATASET_ID
- BQ_USER_JSON
- SLACK_WEBHOOK (if you dont want to set up slack alerts, create an empty secret)

## 3.5) Create BQ tables
- dbt_invocations
- slack_messages

## 4) Create Triggers

## 4.5) Running Triggers and Viewing Results
- In GCB logs
- In BQ tables

## 5) Scheduling Triggers

## 6) Creating your own Jobs in YAML
