FROM python:3.11-slim
WORKDIR /code/identity-provider
COPY requirements.txt /tmp/requirements.txt
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir -r /tmp/requirements.txt
COPY . /code/identity-provider
ENV PYTHONPATH=/code
COPY identity-provider/entrypoint.sh /entrypoint.sh
COPY identity-provider/scripts /code/identity-provider/scripts
RUN chmod +x /entrypoint.sh && \
    chmod +x /code/identity-provider/scripts/*.sh || true
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
