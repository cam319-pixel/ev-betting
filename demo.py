#!/usr/bin/env python3
'''Demo script with synthetic data'''

from datetime import datetime, timedelta
import random
import pytz
from app.config import get_config
from app.database import get_db
from app.models import HistoricalResult, Sport, Market, Outcome, RawOdds
from app.modeling.soccer import PoissonModel
from app.providers.manager import ProviderManager
from app.devig import Devigger


def create_demo_data():
    print("Creating demo historical data...")
    db = get_db()
    teams = ["arsenal", "chelsea", "liverpool", "manchester united"]
    
    for i in range(50):
        home = random.choice(teams)
        away = random.choice([t for t in teams if t != home])
        result = HistoricalResult(
            event_id=f"hist_{i}",
            sport=Sport.SOCCER,
            league="EPL",
            home_team=home,
            away_team=away,
            match_date=datetime(2025, 1, 1) + timedelta(days=i),
            home_score=random.randint(0, 3),
            away_score=random.randint(0, 2)
        )
        db.save_historical_result(result)
    print(f"Created 50 historical matches")


def run_demo():
    print("=" * 60)
    print("EV BETTING SCANNER - DEMO MODE")
    print("=" * 60)
    
    create_demo_data()
    
    print("\nTraining model...")
    db = get_db()
    df = db.get_historical_results(sport="soccer", league="EPL")
    model = PoissonModel()
    model.fit(df)
    print(f"Model trained on {len(df)} matches")
    
    tz = pytz.timezone("America/New_York")
    now = datetime.now(tz)
    match_time = now + timedelta(hours=36)
    
    odds_list = [
        RawOdds(
            provider="demo_book",
            event_id="demo_001",
            sport=Sport.SOCCER,
            league="EPL",
            home_team="arsenal",
            away_team="chelsea",
            start_time=match_time,
            market=Market.MATCH_WINNER,
            outcome=Outcome.HOME,
            price_decimal=2.15,
            last_updated=now
        ),
        RawOdds(
            provider="demo_book",
            event_id="demo_001",
            sport=Sport.SOCCER,
            league="EPL",
            home_team="arsenal",
            away_team="chelsea",
            start_time=match_time,
            market=Market.MATCH_WINNER,
            outcome=Outcome.DRAW,
            price_decimal=3.40,
            last_updated=now
        ),
        RawOdds(
            provider="demo_book",
            event_id="demo_001",
            sport=Sport.SOCCER,
            league="EPL",
            home_team="arsenal",
            away_team="chelsea",
            start_time=match_time,
            market=Market.MATCH_WINNER,
            outcome=Outcome.AWAY,
            price_decimal=3.75,
            last_updated=now
        ),
    ]
    
    print("\nAnalyzing for value bets...")
    manager = ProviderManager()
    market_odds_list = manager.aggregate_odds(odds_list)
    devigger = Devigger()
    
    for market_odds in market_odds_list:
        event = market_odds.event
        model_probs = model.predict_probs(event.home_team, event.away_team)
        
        for outcome in [Outcome.HOME, Outcome.DRAW, Outcome.AWAY]:
            if outcome not in model_probs:
                continue
            
            model_prob = model_probs[outcome]
            best = manager.get_best_odds(market_odds, outcome)
            if not best:
                continue
            
            best_provider, best_price = best
            devigged = devigger.devig_market(market_odds, best_provider)
            if not devigged:
                continue
            
            market_prob = devigged.devigged_probs[outcome]
            edge_pct = ((model_prob - market_prob) / market_prob) * 100
            ev = (model_prob * best_price) - 1
            
            if edge_pct >= 4.0 and ev > 0:
                print(f"\n{'=' * 60}")
                print("VALUE BET FOUND!")
                print(f"{'=' * 60}")
                print(f"Match: {event.home_team.title()} vs {event.away_team.title()}")
                print(f"Bet: {outcome.value.upper()} @ {best_price:.2f}")
                print(f"Model probability: {model_prob:.1%}")
                print(f"Market probability: {market_prob:.1%}")
                print(f"Edge: {edge_pct:.2f}%")
                print(f"Expected Value: {ev:.1%}")
                print(f"{'=' * 60}")
    
    print("\nDemo complete!")
    print("To run with real data:")
    print("1. Add API keys to config.toml")
    print("2. Run: evbet scan")


if __name__ == "__main__":
    run_demo()
