import json
import os
import time

import requests

from eval_ai_interface import EvalAI_Interface
from evaluate import evaluate

# Remote Evaluation Meta Data
# See https://evalai.readthedocs.io/en/latest/evaluation_scripts.html#writing-remote-evaluation-script
auth_token = os.environ["AUTH_TOKEN"]
evalai_api_server = os.environ["API_SERVER"]
queue_name = os.environ["QUEUE_NAME"]
challenge_pk = os.environ["CHALLENGE_PK"]
save_dir = os.environ.get("SAVE_DIR", "./")


def download(submission, save_dir):
    response = requests.get(submission["input_file"])
    submission_file_path = os.path.join(
        save_dir, submission["input_file"].split("/")[-1]
    )
    with open(submission_file_path, "wb") as f:
        f.write(response.content)
    return submission_file_path


def update_running(evalai, submission_pk):
    status_data = {
        "submission": submission_pk,
        "submission_status": "RUNNING",
    }
    update_status = evalai.update_submission_status(status_data)


def update_failed(
    evalai, phase_pk, submission_pk, submission_error, stdout="", metadata=""
):
    submission_data = {
        "challenge_phase": phase_pk,
        "submission": submission_pk,
        "stdout": stdout,
        "stderr": submission_error,
        "submission_status": "FAILED",
        "metadata": metadata,
    }
    update_data = evalai.update_submission_data(submission_data)


def update_finished(
    evalai,
    phase_pk,
    submission_pk,
    result,
    submission_error="",
    stdout="",
    metadata="",
):
    submission_data = {
        "challenge_phase": phase_pk,
        "submission": submission_pk,
        "stdout": stdout,
        "stderr": submission_error,
        "submission_status": "FINISHED",
        "result": result,
        "metadata": metadata,
    }
    update_data = evalai.update_submission_data(submission_data)


if __name__ == "__main__":
    evalai = EvalAI_Interface(auth_token, evalai_api_server, queue_name, challenge_pk)

    while True:
        # Get the message from the queue
        message = evalai.get_message_from_sqs_queue()
        message_body = message.get("body")
        if message_body:
            submission_pk = message_body.get("submission_pk")
            challenge_pk = message_body.get("challenge_pk")
            phase_pk = message_body.get("phase_pk")
            # Get submission details -- This will contain the input file URL
            submission = evalai.get_submission_by_pk(submission_pk)
            challenge_phase = evalai.get_challenge_phase_by_pk(phase_pk)
            if (
                submission.get("status") == "finished"
                or submission.get("status") == "failed"
                or submission.get("status") == "cancelled"
            ):
                message_receipt_handle = message.get("receipt_handle")
                evalai.delete_message_from_sqs_queue(message_receipt_handle)

            else:
                if submission.get("status") == "submitted":
                    update_running(evalai, submission_pk)
                submission_file_path = download(submission, save_dir)
                try:
                    results = evaluate(
                        submission_file_path, challenge_phase["codename"]
                    )
                    update_finished(
                        evalai, phase_pk, submission_pk, json.dumps(results["result"])
                    )
                except Exception as e:
                    update_failed(evalai, phase_pk, submission_pk, str(e))
        # Poll challenge queue for new submissions
        time.sleep(60)
