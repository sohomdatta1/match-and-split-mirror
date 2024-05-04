#!/usr/bin/env bash
celery -A jobs.celery_app inspect ping -d worker@ld-sodium