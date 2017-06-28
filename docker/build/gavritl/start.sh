#!/bin/bash

if [ $RUN_MODE = "gavritl_web" ]
then
    # Start Gunicorn processes
    echo Starting Gunicorn.
    exec gunicorn gavritl.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers 2 \
        --reload \
        --preload \
        --timeout 60
else
    # start standalone process
    echo Starting standalone django app.
    exec python standalone.py
fi