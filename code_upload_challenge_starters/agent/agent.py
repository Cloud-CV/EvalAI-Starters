import evaluation_pb2
import evaluation_pb2_grpc
import grpc
import os
import pickle
import time

time.sleep(30)

LOCAL_EVALUATION = os.environ.get("LOCAL_EVALUATION")

if LOCAL_EVALUATION:
    channel = grpc.insecure_channel("environment:8085")
else:
    channel = grpc.insecure_channel("localhost:8085")

stub = evaluation_pb2_grpc.EnvironmentStub(channel)


def pack_for_grpc(entity):
    return pickle.dumps(entity)


def unpack_for_grpc(entity):
    return pickle.loads(entity)


flag = None

while not flag:
    base = unpack_for_grpc(
        stub.act_on_environment(
            evaluation_pb2.Package(SerializedEntity=pack_for_grpc(1))
        ).SerializedEntity
    )
    flag = base["feedback"][2]
    print("Agent Feedback", base["feedback"])
    print("*" * 100)
