FROM python:3.7.5

ENV PYTHONUNBUFFERED 1
ADD ./environment /
ADD ./utils /
ADD requirements/environment.txt /
RUN pip install --upgrade pip
RUN pip install -r environment.txt
CMD ["python", "environment.py"]
