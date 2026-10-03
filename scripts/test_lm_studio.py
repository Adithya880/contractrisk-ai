"""
LM Studio Local API Verification Script for ContractRisk AI
------------------------------------------------------------
Uses the local LM Studio OpenAI-compatible API (http://127.0.0.1:1234/v1).
Checks:
- Server reachability
- HTTP status
- Available models (/v1/models)
- Sends a tiny test prompt to model 'qwen3-4b-instruct-2507'
- Prints the returned response
- Handles connection errors clearly

Does NOT require an API key for localhost.
Does NOT send any contract data.
"""

import sys
import os
import requests

def test_lm_studio():
    base_url = os.getenv("LLM_BASE_URL", "http://127.0.0.1:1234/v1").rstrip("/")
    target_model = os.getenv("LLM_MODEL", "qwen3-4b-instruct-2507")

    print("=" * 65)
    print(" CONTRACTRISK AI — LOCAL LM STUDIO VERIFICATION")
    print("=" * 65)
    print(f"Target Base URL: {base_url}")
    print(f"Target Model:    {target_model}")

    # 1. Check server reachability and list available models
    models_endpoint = f"{base_url}/models"
    print(f"\n1. Querying available models at: {models_endpoint}")
    try:
        response = requests.get(models_endpoint, timeout=10)
        print(f"   HTTP Status: {response.status_code}")
        if response.status_code == 200:
            models_data = response.json()
            available_models = [m.get("id") for m in models_data.get("data", [])]
            print(f"   Available Models: {available_models}")
        else:
            print(f"   [WARNING] Unexpected status code from /v1/models: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   [ERROR] Could not connect to LM Studio at {base_url}")
        print(f"   Details: {e}")
        print("\nTroubleshooting:")
        print(" - Verify LM Studio is open and running.")
        print(" - Verify Local Server is started on http://127.0.0.1:1234.")
        print(" - Check that Qwen3 4B Instruct 2507 is loaded.")
        sys.exit(1)

    # 2. Send a tiny test prompt to the chat completions endpoint
    chat_endpoint = f"{base_url}/chat/completions"
    print(f"\n2. Sending test prompt to chat endpoint: {chat_endpoint}")

    payload = {
        "model": target_model,
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant. Answer concisely in one sentence."
            },
            {
                "role": "user",
                "content": "Confirm that the local AI server is active and responding."
            }
        ],
        "temperature": 0.2,
        "max_tokens": 50
    }

    try:
        response = requests.post(chat_endpoint, json=payload, timeout=20)
        print(f"   HTTP Status: {response.status_code}")
        if response.status_code == 200:
            res_json = response.json()
            choices = res_json.get("choices", [])
            if choices and "message" in choices[0]:
                content = choices[0]["message"].get("content", "").strip()
                print(f"\nReturned Model Response:")
                print("-" * 50)
                print(content)
                print("-" * 50)
                print("\n[SUCCESS] LM Studio local API is fully operational!")
            else:
                print(f"\n[WARNING] Response JSON missing choices format: {res_json}")
        else:
            print(f"\n[ERROR] HTTP POST failed with status {response.status_code}: {response.text}")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"\n[ERROR] Chat completion request failed: {e}")
        sys.exit(1)

    print("=" * 65)

if __name__ == "__main__":
    test_lm_studio()
