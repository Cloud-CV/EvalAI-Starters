import grpc
import gym
import pickle
import sys
import os
import requests
import json

from environment_utils import EvalAI_Interface

from concurrent import futures
import time

import evaluation_pb2
import evaluation_pb2_grpc

LOCAL_EVALUATION = os.environ.get("LOCAL_EVALUATION")
EVALUATION_COMPLETED = False


class evaluator_environment:
    def __init__(self, environment="CartPole-v0"):
        self.score = 0
        self.feedback = None
        self.env = gym.make(environment)
        self.env.reset()

    def get_action_space(self):
        return list(range(self.env.action_space.n))

    def next_score(self):
        self.score += 1


class Environment(evaluation_pb2_grpc.EnvironmentServicer):
    def __init__(self, challenge_pk, phase_pk, submission_pk, server):
        self.challenge_pk = challenge_pk
        self.phase_pk = phase_pk
        self.submission_pk = submission_pk
        self.server = server

    def get_action_space(self, request, context):
        message = pack_for_grpc(env.get_action_space())
        return evaluation_pb2.Package(SerializedEntity=message)

    def act_on_environment(self, request, context):
        global EVALUATION_COMPLETED
        if not env.feedback or not env.feedback[2]:
            action = unpack_for_grpc(request.SerializedEntity)
            env.next_score()
            env.feedback = env.env.step(action)
        if env.feedback[2]:
            if not LOCAL_EVALUATION:
                update_submission_result(
                    env, self.challenge_pk, self.phase_pk, self.submission_pk
                )
            else:
                print("Final Score: {0}".format(env.score))
                print("Stopping Evaluation!")
                EVALUATION_COMPLETED = True
        return evaluation_pb2.Package(
            SerializedEntity=pack_for_grpc(
                {"feedback": env.feedback, "current_score": env.score,}
            )
        )


env = evaluator_environment()
api = EvalAI_Interface(
    AUTH_TOKEN=os.environ.get("AUTH_TOKEN", "x"),
    EVALAI_API_SERVER=os.environ.get("EVALAI_API_SERVER", "http://localhost:8000"),
)


def pack_for_grpc(entity):
    return pickle.dumps(entity)


def unpack_for_grpc(entity):
    return pickle.loads(entity)


def get_action_space(env):
    return list(range(env.action_space.n))


def update_submission_result(env, challenge_pk, phase_pk, submission_pk):
    submission_data = {
        "submission_status": "finished",
        "submission": submission_pk,
    }
    submission_data = {
        "challenge_phase": phase_pk,
        "submission": submission_pk,
        "stdout": "standard_ouput",
        "stderr": "standard_error",
        "submission_status": "FINISHED",
        "result": json.dumps(
            [
                {
                    "split": "train_split",
                    "show_to_participant": True,
                    "accuracies": {"score": env.score},
                }
            ]
        ),
    }
    api.update_submission_data(submission_data, challenge_pk)
    print("Data updated successfully!")
    EVALUATION_COMPLETED = True
    exit(0)


def main():
    if not LOCAL_EVALUATION:
        BODY = os.environ.get("BODY")
        # Sample example for BODY
        # BODY = "{'submitted_image_uri': '937891341272.dkr.ecr.us-east-1.amazonaws.com/cartpole-challenge-203-participant-team-265:bb55f57f-ae44-4e76-96c2-e1ebb5d7b65a', 'submission_pk': 1351, 'phase_pk': '527', 'challenge_pk': '203'}"
        BODY = BODY.replace("'", '"')
        BODY = json.loads(BODY)
        challenge_pk = BODY["challenge_pk"]
        phase_pk = BODY["phase_pk"]
        submission_pk = BODY["submission_pk"]
    else:
        challenge_pk = "1"
        phase_pk = "1"
        submission_pk = "1"

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    evaluation_pb2_grpc.add_EnvironmentServicer_to_server(
        Environment(challenge_pk, phase_pk, submission_pk, server), server
    )
    print("Starting server. Listening on port 8085.")
    server.add_insecure_port("[::]:8085")
    server.start()
    try:
        while not EVALUATION_COMPLETED:
            time.sleep(4)
        server.stop(0)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    main()
