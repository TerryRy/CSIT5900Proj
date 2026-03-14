#!/bin/bash

# ========== 可修改的配置项 ==========
export AZURE_ENDPOINT="https://hkust.azure-api.net/"
export AZURE_API_KEY="dbfc4f7054684d0ba3e3c76e8a5e3a07"
export AZURE_API_VERSION="2025-02-01-preview"
export DEPLOYMENT_NAME="gpt-4o-mini"
export SYSTEM_PROMPT_PATH="./prompt.txt"
# ====================================

# 启动Gradio服务
python Agent.py