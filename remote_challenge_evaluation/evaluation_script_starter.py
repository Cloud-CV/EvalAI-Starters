import logging
import requests
import json
import time

logger = logging.getLogger(__name__)


URLS = {
    "get_message_from_sqs_queue": "/api/jobs/challenge/queues/{}/",
    "get_submission_by_pk": "/api/jobs/submission/{}",
    "delete_message_from_sqs_queue": "/api/jobs/queues/{}/",
    "update_evaluated_submission": "/api/jobs/challenges/{}/update_partially_evaluated_submission/",
}


class EvalAI_Interface:
    def __init__(self, AUTH_TOKEN, EVALAI_API_SERVER, QUEUE_NAME, CHALLENGE_PK):
        """Class to initiate call to EvalAI backend

        Arguments:
            AUTH_TOKEN {[string]} -- The authentication token corresponding to EvalAI
            EVALAI_API_SERVER {[string]} -- It should be set to https://eval.ai # For production server
            QUEUE_NAME {[string]} -- Unique queue name corresponding to every challenge
            CHALLENGE_PK {[integer]} -- Primary key corresponding to a challenge
        """

        self.AUTH_TOKEN = AUTH_TOKEN
        self.EVALAI_API_SERVER = EVALAI_API_SERVER
        self.QUEUE_NAME = QUEUE_NAME
        self.CHALLENGE_PK = CHALLENGE_PK

    def get_request_headers(self):
        headers = {"Authorization": "Token {}".format(self.AUTH_TOKEN)}
        return headers

    def make_request(self, url, method, data=None):
        headers = self.get_request_headers()
        try:
            response = requests.request(
                method=method, url=url, headers=headers, data=data
            )
            response.raise_for_status()
        except requests.exceptions.RequestException:
            logger.info("The server isn't able establish connection with EvalAI")
            raise
        return response.json()

    def return_url_per_environment(self, url):
        base_url = "{0}".format(self.EVALAI_API_SERVER)
        url = "{0}{1}".format(base_url, url)
        return url

    def get_message_from_sqs_queue(self):
        url = URLS.get("get_message_from_sqs_queue").format(self.QUEUE_NAME)
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "GET")
        return response

    def delete_message_from_sqs_queue(self, receipt_handle):
        url = URLS.get("delete_message_from_sqs_queue").format(self.QUEUE_NAME)
        url = self.return_url_per_environment(url)
        data = {"receipt_handle": receipt_handle}
        response = self.make_request(url, "POST", data)
        return response

    def update_submission_data(self, data, challenge_pk, submission_pk):
        url = URLS.get("update_evaluated_submission").format(self.CHALLENGE_PK)
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "PUT", data=data)
        return response

    def update_submission_status(self, data, challenge_pk):
        url = URLS.get("update_evaluated_submission").format(self.CHALLENGE_PK)
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "PATCH", data=data)
        return response

    def update_submission_data_partially(self, data, challenge_pk):
        url = URLS.get("update_evaluated_submission").format(self.CHALLENGE_PK)
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "PUT", data=data)
        return response

    def get_submission_by_pk(self, submission_pk):
        url = URLS.get("get_submission_by_pk").format(submission_pk)
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "GET")
        return response


if __name__ == "__main__":

    auth_token = ""  # Go to EvalAI UI to fetch your auth token
    evalai_api_server = ""  # For staging server, use -- https://staging.eval.ai
    # For production server, use -- https://eval.ai
    queue_name = (
        ""  # Please email EvalAI admin (team@cloudcv.org) to get the queue name
    )
    challenge_pk = (
        ""  # Please email EvalAI admin (team@cloudcv.org) to get the challenge primary key
    )

    # Create evalai object
    evalai = EvalAI_Interface(auth_token, evalai_api_server, queue_name, challenge_pk)

    # Q. How to set up the remote evaluation?
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

            if (
                submission.get("status") == "finished"
                or submission.get("status") == "failed"
                or submission.get("status") == "cancelled"
            ):
                message_receipt_handle = message.get("receipt_handle")
                evalai.delete_message_from_sqs_queue(message_receipt_handle)

            elif submission.get("status") == "running":
                # Do nothing on EvalAI
                pass

            else:
                # Download the input file
                # Run the submission with the file.
                pass

        time.sleep(60)

    # Q. How to update EvalAI with the submission state?

    # 1. Update EvalAI right after sending the submission into "RUNNING" state,
    status_data = {"submission": "", "job_name": "", "submission_status": "RUNNING"}
    update_status = evalai.update_submission_status(status_data, challenge_pk)

    # 2. Update EvalAI after calculating final set of metrics and set submission status as "FINISHED"
    submission_data = {
        "challenge_phase": "<phase_pk>",
        "submission": "<submission_pk>",
        "stdout": "",
        "stderr": "",
        "submission_status": "FINISHED",
        "result": '[{"split": "<split-name>", "show_to_participant": true,"accuracies": {"Metric1": 80,"Metric2": 60,"Metric3": 60,"Total": 10}}]',
        "metadata": "",
    }
    update_data = evalai.update_submission_data_partially(
        submission_data, challenge_pk, submission_pk
    )
    # OR
    # 3. Update EvalAI in case of errors and set submission status as "FAILED"
    submission_data = {
        "challenge_phase": "<phase_pk>",
        "submission": "<submission_pk>",
        "stdout": "",
        "stderr": "<ERROR FROM SUBMISSION>",
        "submission_status": "FAILED",
        "metadata": "",
    }
    update_data = evalai.update_submission_data_partially(
        submission_data, challenge_pk, submission_pk
    )
