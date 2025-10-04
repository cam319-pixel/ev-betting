import pandas as pd
import requests
from datetime import datetime
from app.database import get_db
from app.models import HistoricalResult, Sport

# Download free soccer data from football-data.co.uk
print("Downloading EPL historical data...")

# EPL 2023-2024 season
url = "https://www.football-data.co.uk/mmz4281/2324/E0.csv"
df = pd.read_csv(url)

db = get_db()
count = 0

for _, row in df.iterrows():
    try:
        # Parse date (format: DD/MM/YYYY)
        match_date = datetime.strptime(row['Date'], '%d/%m/%Y')
        
        # Normalize team names
        home_team = row['HomeTeam'].lower().replace(' ', '')
        away_team = row['AwayTeam'].lower().replace(' ', '')
        
        result = HistoricalResult(
            event_id=f"{home_team}_{away_team}_{match_date.strftime('%Y%m%d')}",
            sport=Sport.SOCCER,
            league="soccer_epl",
            home_team=home_team,
            away_team=away_team,
            match_date=match_date,
            home_score=int(row['FTHG']),
            away_score=int(row['FTAG']),
            home_odds=float(row['B365H']) if pd.notna(row['B365H']) else None,
            draw_odds=float(row['B365D']) if pd.notna(row['B365D']) else None,
            away_odds=float(row['B365A']) if pd.notna(row['B365A']) else None
        )
        
        db.save_historical_result(result)
        count += 1
    except Exception as e:
        print(f"Error: {e}")
        continue

print(f"\nImported {count} EPL matches!")
print("Run 'evbet scan' again to see better predictions.")