import numpy as np
import pandas as pd
from scipy.stats import poisson
from app.models import Outcome


class SoccerModel:
    def fit(self, df):
        raise NotImplementedError
    
    def predict_probs(self, home_team, away_team):
        raise NotImplementedError


class PoissonModel(SoccerModel):
    def __init__(self):
        self.home_attack = {}
        self.home_defense = {}
        self.away_attack = {}
        self.away_defense = {}
        self.avg_home_goals = 0.0
        self.avg_away_goals = 0.0
    
    def fit(self, df):
        self.avg_home_goals = df['home_score'].mean()
        self.avg_away_goals = df['away_score'].mean()
        
        teams = set(df['home_team']) | set(df['away_team'])
        for team in teams:
            home_games = df[df['home_team'] == team]
            away_games = df[df['away_team'] == team]
            
            self.home_attack[team] = home_games['home_score'].mean() / self.avg_home_goals if len(home_games) > 0 else 1.0
            self.home_defense[team] = home_games['away_score'].mean() / self.avg_away_goals if len(home_games) > 0 else 1.0
            self.away_attack[team] = away_games['away_score'].mean() / self.avg_away_goals if len(away_games) > 0 else 1.0
            self.away_defense[team] = away_games['home_score'].mean() / self.avg_home_goals if len(away_games) > 0 else 1.0
    
    def predict_probs(self, home_team, away_team):
        # Check if we have data for these teams
        if (home_team not in self.home_attack or 
            away_team not in self.away_attack or
            home_team not in self.away_defense or
            away_team not in self.home_defense):
            return None
    
        home_expected = (self.avg_home_goals * 
                        self.home_attack[home_team] * 
                        self.away_defense[away_team])
        away_expected = (self.avg_away_goals * 
                        self.away_attack[away_team] * 
                        self.home_defense[home_team])
    
        max_goals = 10
        prob_home = 0.0
        prob_draw = 0.0
        prob_away = 0.0
    
        for h in range(max_goals + 1):
            for a in range(max_goals + 1):
                prob = poisson.pmf(h, home_expected) * poisson.pmf(a, away_expected)
                if h > a:
                    prob_home += prob
                elif h == a:
                    prob_draw += prob
                else:
                    prob_away += prob
    
        if prob_home > 0.99 or prob_draw > 0.99 or prob_away > 0.99:
            return None
    
        return {Outcome.HOME: prob_home, Outcome.DRAW: prob_draw, Outcome.AWAY: prob_away}



class EloLogisticModel(SoccerModel):
    def __init__(self, k_factor=32.0):
        self.k_factor = k_factor
        self.ratings = {}
    
    def fit(self, df):
        df = df.sort_values('match_date')
        teams = set(df['home_team']) | set(df['away_team'])
        for team in teams:
            self.ratings[team] = 1500.0
        
        for _, row in df.iterrows():
            home_team = row['home_team']
            away_team = row['away_team']
            
            if row['home_score'] > row['away_score']:
                result = 1.0
            elif row['home_score'] < row['away_score']:
                result = 0.0
            else:
                result = 0.5
            
            rating_diff = self.ratings[home_team] - self.ratings[away_team] + 100
            expected = 1 / (1 + 10 ** (-rating_diff / 400))
            
            self.ratings[home_team] += self.k_factor * (result - expected)
            self.ratings[away_team] += self.k_factor * ((1 - result) - (1 - expected))
    
    def predict_probs(self, home_team, away_team):
        home_rating = self.ratings.get(home_team, 1500.0)
        away_rating = self.ratings.get(away_team, 1500.0)
        rating_diff = home_rating - away_rating + 100
        prob_home_or_draw = 1 / (1 + 10 ** (-rating_diff / 400))
        prob_draw = 0.25
        prob_home = (prob_home_or_draw - prob_draw / 2) * 1.1
        prob_away = 1 - prob_home - prob_draw
        prob_home = max(0.01, min(0.98, prob_home))
        prob_away = max(0.01, min(0.98, prob_away))
        prob_draw = 1 - prob_home - prob_away
        return {Outcome.HOME: prob_home, Outcome.DRAW: prob_draw, Outcome.AWAY: prob_away}
