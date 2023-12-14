#!/bin/bash


export WEB_CONCURRENCY=$(grep ^cpu\\scores /proc/cpuinfo | uniq |  awk '{print $4}')
python manage.py run_huey -w WEB_CONCURRENCY