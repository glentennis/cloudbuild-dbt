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

## 0.0) Notes

- I am going to assume that you're an admin on the GCB project you're using. If not, you may need to request access for certain components as you go along. Fortunately, GCP is pretty good at telling you which permissions you need when you run into an issue.
- 

## 1) Copy the "cloud_build" folder here into your dbt project

Since Google Cloud Build does not currently support git submodules, you'll have to physically copy the cloud build code into your dbt project. If I ever push updates to the code, you can come back and do it again! Not perfect, but much better than making any big changes to the dbt project you know and love.

- In your dbt_project.yml, you will need to set `profile: 'default'`

## 2) Create a BigQuery Service Account

You will need to:
- [Create a service account](https://cloud.google.com/iam/docs/service-accounts-create) and grant the ["BigQuery Admin" role](https://cloud.google.com/bigquery/docs/access-control#bigquery.admin) for your project.
- [Create and download a JSON key for that service account](https://cloud.google.com/iam/docs/keys-create-delete#iam-service-account-keys-create-console).
- Remember where you save that json file!

## 2.1) Create Buckets

## 2.2) Create BQ tables
- dbt_invocations
- slack_messages

## 2.3) Set up Slack Webhook (optional)
https://api.slack.com/messaging/webhooks

## 3) Create Secrets

In [Secret Manager](https://console.cloud.google.com/security/secret-manager?), create the following secrets

- bq_user_json: copy and paste the contents of the Service Account JSON file from step 2.
- artifacts_bucket: name of the bucket you created in step 2.1
- cloud_build_dataset_id: name of the BQ dataset you set up in 2.2
- slack_webhook: URL from 2.3. if you dont want to set up slack alerts, just set it to `none`

Notes:
- Your [compute engine default service account](https://cloud.google.com/build/docs/cloud-build-service-account) ([PROJECT_NUMBER]-compute@developer.gserviceaccount.com) must have access to all of these secrets. You can accomplish this by granting access to each secret individually, or granting the role "Secret Manager Secret Accessor" to you cloud build service account

## 3.5) Connect Repo to GCB

https://console.cloud.google.com/cloud-build/repositories/2nd-gen?

* You may need to enable the GCB API

* More info on how to connect a Github Repo to GCB:
https://cloud.google.com/build/docs/repositories?

## 4) Create Triggers

To start out, create a trigger with the following settings:
https://console.cloud.google.com/cloud-build/triggers;region=global/add?

- Name: dbt-build
- Event: Manual invocation
- Source: Select the repo you just connected to
- "Cloud Build configuration file location": 
- Create one Substitution Variable with name `_RETRY_FROM_STEP_NUM` and value `0`

All other settings can be left on default.

## 4.5) Run Trigger and Viewing Results
- In GCB logs
- In BQ tables

## 5) Scheduling Triggers

From the [triggers page](https://console.cloud.google.com/cloud-build/triggers), click the three dots next to a trigger and select "Run on Schedule". From there, it's pretty simple.

## 6) Creating your own Jobs in YAML

# Areas of Improvement and Pet Peeves

- Each cloud build job.yaml file requires a lot of repetitive, boilerplate configuration (e.g. I shouldn't have to specify that I want PROJECT_ID to be an env var every time.) This could be solved by configuring job yaml with a codegen script + configs, and generating job yaml ephemerally on each push to production