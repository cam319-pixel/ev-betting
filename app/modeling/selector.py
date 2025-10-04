import pickle
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
        
        df = self.db.get_historical_results(sport=sport.value, league=league)
        
        if len(df) < self.config.modeling.min_historical_games:
            model = PoissonModel()
        else:
            model = PoissonModel()
        
        if len(df) > 0:
            model.fit(df)
        
        with open(cache_file, "wb") as f:
            pickle.dump(model, f)
        
        return model
