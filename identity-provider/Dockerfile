FROM python:3.11-slim
WORKDIR /code/identity-provider
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY . /code/identity-provider
ENV PYTHONPATH=/code
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
