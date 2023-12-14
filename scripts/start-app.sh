#!/bin/bash
# Pull aws secrets
# aws secretsmanager get-secret-value --secret-id developmentSecrets --query SecretString --output text > secrets.json
export WEB_CONCURRENCY=$(grep ^cpu\\scores /proc/cpuinfo | uniq |  awk '{print $4}')
python3 manage.py makemigrations
python3 manage.py migrate
gunicorn --workers=$WEB_CONCURRENCY core.wsgi:application 