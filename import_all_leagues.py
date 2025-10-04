import pandas as pd
from datetime import datetime
from app.database import get_db
from app.models import HistoricalResult, Sport

db = get_db()

# SOCCER - Football-data.co.uk (FREE)
print("="*60)
print("IMPORTING SOCCER")
print("="*60)

soccer_leagues = {
    'E0': 'soccer_epl',
    'SP1': 'soccer_spain_la_liga',
    'D1': 'soccer_germany_bundesliga',
    'I1': 'soccer_italy_serie_a',
    'F1': 'soccer_france_ligue_one',
}

total_soccer = 0

for league_code, league_name in soccer_leagues.items():
    print(f"\nDownloading {league_name}...")
    seasons = ['2324', '2223', '2122']
    
    for season in seasons:
        try:
            url = f"https://www.football-data.co.uk/mmz4281/{season}/{league_code}.csv"
            df = pd.read_csv(url)
            
            count = 0
            for _, row in df.iterrows():
                try:
                    match_date = datetime.strptime(row['Date'], '%d/%m/%Y')
                    home_team = row['HomeTeam'].lower().replace(' ', '').replace('united', '').replace('city', '')
                    away_team = row['AwayTeam'].lower().replace(' ', '').replace('united', '').replace('city', '')
                    
                    result = HistoricalResult(
                        event_id=f"{home_team}_{away_team}_{match_date.strftime('%Y%m%d')}",
                        sport=Sport.SOCCER,
                        league=league_name,
                        home_team=home_team,
                        away_team=away_team,
                        match_date=match_date,
                        home_score=int(row['FTHG']),
                        away_score=int(row['FTAG']),
                        home_odds=float(row['B365H']) if pd.notna(row.get('B365H')) else None,
                        draw_odds=float(row['B365D']) if pd.notna(row.get('B365D')) else None,
                        away_odds=float(row['B365A']) if pd.notna(row.get('B365A')) else None
                    )
                    
                    db.save_historical_result(result)
                    count += 1
                except:
                    continue
            
            print(f"  Season {season}: {count} matches")
            total_soccer += count
        except:
            print(f"  Season {season}: Failed")

# NBA - Using sports-reference.com format (may need adjustment)
print("\n" + "="*60)
print("IMPORTING NBA")
print("="*60)
print("Note: NBA historical data requires paid API or manual CSV")
print("Skipping NBA for now - add your own CSV if you have one")

# NFL - Similar issue
print("\n" + "="*60)
print("IMPORTING NFL")
print("="*60)
print("Note: NFL historical data requires paid API or manual CSV")
print("Skipping NFL for now - add your own CSV if you have one")

print("\n" + "="*60)
print(f"TOTAL IMPORTED: {total_soccer} soccer matches")
print("="*60)
print("\nFor NBA/NFL data:")
print("1. Get historical data from kaggle.com/datasets")
print("2. Or use a paid API like sportsdata.io")
print("3. Format as CSV with columns: Date, HomeTeam, AwayTeam, HomeScore, AwayScore")
print("\nRun: evbet scan")