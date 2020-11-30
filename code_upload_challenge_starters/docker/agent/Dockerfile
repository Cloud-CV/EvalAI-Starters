FROM python:3.7.5

ENV PYTHONUNBUFFERED 1
ADD ./agent /
ADD ./utils /
ADD requirements/agent.txt /
RUN pip install --upgrade pip
RUN pip install -r agent.txt
CMD [ "python", "agent.py" ]
