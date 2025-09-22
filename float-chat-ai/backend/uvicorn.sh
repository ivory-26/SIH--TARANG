#!/bin/bash
# Uvicorn startup script for Float-Chat-AI backend

# Load environment variables if .env file exists
if [ -f ".env" ]; then
    export $(cat .env | xargs)
fi

# Start uvicorn server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level info