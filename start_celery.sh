#!/bin/bash

# Start Celery worker
celery -A src.celery_config:celery worker --loglevel=info &

# Start Celery beat
celery -A src.celery_config:celery beat --loglevel=info &

# Wait for all background processes to finish
wait