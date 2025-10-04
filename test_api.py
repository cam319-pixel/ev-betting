import httpx

api_key = "45853738501b4223d661a09e0e1530e9"  # Replace with your actual key
url = f"https://api.the-odds-api.com/v4/sports/?apiKey={api_key}"

response = httpx.get(url)
print(response.json())