import re
from datetime import datetime
from app.config import get_config
from app.models import Market, Outcome, RawOdds, Sport
from app.providers.base import OddsProvider


class TheOddsAPIProvider(OddsProvider):
    @property
    def name(self):
        return "theodds_api"
    
    def __init__(self):
        super().__init__()
        config = get_config()
        self.api_key = config.providers.the_odds_api_key
        self.base_url = config.providers.the_odds_api.base_url
    
    async def fetch_odds(self, sport, leagues=None):
        all_odds = []
        
        if not leagues:
            return all_odds
        
        for league in leagues:
            url = f"{self.base_url}/sports/{league}/odds"
            params = {
                "apiKey": self.api_key,
                "regions": "us,uk,eu",
                "markets": "h2h",
                "oddsFormat": "decimal"
            }
            
            try:
                response = await self.client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                odds = self._parse_response(data, sport, league)
                all_odds.extend(odds)
            except Exception as e:
                print(f"Error fetching {league}: {e}")
        
        return all_odds
    
    def _parse_response(self, data, sport, league):
        all_odds = []
        
        for event in data:
            event_id = self.generate_event_id(
                event["home_team"],
                event["away_team"],
                datetime.fromisoformat(event["commence_time"].replace("Z", "+00:00"))
            )
            
            start_time = datetime.fromisoformat(event["commence_time"].replace("Z", "+00:00"))
            
            for bookmaker in event.get("bookmakers", []):
                for market in bookmaker.get("markets", []):
                    if market["key"] != "h2h":
                        continue
                    
                    market_type = Market.MATCH_WINNER if sport == Sport.SOCCER else Market.MONEYLINE
                    
                    for outcome in market.get("outcomes", []):
                        outcome_name = outcome["name"]
                        price = outcome["price"]
                        
                        if outcome_name == event["home_team"]:
                            outcome_enum = Outcome.HOME
                        elif outcome_name == event["away_team"]:
                            outcome_enum = Outcome.AWAY
                        elif outcome_name.lower() == "draw":
                            outcome_enum = Outcome.DRAW
                        else:
                            continue
                        
                        odds = RawOdds(
                            provider=bookmaker["key"],
                            event_id=event_id,
                            sport=sport,
                            league=league,
                            home_team=self.normalize_team_name(event["home_team"]),
                            away_team=self.normalize_team_name(event["away_team"]),
                            start_time=start_time,
                            market=market_type,
                            outcome=outcome_enum,
                            price_decimal=price,
                            last_updated=datetime.now()
                        )
                        all_odds.append(odds)
        
        return all_odds
    
    def normalize_team_name(self, name):
        # Convert to lowercase and remove common variations
        normalized = name.lower()
    
        # Remove common words that vary
        normalized = normalized.replace(' fc', '')
        normalized = normalized.replace(' afc', '')
        normalized = normalized.replace(' united', '')
        normalized = normalized.replace(' city', '')
        normalized = normalized.replace('manchester', 'man')
        normalized = normalized.replace('tottenham', 'spurs')
    
        # Remove all non-alphanumeric except spaces
        normalized = ''.join(c for c in normalized if c.isalnum() or c.isspace())
    
        # Remove extra spaces
        normalized = ' '.join(normalized.split())
    
        return normalized
    
    def generate_event_id(self, home_team, away_team, start_time):
        home_norm = self.normalize_team_name(home_team)
        away_norm = self.normalize_team_name(away_team)
        date_str = start_time.strftime("%Y%m%d")
        return f"{home_norm}_{away_norm}_{date_str}"