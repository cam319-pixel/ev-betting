import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import pytz
from app.config import get_config
from app.database import get_db
from app.devig import Devigger
from app.models import Outcome, Sport, ValueBet
from app.modeling.selector import ModelSelector
from app.providers.manager import ProviderManager


class ValueBetScanner:
    def __init__(self):
        self.config = get_config()
        self.db = get_db()
        self.provider_manager = ProviderManager()
        self.model_selector = ModelSelector()
        self.devigger = Devigger()
    
    async def scan(self):
        value_bets = []
        tz = pytz.timezone(self.config.general.timezone)
        now = datetime.now(tz)
        min_start = now + timedelta(hours=self.config.filters.min_hours_ahead)
        max_start = now + timedelta(hours=self.config.filters.max_hours_ahead)
        
        sports = [Sport.SOCCER, Sport.BASKETBALL, Sport.FOOTBALL]
        
        for sport in sports:
            leagues = self.config.leagues.soccer
            if not leagues:
                continue
            
            print(f"\nScanning {sport.value}...")
            raw_odds = await self.provider_manager.fetch_all_odds(sport, leagues)
            
            if not raw_odds:
                print("No odds found")
                continue
            
            market_odds_list = self.provider_manager.aggregate_odds(raw_odds)
            model = self.model_selector.get_model_for_sport(sport)
            
            for market_odds in market_odds_list:
                event = market_odds.event
                try:
                    model_probs = model.predict_probs(event.home_team, event.away_team)
                    if model_probs is None:
                        continue
                except:
                    continue
                
                for outcome in [Outcome.HOME, Outcome.DRAW, Outcome.AWAY]:
                    if outcome not in model_probs:
                        continue
                    
                    model_prob = model_probs[outcome]
                    best = self.provider_manager.get_best_odds(market_odds, outcome)
                    if not best:
                        continue
                    
                    best_provider, best_price = best
                    devigged = self.devigger.devig_market(market_odds, best_provider)
                    if not devigged or outcome not in devigged.devigged_probs:
                        continue
                    
                    market_prob = devigged.devigged_probs[outcome]
                    edge = model_prob - market_prob
                    edge_pct = (edge / market_prob) * 100 if market_prob > 0 else 0
                    ev = (model_prob * best_price) - 1
                    
                    if edge_pct < self.config.filters.min_edge_pct or ev <= self.config.filters.min_ev:
                        continue
                    
                    kelly = self._calculate_kelly_stake(model_prob, best_price)
                    
                    value_bet = ValueBet(
                        event_id=event.event_id,
                        league=event.league,
                        home_team=event.home_team,
                        away_team=event.away_team,
                        start_time_local=event.start_time.astimezone(tz),
                        bookmaker=best_provider,
                        market=market_odds.market,
                        outcome=outcome,
                        price_decimal=best_price,
                        model_prob=model_prob,
                        market_prob_devig=market_prob,
                        edge_pct=edge_pct,
                        ev=ev,
                        kelly_stake=kelly
                    )
                    
                    value_bets.append(value_bet)
                    self.db.save_value_bet(value_bet)
        
        value_bets.sort(key=lambda x: (x.ev, x.edge_pct), reverse=True)
        return value_bets
    
    def _calculate_kelly_stake(self, true_prob, odds):
        b = odds - 1
        p = true_prob
        q = 1 - p
        if b <= 0 or p <= 0:
            return 0.0
        kelly_fraction = (b * p - q) / b
        kelly_fraction *= self.config.betting.kelly_fraction
        kelly_fraction = min(kelly_fraction, self.config.betting.kelly_cap)
        kelly_fraction = max(kelly_fraction, 0.0)
        stake = self.config.betting.bankroll * kelly_fraction
        return round(stake, 2)
    
    def export_to_csv(self, value_bets, filename="value_bets.csv"):
        if not value_bets:
            return
        data = []
        for bet in value_bets:
            data.append({
                "event_id": bet.event_id,
                "league": bet.league,
                "start_time_local": bet.start_time_local.strftime("%Y-%m-%d %H:%M"),
                "home_team": bet.home_team,
                "away_team": bet.away_team,
                "bookmaker": bet.bookmaker,
                "market": bet.market.value,
                "outcome": bet.outcome.value,
                "price_decimal": f"{bet.price_decimal:.2f}",
                "model_prob": f"{bet.model_prob:.4f}",
                "market_prob_devig": f"{bet.market_prob_devig:.4f}",
                "edge_pct": f"{bet.edge_pct:.2f}",
                "ev": f"{bet.ev:.4f}",
                "kelly_stake": f"{bet.kelly_stake:.2f}"
            })
        df = pd.DataFrame(data)
        results_dir = self.config.general.results_dir
        Path(results_dir).mkdir(parents=True, exist_ok=True)
        output_path = Path(results_dir) / filename
        df.to_csv(output_path, index=False)
        print(f"\nExported {len(value_bets)} value bets to {output_path}")
    
    async def close(self):
        await self.provider_manager.close_all()
