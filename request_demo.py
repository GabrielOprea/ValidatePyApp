import requests

url = "https://jsonplaceholder.typicode.com/posts/1"

response = requests.get(url)

if response.status_code == 200:
    print("Request was successful!")
    print(response.json())
else:
    print(f"Request failed with status code: {response.status_code}")