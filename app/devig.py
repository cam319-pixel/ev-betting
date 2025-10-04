import math
from app.config import get_config
from app.models import DeviggedOdds


class Devigger:
    def __init__(self):
        self.config = get_config()
        self.method = self.config.devig.method
    
    def devig_market(self, market_odds, provider):
        if provider not in market_odds.odds:
            return None
        outcomes = market_odds.odds[provider]
        raw_probs = {outcome: 1 / price for outcome, price in outcomes.items()}
        overround = sum(raw_probs.values())
        
        if self.method == "multiplicative":
            devigged = self._multiplicative(raw_probs, overround)
        else:
            devigged = self._multiplicative(raw_probs, overround)
        
        return DeviggedOdds(
            event_id=market_odds.event.event_id,
            provider=provider,
            market=market_odds.market,
            raw_probs=raw_probs,
            devigged_probs=devigged,
            overround=overround
        )
    
    def _multiplicative(self, raw_probs, overround):
        return {outcome: prob / overround for outcome, prob in raw_probs.items()}
