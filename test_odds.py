import httpx

api_key = "45853738501b4223d661a09e0e1530e9"  # Replace with your actual key

# Test EPL
sport = "soccer_epl"
url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
params = {
    "apiKey": api_key,
    "regions": "us,uk,eu",
    "markets": "h2h",
    "oddsFormat": "decimal"
}

response = httpx.get(url, params=params)
print(f"Status: {response.status_code}")
print(f"Number of games: {len(response.json())}")
print("\nFirst game (if any):")
if response.json():
    game = response.json()[0]
    print(f"Teams: {game['home_team']} vs {game['away_team']}")
    print(f"Start time: {game['commence_time']}")
else:
    print("No games found")

print(f"\nRequests remaining: {response.headers.get('x-requests-remaining')}")