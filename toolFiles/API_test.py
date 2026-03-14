'''
curl https://hkust.azure-api.net/openai/deployments/gpt-4o-mini/chat/completions?api-version=2024-10-21 \
    -H "Content-Type: application/json" \
    -H "api-key: dbfc4f7054684d0ba3e3c76e8a5e3a07" \
    -d '{"messages": [{"role": "system", "content": "您是 Azure 专家。"},
                                  {"role": "user", "content": "什么是 OpenAI？"}]}'


curl https://hkust.azure-api.net/openai/deployments/gpt-4o-mini/chat/completions?api-version=2025-02-01-preview -H "Content-Type: application/json" -H "api-key: dbfc4f7054684d0ba3e3c76e8a5e3a07"  -d '{"messages": [{"role": "system", "content": "您是 Azure 专家。"}, {"role": "user", "content": "什么是 OpenAI？"}]}'
'''

import os
from openai import AzureOpenAI

# ── 改這裡 ────────────────────────────────
API_KEY = "dbfc4f7054684d0ba3e3c76e8a5e3a07"
ENDPOINT = "https://hkust.azure-api.net/"   # 例如 https://hkustopenai.openai.azure.com/
DEPLOYMENT_NAME = "gpt-4o-mini"   # 或 gpt-35-turbo、gpt-4o，看你 portal 有什麼
API_VERSION = "2025-02-01-preview"   # 常用版本，新的可以用 "2025-03-01-preview" 等
# ───────────────────────────────────────────

client = AzureOpenAI(
    azure_endpoint = ENDPOINT,
    api_key = API_KEY,
    api_version = API_VERSION
)

response = client.chat.completions.create(
    model=DEPLOYMENT_NAME,  # 這裡填 deployment name，不是模型名稱
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "1+1等于几？"}
    ],
    temperature=0.7,
    max_tokens=300
)

print("AI 回覆：")
print(response.choices[0].message.content)