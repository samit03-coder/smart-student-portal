import requests

url = "https://07f8b85b0ce1.ngrok-free.app"  # Replace with your actual Ngrok URL

headers = {
    "ngrok-skip-browser-warning": "true"
}

response = requests.get(url, headers=headers)
print("Status Code:", response.status_code)
print("Response Body:\n", response.text)
