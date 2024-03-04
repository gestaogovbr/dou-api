#!/bin/sh

# Make env vars available to cronjob
printenv | grep -v "no_proxy" >> /etc/environment

# Start cron in the background
cron

# Start Gunicorn and run in the foreground
exec gunicorn -w 4 -b 0.0.0.0:5057 api:app
