from pathlib import Path
import joblib, numpy as np, pandas as pd
from sqlalchemy import select
from app.core.config import settings
from app.db.models import Match
from app.ml.features import build_features

class Predictor:
    def __init__(self): self.bundle=joblib.load(Path(settings.model_dir)/"latest.joblib")
    def predict(self, db, match: Match):
        rows=db.execute(select(Match).where(Match.kickoff < match.kickoff, Match.home_goals.is_not(None))).scalars().all()
        hist=pd.DataFrame([{c:getattr(r,c) for c in ["home_team","away_team","kickoff","home_goals","away_goals","home_corners","away_corners","home_xg","away_xg"]} for r in rows])
        f=build_features(hist,match.home_team,match.away_team,match.kickoff); X=np.asarray([[f[k] for k in self.bundle["features"]]])
        wp=self.bundle["winner"].predict_proba(X)[0]; wi=int(np.argmax(wp)); labels=["Home Win","Draw","Away Win"]
        double_home_draw=float(wp[0]+wp[1]); double_away_draw=float(wp[1]+wp[2]); dc="Home Or Draw" if double_home_draw>=double_away_draw else "Away Or Draw"; dc_conf=max(double_home_draw,double_away_draw)
        gp=float(self.bundle["goals"].predict_proba(X)[0,1]); corner=float(max(0,self.bundle["corners"].predict(X)[0]))
        return {"winner":{"outcome":labels[wi],"probability":float(wp[wi]),"double_chance":dc,"double_chance_probability":dc_conf},"goals":{"over_2_5_probability":gp,"under_2_5_probability":1-gp},"corners":{"projection":corner},"features":f,"model_version":self.bundle["version"]}
