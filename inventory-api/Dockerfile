FROM python:3.11-slim
WORKDIR /code/inventory-api
COPY requirements.txt /tmp/requirements.txt
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir -r /tmp/requirements.txt
COPY . /code/inventory-api
ENV PYTHONPATH=/code
COPY inventory-api/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
