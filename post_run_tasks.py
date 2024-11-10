import glob
import os
import json
import argparse
import requests
from datetime import datetime, UTC
from difflib import get_close_matches
from google.cloud import storage, bigquery
from google.oauth2 import service_account

STATUS_PATH = 'latest_status.txt'
BUILD_URL = f"https://console.cloud.google.com/cloud-build/builds;region=us-central1/{os.environ['BUILD_ID']}"


def get_artifact_urls(bucket_name, prefix, delimiter=None):
    """Retrieve artifact URLs from a specified GCS bucket."""
    storage_client = storage.Client()
    blobs = storage_client.list_blobs(bucket_name, prefix=prefix, delimiter=delimiter)
    
    artifact_urls = [
        f'https://storage.cloud.google.com/{bucket_name}/{blob.name}' for blob in blobs
    ]
    
    if delimiter:
        print("Prefixes:")
        for prefix in blobs.prefixes:
            print(prefix)

    return artifact_urls


def upload_files(directory_path, bucket_name, blob_prefix):
    """Upload files from a directory to a GCS bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    rel_paths = glob.glob(f"{directory_path}/**", recursive=True)

    for local_file in rel_paths:
        if os.path.isfile(local_file):
            remote_path = f"{blob_prefix}/{os.path.relpath(local_file, directory_path)}"
            blob = bucket.blob(remote_path)
            blob.upload_from_filename(local_file)


def upload_file(file_path, bucket_name, dest_blob_name):
    """Upload a single file to a GCS bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(f"{dest_blob_name}/{os.path.basename(file_path)}")
    blob.upload_from_filename(file_path)


def get_bq_client():
    print(os.getcwd())
    print(os.listdir())
    credentials = service_account.Credentials.from_service_account_file('bq-user-json.json')
    bq_client = bigquery.Client(credentials)
    return bq_client


def bq_insert_rows_from_dicts(table_path, data):
    """Upload a list of dicts to a BQ table."""
    bq_client = get_bq_client()
    table = bq_client.get_table(table_path)
    errors = bq_client.insert_rows_json(table, data)
    if not errors:
        print(f"Insert to {table} successful.")


def bq_get_data(query):
    """Get a list of dicts based on a BQ query"""
    bq_client = get_bq_client()
    query_job = bq_client.query(query)
    results = query_job.result()
    return [dict(row) for row in results]


def build_failure_clause(results, artifact_urls):
    """Construct a message detailing failures and corresponding artifact URLs."""
    failure_clause = ''
    for r in results.get('results', []):
        if r['status'] in ['error', 'fail']:
            message = r['message']
            closest_match = get_close_matches(f"{BUILD_URL}/{r['unique_id']}", artifact_urls, n=1)
            artifact_url = closest_match[0] if closest_match else 'no url found'
            failure_clause += f"- {r['unique_id']}: {message}\n  - most similar artifact: {artifact_url}\n\n"
    return failure_clause


def send_slack_message(url, text, message_category='unspecified'):
    """Send a message to a Slack webhook."""
    payload = {"text": text}
    headers = {"Content-type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        message_data = [{
            'sent_at': str(datetime.now(UTC)),
            'text': text,
            'channel': 'alerts',
            'message_category': message_category,
            'build_id': os.environ['BUILD_ID'],
        }]
        bq_insert_rows_from_dicts(f'{os.ENVIRON['CLOUD_BUILD_DATASET_ID']}.slack_messages', message_data)


def handle_error_notifications(failure_clause, alert_type, dbt_invocations):
    """Handle notifications for errors based on the alert type."""
    text = f"dbt job failed\n{BUILD_URL}\nFailed on command:\n{dbt_invocations[-1].get('invocation')}\nFailures:\n{failure_clause}"

    if alert_type == 'slack':
        send_slack_message(url=os.environ['SLACK_WEBHOOK'], text=text, message_category='analytics_error_alerts')
    elif alert_type == 'ci':
        print(text)
        raise Exception("Slim CI Failed")
    else:
        raise Exception("Unknown alert type selected")


def check_for_errors(dbt_invocations, artifact_urls):
    """Check for errors in the run results and handle notifications accordingly."""
    run_results = {}
    failure_clause = 'Command Line Error (see build logs)'

    if os.path.exists('target/run_results.json'):
        with open('target/run_results.json', 'r') as f:
            run_results = json.load(f)
        
        statuses = [r['status'] for r in run_results['results']]
        failure_clause = build_failure_clause(run_results, artifact_urls)

    with open(STATUS_PATH, 'r') as f:
        system_status = f.read()

    if 'error' in statuses or 'fail' in statuses or system_status == 'fail':
        handle_error_notifications(failure_clause, args.alert_type, dbt_invocations)


def insert_events_to_bigquery(dbt_invocations):
    """Insert dbt invocation events into BigQuery."""
    for d in dbt_invocations:
        d.update({
            'build_id': os.environ['BUILD_ID'],
            'trigger_name': os.environ['TRIGGER_NAME'],
            'branch_name': os.environ['BRANCH_NAME']
        })

    bq_insert_rows_from_dicts(f'{os.ENVIRON['CLOUD_BUILD_DATASET_ID']}.dbt_invocations', dbt_invocations)


def main(args):
    """Main function to handle uploads, insertions, and error checking."""
    upload_files('target', os.environ['ARTIFACTS_BUCKET'], os.environ['BUILD_ID'])
    upload_files('logs', os.environ['ARTIFACTS_BUCKET'], os.path.join(os.environ['BUILD_ID'], 'logs'))

    artifact_urls = get_artifact_urls(os.environ['ARTIFACTS_BUCKET'], os.environ['BUILD_ID'])

    if args.write_state_artifacts == 'y':
        upload_file('target/manifest.json', os.environ['ARTIFACTS_BUCKET'], 'dbt_state/target')
        upload_file('target/partial_parse.msgpack', os.environ['ARTIFACTS_BUCKET'], 'dbt_state/target')

    with open('dbt_invocations.json', 'r') as f:
        dbt_invocations = [json.loads(line) for line in f]

    insert_events_to_bigquery(dbt_invocations)
    check_for_errors(dbt_invocations, artifact_urls)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-wa", "--write_state_artifacts", default='n', help="Write artifacts to bucket (y/n)")
    parser.add_argument("-at", "--alert_type", default='slack', help="Alert type for failures")
    args = parser.parse_args()

    main(args)
