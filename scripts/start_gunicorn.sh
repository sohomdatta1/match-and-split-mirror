#!/usr/bin/env bash
gunicorn -w 4 -b 0.0.0.0 router:app --timeout 600 --access-logfile -