#!/usr/bin/env python3
"""Import soccer historical data from results.csv"""

import pandas as pd
from datetime import datetime
from pathlib import Path
from app.config import get_config
from app.database import get_db
from app.models import HistoricalResult, Sport


def normalize_team_name(name):
    """Normalize team names to match odds API format"""
    # Convert to lowercase and strip whitespace
    name = str(name).lower().strip()
    
    # Common team name mappings
    replacements = {
        'man united': 'manchester united',
        'man city': 'manchester city',
        'spurs': 'tottenham',
        'wolves': 'wolverhampton wanderers',
        'brighton': 'brighton and hove albion',
        'west ham': 'west ham united',
        'newcastle': 'newcastle united',
        'leeds': 'leeds united',
        'leicester': 'leicester city',
        'norwich': 'norwich city',
        'crystal palace': 'crystal palace',
    }
    
    return replacements.get(name, name)


def import_soccer_results(csv_path, league='EPL'):
    """Import soccer results from CSV
    
    Args:
        csv_path: Path to results.csv
        league: League identifier (default: EPL)
    """
    print(f"Importing soccer data from {csv_path}...")
    
    # Try different encodings
    for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
        try:
            df = pd.read_csv(csv_path, encoding=encoding)
            print(f"  Successfully read with {encoding} encoding")
            break
        except UnicodeDecodeError:
            continue
    else:
        print(f"✗ Could not read CSV with any encoding")
        return 0
    db = get_db()
    count = 0
    skipped = 0
    
    for _, row in df.iterrows():
        # Parse the date
        try:
            match_date = pd.to_datetime(row['DateTime'])
        except:
            skipped += 1
            continue
        
        # Get team names
        home_team = normalize_team_name(row['HomeTeam'])
        away_team = normalize_team_name(row['AwayTeam'])
        
        # Get scores (FTHG = Full Time Home Goals, FTAG = Full Time Away Goals)
        try:
            home_score = int(row['FTHG'])
            away_score = int(row['FTAG'])
        except:
            skipped += 1
            continue
        
        # Create event ID
        event_id = f"{home_team}_{away_team}_{match_date.strftime('%Y%m%d')}"
        
        # Save result
        result = HistoricalResult(
            event_id=event_id,
            sport=Sport.SOCCER,
            league=league,
            home_team=home_team,
            away_team=away_team,
            match_date=match_date,
            home_score=home_score,
            away_score=away_score,
            home_odds=None,
            draw_odds=None,
            away_odds=None
        )
        
        try:
            db.save_historical_result(result)
            count += 1
            if count % 100 == 0:
                print(f"  Imported {count} games...")
        except Exception as e:
            skipped += 1
            continue
    
    print(f"✓ Imported {count} soccer games")
    if skipped > 0:
        print(f"  Skipped {skipped} games (missing data or duplicates)")
    
    return count


def import_nfl_csv(csv_path):
    """Import NFL historical data from CSV"""
    print(f"Importing NFL data from {csv_path}...")
    
    df = pd.read_csv(csv_path)
    db = get_db()
    count = 0
    skipped = 0
    
    for _, row in df.iterrows():
        try:
            match_date = pd.to_datetime(row['schedule_date'])
            home_team = str(row['team_home']).lower().strip()
            away_team = str(row['team_away']).lower().strip()
            home_score = int(row['score_home'])
            away_score = int(row['score_away'])
        except:
            skipped += 1
            continue
        
        event_id = f"{home_team}_{away_team}_{match_date.strftime('%Y%m%d')}"
        
        result = HistoricalResult(
            event_id=event_id,
            sport=Sport.FOOTBALL,
            league="NFL",
            home_team=home_team,
            away_team=away_team,
            match_date=match_date,
            home_score=home_score,
            away_score=away_score,
            home_odds=None,
            draw_odds=None,
            away_odds=None
        )
        
        try:
            db.save_historical_result(result)
            count += 1
            if count % 100 == 0:
                print(f"  Imported {count} NFL games...")
        except:
            skipped += 1
    
    print(f"✓ Imported {count} NFL games")
    if skipped > 0:
        print(f"  Skipped {skipped} games")
    
    return count


def import_nba_csv(csv_path):
    """Import NBA historical data from CSV"""
    print(f"Importing NBA data from {csv_path}...")
    
    df = pd.read_csv(csv_path)
    db = get_db()
    count = 0
    skipped = 0
    
    # Process by game_id to avoid duplicates (CSV has one row per game)
    processed_games = set()
    
    for _, row in df.iterrows():
        try:
            game_id = row['game_id']
            
            # Skip if already processed
            if game_id in processed_games:
                continue
            
            match_date = pd.to_datetime(row['game_date'])
            home_team = str(row['team_name_home']).lower().strip()
            away_team = str(row['team_name_away']).lower().strip()
            home_score = int(row['pts_home'])
            away_score = int(row['pts_away'])
            
            event_id = f"{home_team}_{away_team}_{match_date.strftime('%Y%m%d')}"
            
            result = HistoricalResult(
                event_id=event_id,
                sport=Sport.BASKETBALL,
                league="NBA",
                home_team=home_team,
                away_team=away_team,
                match_date=match_date,
                home_score=home_score,
                away_score=away_score,
                home_odds=None,
                draw_odds=None,
                away_odds=None
            )
            
            db.save_historical_result(result)
            processed_games.add(game_id)
            count += 1
            if count % 100 == 0:
                print(f"  Imported {count} NBA games...")
        except Exception as e:
            skipped += 1
            continue
    
    print(f"✓ Imported {count} NBA games")
    if skipped > 0:
        print(f"  Skipped {skipped} games")
    
    return count


if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("HISTORICAL DATA IMPORT")
    print("=" * 60)
    
    total = 0
    
    # Import soccer results
    soccer_path = Path("data/results.csv")
    if soccer_path.exists():
        total += import_soccer_results(soccer_path, league="EPL")
    else:
        print(f"✗ Soccer file not found: {soccer_path}")
    
    # Import NFL results
    nfl_path = Path("data/nfl_games.csv")
    if nfl_path.exists():
        total += import_nfl_csv(nfl_path)
    else:
        print(f"✗ NFL file not found: {nfl_path}")
    
    # Import NBA results
    nba_path = Path("data/nba_games.csv")
    if nba_path.exists():
        total += import_nba_csv(nba_path)
    else:
        print(f"✗ NBA file not found: {nba_path}")
    
    print("\n" + "=" * 60)
    print(f"TOTAL: Imported {total} historical games")
    print("=" * 60)
    
    if total > 0:
        print("\nNow delete the cached models so they retrain:")
        print("  rm -rf data/cache/models/*")
        print("\nThen run: evbet scan")