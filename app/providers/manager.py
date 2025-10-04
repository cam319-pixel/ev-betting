import asyncio
from collections import defaultdict
from datetime import datetime
from app.models import MarketOdds, NormalizedEvent
from app.providers.theodds_api import TheOddsAPIProvider


class ProviderManager:
    def __init__(self):
        self.providers = [TheOddsAPIProvider()]
    
    async def fetch_all_odds(self, sport, leagues=None):
        tasks = [provider.fetch_odds(sport, leagues) for provider in self.providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_odds = []
        for result in results:
            if isinstance(result, Exception):
                print(f"Provider error: {result}")
                continue
            all_odds.extend(result)
        return all_odds
    
    def aggregate_odds(self, raw_odds):
        event_groups = defaultdict(list)
        for odds in raw_odds:
            event_groups[odds.event_id].append(odds)
        
        aggregated = []
        for event_id, odds_list in event_groups.items():
            first = odds_list[0]
            event = NormalizedEvent(
                event_id=event_id,
                sport=first.sport,
                league=first.league,
                home_team=first.home_team,
                away_team=first.away_team,
                start_time=first.start_time
            )
            market_groups = defaultdict(lambda: defaultdict(dict))
            for odds in odds_list:
                market_groups[odds.market][odds.provider][odds.outcome] = odds.price_decimal
            
            for market, provider_odds in market_groups.items():
                market_odds = MarketOdds(
                    event=event,
                    market=market,
                    odds=dict(provider_odds),
                    last_updated=datetime.now()
                )
                aggregated.append(market_odds)
        return aggregated
    
    def get_best_odds(self, market_odds, outcome):
        best_price = 0.0
        best_provider = ""
        for provider, outcomes in market_odds.odds.items():
            if outcome in outcomes:
                price = outcomes[outcome]
                if price > best_price:
                    best_price = price
                    best_provider = provider
        if best_price > 0:
            return (best_provider, best_price)
        return None
    
    async def close_all(self):
        for provider in self.providers:
            await provider.close()