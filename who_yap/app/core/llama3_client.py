import requests
from .config import LlamaConfig

def llama3_chat(prompt, model=LlamaConfig.MODEL_NAME, base_url=LlamaConfig.BASE_URL):
    url = f"{base_url}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()["response"] 