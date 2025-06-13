FROM python:3.11-slim
WORKDIR /code/billing-api
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY . /code/billing-api
ENV PYTHONPATH=/code
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
