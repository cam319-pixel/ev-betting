from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Sport(str, Enum):
    SOCCER = "soccer"
    BASKETBALL = "basketball"
    FOOTBALL = "football"


class Market(str, Enum):
    MATCH_WINNER = "match_winner"
    MONEYLINE = "moneyline"


class Outcome(str, Enum):
    HOME = "home"
    DRAW = "draw"
    AWAY = "away"


class RawOdds(BaseModel):
    provider: str
    event_id: str
    sport: Sport
    league: str
    home_team: str
    away_team: str
    start_time: datetime
    market: Market
    outcome: Outcome
    price_decimal: float
    last_updated: datetime
    class Config:
        frozen = True


class NormalizedEvent(BaseModel):
    event_id: str
    sport: Sport
    league: str
    home_team: str
    away_team: str
    start_time: datetime
    class Config:
        frozen = True


class MarketOdds(BaseModel):
    event: NormalizedEvent
    market: Market
    odds: dict[str, dict[Outcome, float]]
    last_updated: datetime


class DeviggedOdds(BaseModel):
    event_id: str
    provider: str
    market: Market
    raw_probs: dict[Outcome, float]
    devigged_probs: dict[Outcome, float]
    overround: float


class ValueBet(BaseModel):
    event_id: str
    league: str
    home_team: str
    away_team: str
    start_time_local: datetime
    bookmaker: str
    market: Market
    outcome: Outcome
    price_decimal: float
    model_prob: float
    market_prob_devig: float
    edge_pct: float
    ev: float
    kelly_stake: float
    class Config:
        frozen = True


class HistoricalResult(BaseModel):
    event_id: str
    sport: Sport
    league: str
    home_team: str
    away_team: str
    match_date: datetime
    home_score: int
    away_score: int
    home_odds: Optional[float] = None
    draw_odds: Optional[float] = None
    away_odds: Optional[float] = None


class ModelPerformance(BaseModel):
    model_name: str
    sport: Sport
    log_loss: float
    brier_score: float
    accuracy: float
    calibration_error: float
    num_predictions: int
    evaluated_at: datetime
