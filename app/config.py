import tomllib
from pathlib import Path
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class GeneralConfig(BaseModel):
    timezone: str = "America/New_York"
    cache_dir: str = "data/cache"
    results_dir: str = "data/results"


class FilterConfig(BaseModel):
    min_hours_ahead: int = 24
    max_hours_ahead: int = 48
    min_edge_pct: float = 4.0
    min_ev: float = 0.0


class BettingConfig(BaseModel):
    bankroll: float = 10000.0
    kelly_cap: float = 0.25
    kelly_fraction: float = 0.5


class LeaguesConfig(BaseModel):
    soccer: list[str] = Field(default_factory=list)
    basketball: list[str] = Field(default_factory=list)
    football: list[str] = Field(default_factory=list)


class ProviderSettings(BaseModel):
    enabled: bool = True
    base_url: str = ""


class ProvidersConfig(BaseModel):
    the_odds_api_key: str = ""
    refresh_interval_seconds: int = 300
    request_timeout_seconds: int = 10
    max_retries: int = 3
    the_odds_api: ProviderSettings = Field(default_factory=ProviderSettings)


class ModelingConfig(BaseModel):
    soccer_models: list[str] = Field(default_factory=list)
    cv_folds: int = 5
    min_historical_games: int = 100
    model_cache_days: int = 7


class DevigConfig(BaseModel):
    method: str = "multiplicative"


class Config(BaseSettings):
    general: GeneralConfig = Field(default_factory=GeneralConfig)
    filters: FilterConfig = Field(default_factory=FilterConfig)
    betting: BettingConfig = Field(default_factory=BettingConfig)
    leagues: LeaguesConfig = Field(default_factory=LeaguesConfig)
    providers: ProvidersConfig = Field(default_factory=ProvidersConfig)
    modeling: ModelingConfig = Field(default_factory=ModelingConfig)
    devig: DevigConfig = Field(default_factory=DevigConfig)

    @classmethod
    def load(cls, config_path: str = "config.toml"):
        path = Path(config_path)
        if not path.exists():
            return cls()
        with open(path, "rb") as f:
            data = tomllib.load(f)
        return cls(**data)


_config = None

def get_config():
    global _config
    if _config is None:
        _config = Config.load()
    return _config
