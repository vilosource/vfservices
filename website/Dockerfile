FROM python:3.11-slim
WORKDIR /code
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY . /code
ENV PYTHONPATH=/code
CMD ["python", "website/manage.py", "runserver", "0.0.0.0:8000"]
