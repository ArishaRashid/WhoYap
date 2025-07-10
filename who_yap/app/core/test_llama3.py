import requests

if __name__ == "__main__":
    print("Starting test")
    try:
        resp = requests.post(
            "http://localhost:8000/llama3-chat",
            json={"prompt": "Say hello in French"}
        )
        resp.raise_for_status()
        print("Response received:")
        print(resp.json())
    except Exception as e:
        print("An error occurred:")
        print(e)
    print("Test finished.")
