FROM python:3.11.4-slim-bullseye

RUN apt-get update && apt-get install -y cron

COPY ./job/cronjob /etc/cron.d/dou-cronjob

RUN chmod 0644 /etc/cron.d/dou-cronjob && \
    crontab /etc/cron.d/dou-cronjob && \
    touch /var/log/cron.log

WORKDIR /dou-api

ENV PYTHONPATH /dou-api/app

COPY . /dou-api

RUN python -m pip install -r requirements.txt --no-cache-dir

EXPOSE 5057

COPY start.sh /start.sh

RUN chmod +x /start.sh

CMD ["/start.sh"]
