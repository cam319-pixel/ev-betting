import pickle
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from app.config import get_config
from app.database import get_db
from app.models import Sport
from app.modeling.soccer import PoissonModel, EloLogisticModel


class ModelSelector:
    def __init__(self):
        self.config = get_config()
        self.db = get_db()
        self.model_cache_dir = Path(self.config.general.cache_dir) / "models"
        self.model_cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_model_for_sport(self, sport, league=None):
        cache_file = self.model_cache_dir / f"{sport.value}_best.pkl"
        if cache_file.exists():
            cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if cache_age < timedelta(days=self.config.modeling.model_cache_days):
                with open(cache_file, "rb") as f:
                    return pickle.load(f)
        
        # Get historical results
        df = self.db.get_historical_results(sport=sport.value, league=league)
        
        # FILTER TO ONLY RECENT DATA (last 2 years)
        if len(df) > 0 and 'match_date' in df.columns:
            df['match_date'] = pd.to_datetime(df['match_date'], format='mixed', utc=True)
            cutoff_date = pd.Timestamp(datetime.now() - timedelta(days=730), tz='UTC')  # Make it timezone-aware
            df = df[df['match_date'] >= cutoff_date]
            print(f"  Training on {len(df)} games from last 2 years (filtered from older data)")
        
        if len(df) < self.config.modeling.min_historical_games:
            model = PoissonModel()
        else:
            model = PoissonModel()
        
        if len(df) > 0:
            model.fit(df)
        
        with open(cache_file, "wb") as f:
            pickle.dump(model, f)
        
        return model