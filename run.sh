#!/bin/bash

# load .env
export $(grep -v '^#' .env | xargs)

# show prompt version
echo "Using Prompt Template: $SYSTEM_PROMPT_PATH"

# start Gradio service
python Agent.py

