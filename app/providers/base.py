from abc import ABC, abstractmethod
from datetime import datetime
import httpx
from app.models import RawOdds, Sport


class OddsProvider(ABC):
    def __init__(self, timeout=10, max_retries=3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = httpx.AsyncClient(timeout=timeout)
    
    @property
    @abstractmethod
    def name(self):
        pass
    
    @abstractmethod
    async def fetch_odds(self, sport, leagues=None):
        pass
    
    @abstractmethod
    def normalize_team_name(self, name):
        pass
    
    @abstractmethod
    def generate_event_id(self, home_team, away_team, start_time):
        pass
    
    async def close(self):
        await self.client.aclose()
