FROM python:3.11-slim
WORKDIR /code/cielo_website
COPY requirements.txt /tmp/requirements.txt
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir -r /tmp/requirements.txt
#COPY . /code/cielo_website
ENV PYTHONPATH=/code
COPY cielo_website/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]