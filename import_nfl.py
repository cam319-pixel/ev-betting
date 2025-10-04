import pandas as pd
from datetime import datetime
from app.database import get_db
from app.models import HistoricalResult, Sport

db = get_db()

print("="*60)
print("IMPORTING NFL GAMES")
print("="*60)

# Read the NFL CSV
df = pd.read_csv('nfl_games.csv')

# Filter out rows with missing scores
df = df.dropna(subset=['score_home', 'score_away'])

count = 0
skipped = 0

for _, row in df.iterrows():
    try:
        # Parse date
        match_date = pd.to_datetime(row['schedule_date'])
        
        # Normalize team names (remove spaces, lowercase)
        home_team = str(row['team_home']).lower().replace(' ', '')
        away_team = str(row['team_away']).lower().replace(' ', '')
        
        # Skip if team names are invalid
        if home_team == 'nan' or away_team == 'nan':
            skipped += 1
            continue
        
        result = HistoricalResult(
            event_id=f"{home_team}_{away_team}_{match_date.strftime('%Y%m%d')}",
            sport=Sport.FOOTBALL,
            league='americanfootball_nfl',
            home_team=home_team,
            away_team=away_team,
            match_date=match_date,
            home_score=int(row['score_home']),
            away_score=int(row['score_away'])
        )
        
        db.save_historical_result(result)
        count += 1
        
        if count % 500 == 0:
            print(f"  Imported {count} games...")
            
    except Exception as e:
        skipped += 1
        continue

print(f"\n{'='*60}")
print(f"IMPORTED: {count} NFL games")
print(f"SKIPPED: {skipped} games (missing data)")
print(f"{'='*60}")
print("\nRun: evbet scan")