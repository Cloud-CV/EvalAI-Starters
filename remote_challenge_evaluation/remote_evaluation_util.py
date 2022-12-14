from eval_ai_interface import EvalAI_Interface


class RemoteEvaluationUtil:
    def __init__(self):
        self.auth_token = ""  # Go to EvalAI UI to fetch your auth token
        self.evalai_api_server = ""  # For staging server, use -- https://staging.eval.ai; For production server, use -- https://eval.ai
        self.queue_name = ""  # Check Manage Tab of challenge for queue name
        self.challenge_pk = ""  # Check Manage Tab of challenge for challenge PK

        # Create evalai object
        self.evalai = EvalAI_Interface(
            self.auth_token, self.evalai_api_server, self.queue_name, self.challenge_pk
        )

    def download_and_evaluate(
        self, submission, challenge_pk, phase_pk, submission_pk
    ):

        # Set the status to running
        # self._update_running(submission, job_name="")

        # Download the input file
        # The submission file URL can be found at submission_input_file_url = submission.input_file.url
        # Run the submission with the input file using your own code and data.

        # Once the submission is done, make an API call to our queue to inform that the message is evaluated
        # self._update_finished(
        #     evalai,
        #     phase_pk,
        #     submission_pk,
        #     result='[{"split": "<split-name>", "show_to_participant": true,"accuracies": {"Metric1": 80,"Metric2": 60,"Metric3": 60,"Total": 10}}]'
        # )
        pass

    def _update_running(self, submission, job_name):
        status_data = {
            "submission": submission,
            "job_name": job_name,
            "submission_status": "RUNNING",
        }
        update_status = self.evalai.update_submission_status(status_data)

    def _update_failed(
        self, phase_pk, submission_pk, submission_error, stdout="", metadata=""
    ):
        submission_data = {
            "challenge_phase": phase_pk,
            "submission": submission_pk,
            "stdout": stdout,
            "stderr": submission_error,
            "submission_status": "FAILED",
            "metadata": metadata,
        }
        update_data = self.evalai.update_submission_data(submission_data)

    def _update_finished(
        self,
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
        update_data = self.evalai.update_submission_data(submission_data)
