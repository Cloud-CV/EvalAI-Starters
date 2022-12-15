import time

from remote_evaluation_util import RemoteEvaluationUtil

if __name__ == "__main__":

    remote_evaluation_util = RemoteEvaluationUtil()
    evalai = remote_evaluation_util.evalai

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

            else: # status is submitted
                remote_evaluation_util.update_running(submission, job_name="")
                submission_file_path = remote_evaluation_util.download(submission)
                remote_evaluation_util.evaluate(submission_file_path, challenge_pk, phase_pk, submission_pk)

        # Poll challenge queue for new submissions
        time.sleep(60)
