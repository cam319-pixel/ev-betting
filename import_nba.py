import pandas as pd
from datetime import datetime
from app.database import get_db
from app.models import HistoricalResult, Sport

db = get_db()

print("="*60)
print("IMPORTING NBA GAMES")
print("="*60)

# Read the NBA CSV
df = pd.read_csv('nba_games.csv')

# Filter out rows with missing scores
df = df.dropna(subset=['pts_home', 'pts_away'])

count = 0
skipped = 0

for _, row in df.iterrows():
    try:
        # Parse date
        match_date = pd.to_datetime(row['game_date'])
        
        # Normalize team names (remove spaces, lowercase)
        home_team = str(row['team_name_home']).lower().replace(' ', '')
        away_team = str(row['team_name_away']).lower().replace(' ', '')
        
        # Skip if team names are invalid
        if home_team == 'nan' or away_team == 'nan':
            skipped += 1
            continue
        
        result = HistoricalResult(
            event_id=f"{home_team}_{away_team}_{match_date.strftime('%Y%m%d')}",
            sport=Sport.BASKETBALL,
            league='basketball_nba',
            home_team=home_team,
            away_team=away_team,
            match_date=match_date,
            home_score=int(row['pts_home']),
            away_score=int(row['pts_away'])
        )
        
        db.save_historical_result(result)
        count += 1
        
        if count % 1000 == 0:
            print(f"  Imported {count} games...")
            
    except Exception as e:
        skipped += 1
        continue

print(f"\n{'='*60}")
print(f"IMPORTED: {count} NBA games")
print(f"SKIPPED: {skipped} games")
print(f"{'='*60}")
print("\nRun: evbet scan")