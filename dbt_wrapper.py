import os
import sys
import json
from datetime import datetime

RUN_RESULTS_PATH = 'target/run_results.json'
STATUS_PATH = 'latest_status.txt'
RETRY_FROM_STEP_NUM_PATH = 'retry_from_step_num.txt'
CURRENT_STEP_NUM_PATH = 'current_step_num.txt'
COMMAND = sys.argv[1]

os.environ["DBT_PROFILES_DIR"] = "/workspace/cloud_build/"

dbt_invocation = {
    'invocation': COMMAND,
    'started_at': str(datetime.utcnow()),
    'status': 'success'
}

def record_failure():
    with open(STATUS_PATH, 'w') as f:
        f.write('fail')
    dbt_invocation['status'] = 'fail'

# exit if this is a retry run, and we haven't reached "retry from step"
with open(RETRY_FROM_STEP_NUM_PATH, 'r') as f:
    retry_from_step_num = f.read().strip()
    if retry_from_step_num == '':
        retry_from_step_num = None
    else:
        retry_from_step_num = int(retry_from_step_num)

if retry_from_step_num:
    with open(RETRY_FROM_STEP_NUM_PATH, 'r') as f:
        retry_from_step_num = int(f.read())

    with open(CURRENT_STEP_NUM_PATH, 'r') as f:
        current_step_num = int(f.read())

    with open(CURRENT_STEP_NUM_PATH, 'w') as f:
        f.write(str(current_step_num+1))

    if current_step_num < retry_from_step_num and COMMAND != 'dbt deps':
        print('retry run. skipping this step')
        sys.exit()

# exit if there's been an error
with open(STATUS_PATH, 'r') as f:
    status = f.read()

if status == 'fail':
    print('failure detected. skipping step')
    sys.exit()

# otherwise, run command
os.system(f'echo "running: {COMMAND}"')
os_result = os.system(COMMAND)

dbt_invocation['completed_at'] = str(datetime.utcnow())

# raise slack error if os.system fails
if os_result != 0:
    record_failure()
else:
    if os.path.isfile(RUN_RESULTS_PATH):
        with open(RUN_RESULTS_PATH, 'r') as f:
            run_results = f.read()

        dbt_invocation['dbt_invocation_id'] = json.loads(run_results).get('metadata', {}).get('invocation_id')

        if '"status": "fail"' in run_results or '"status": "error"' in run_results:
            record_failure()

with open('dbt_invocations.json', 'a') as f:
    f.write(json.dumps(dbt_invocation))
    f.write('\n')
