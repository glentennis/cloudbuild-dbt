#!/usr/bin/env bash

# initialize files
touch latest_status.txt
touch dbt_invocations.json

# setup time tracking
echo $(date +%s) > start_time.txt

# set auth json
echo $BQ_USER_JSON > bq-user-json.json

# download last state artifacts so that we are not starting from scratch
mkdir target
gsutil -m cp -r gs://$ARTIFACTS_BUCKET/dbt_state/target/* ./target/

# create an isolated copy of state artifacts for deferred runs
cp -r ./target/ ./prod_artifacts/

# setup retry logic
echo $_RETRY_FROM_STEP_NUM > retry_from_step_num.txt
echo "1" > current_step_num.txt
