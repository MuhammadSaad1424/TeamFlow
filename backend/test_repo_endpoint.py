"""Test repository creation endpoint."""
import requests
import json

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4YjQ4YWVmOC1iZjlmLTQ5ZTktYjEzOC1hZGNjNmUwZWZiMGEiLCJleHAiOjE3ODE3MTg0NzZ9.rSDtkNgdRbC2Pm6Mn37EQXz-ZFWW0CYHDWmK1esOBnk"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
}

payload = {
    "github_url": "https://github.com/facebookresearch/detectron2",
    "name": "Detectron2",
    "description": "Facebook Meta detectron2 object detection framework"
}

try:
    response = requests.post(
        "http://localhost:8000/api/v1/repositories",
        headers=headers,
        json=payload,
        timeout=30
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
