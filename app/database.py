import sqlite3
from datetime import datetime
from pathlib import Path
import pandas as pd
from app.config import get_config
from app.models import RawOdds, HistoricalResult, ValueBet


class Database:
    def __init__(self, db_path=None):
        config = get_config()
        if db_path is None:
            cache_dir = Path(config.general.cache_dir)
            cache_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(cache_dir / "evbet.db")
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_tables()
    
    def _init_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw_odds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT, event_id TEXT, sport TEXT, league TEXT,
                home_team TEXT, away_team TEXT, start_time TEXT,
                market TEXT, outcome TEXT, price_decimal REAL,
                last_updated TEXT,
                UNIQUE(provider, event_id, market, outcome)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historical_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE, sport TEXT, league TEXT,
                home_team TEXT, away_team TEXT, match_date TEXT,
                home_score INTEGER, away_score INTEGER,
                home_odds REAL, draw_odds REAL, away_odds REAL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS value_bets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT, league TEXT, home_team TEXT, away_team TEXT,
                start_time_local TEXT, bookmaker TEXT, market TEXT,
                outcome TEXT, price_decimal REAL, model_prob REAL,
                market_prob_devig REAL, edge_pct REAL, ev REAL,
                kelly_stake REAL, created_at TEXT
            )
        """)
        self.conn.commit()
    
    def cache_odds(self, odds):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO raw_odds 
            (provider, event_id, sport, league, home_team, away_team, 
             start_time, market, outcome, price_decimal, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (odds.provider, odds.event_id, odds.sport.value, odds.league,
              odds.home_team, odds.away_team, odds.start_time.isoformat(),
              odds.market.value, odds.outcome.value, odds.price_decimal,
              odds.last_updated.isoformat()))
        self.conn.commit()
    
    def save_historical_result(self, result):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO historical_results
            (event_id, sport, league, home_team, away_team, match_date,
             home_score, away_score, home_odds, draw_odds, away_odds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (result.event_id, result.sport.value, result.league,
              result.home_team, result.away_team, result.match_date.isoformat(),
              result.home_score, result.away_score,
              result.home_odds, result.draw_odds, result.away_odds))
        self.conn.commit()
    
    def get_historical_results(self, sport=None, league=None):
        query = "SELECT * FROM historical_results WHERE 1=1"
        params = []
        if sport:
            query += " AND sport = ?"
            params.append(sport)
        if league:
            query += " AND league = ?"
            params.append(league)
        return pd.read_sql_query(query, self.conn, params=params)
    
    def save_value_bet(self, bet):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO value_bets
            (event_id, league, home_team, away_team, start_time_local,
             bookmaker, market, outcome, price_decimal, model_prob,
             market_prob_devig, edge_pct, ev, kelly_stake, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (bet.event_id, bet.league, bet.home_team, bet.away_team,
              bet.start_time_local.isoformat(), bet.bookmaker,
              bet.market.value, bet.outcome.value, bet.price_decimal,
              bet.model_prob, bet.market_prob_devig, bet.edge_pct,
              bet.ev, bet.kelly_stake, datetime.now().isoformat()))
        self.conn.commit()
    
    def close(self):
        self.conn.close()


_db = None

def get_db():
    global _db
    if _db is None:
        _db = Database()
    return _db
