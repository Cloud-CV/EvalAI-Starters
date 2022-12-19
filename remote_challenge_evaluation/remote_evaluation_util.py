import os
import requests
from eval_ai_interface import EvalAI_Interface


class RemoteEvaluationUtil:
    def __init__(self):
        # TODO: Populate the variables for the evaluation
        self.auth_token = os.environ["AUTH_TOKEN"]  # Go to EvalAI UI to fetch your auth token
        self.evalai_api_server = os.environ["API_SERVER"]  # For staging server, use -- https://staging.eval.ai; For production server, use -- https://eval.ai
        self.queue_name = os.environ["QUEUE_NAME"]  # Check Manage Tab of challenge for queue name
        self.challenge_pk = os.environ["CHALLENGE_PK"]  # Check Manage Tab of challenge for challenge PK
        self.save_dir = os.environ.get("SAVE_DIR", "./") # Location where submissions are downloaded

        self.evalai = EvalAI_Interface(
            self.auth_token, self.evalai_api_server, self.queue_name, self.challenge_pk
        )

    def download(self, submission):
        response = requests.get(submission.input_file.url)
        submission_file_path = os.path.join(self.save_dir, submission.input_file.name)
        with open(submission_file_path, "wb") as f:
            f.write(response.content)
        return submission_file_path

    # TODO: Write an evaluate method, change default parameters.
    def evaluate(user_submission_file, phase_codename, challenge_pk, phase_pk, submission_pk, test_annotation_file = None, **kwargs):
        """ 
        Evaluates the submission for a particular challenge phase and returns score
        Arguments:
            
            `user_submission_file`: Path to file submitted by the user.
            `phase_codename`: Phase to which submission is made.
            `challenge_pk`: Challenge ID.
            `phase_pk`: Challenge Phase ID.
            `submission_pk`: Submission ID.
            `test_annotations_file`: Path to test_annotation_file on the server.
                Please update Line 32 in `main.py` if you change this. 
                We recommend using `phase_codename` to select local test annotation files instead or a default value.
            
            `**kwargs`: keyword arguments that contains additional submission
            metadata that challenge hosts can use to send slack notification.
            You can access the submission metadata
            with kwargs['submission_metadata']
            
            Example: A sample submission metadata can be accessed like this:
            >>> print(kwargs['submission_metadata'])
            {
                'status': u'running',
                'when_made_public': None,
                'participant_team': 5,
                'input_file': 'https://abc.xyz/path/to/submission/file.json',
                'execution_time': u'123',
                'publication_url': u'ABC',
                'challenge_phase': 1,
                'created_by': u'ABC',
                'stdout_file': 'https://abc.xyz/path/to/stdout/file.json',
                'method_name': u'Test',
                'stderr_file': 'https://abc.xyz/path/to/stderr/file.json',
                'participant_team_name': u'Test Team',
                'project_url': u'http://foo.bar',
                'method_description': u'ABC',
                'is_public': False,
                'submission_result_file': 'https://abc.xyz/path/result/file.json',
                'id': 123,
                'submitted_at': u'2017-03-20T19:22:03.880652Z'
            }
        """
        pass
    
    def update_running(self, submission, job_name):
        # Set the status to running
        status_data = {
            "submission": submission,
            "job_name": job_name,
            "submission_status": "RUNNING",
        }
        update_status = self.evalai.update_submission_status(status_data)

    def update_failed(
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

    def update_finished(
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
