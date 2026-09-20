from pathlib import Path
import joblib, numpy as np, pandas as pd
from sqlalchemy import select
from app.core.config import settings
from app.db.models import Match
from app.ml.features import build_features

class Predictor:
    def __init__(self): self.bundle=joblib.load(Path(settings.model_dir)/"latest.joblib")

    @staticmethod
    def _market_probabilities(odds):
        if not odds: return {}
        detail=odds.get("detail",odds)
        markets=[]
        def walk(v):
            if isinstance(v,dict):
                if isinstance(v.get("outcomes"),list): markets.append(v)
                for x in v.values(): walk(x)
            elif isinstance(v,list):
                for x in v: walk(x)
        walk(detail)
        result={}
        for market in markets:
            name=str(market.get("name") or market.get("market_name") or market.get("description") or "").casefold()
            outcomes=market.get("outcomes") or []
            parsed=[]
            for o in outcomes:
                if not isinstance(o,dict): continue
                label=str(o.get("description") or o.get("name") or o.get("label") or "").strip().casefold()
                p=o.get("probability")
                odd=o.get("odds") or o.get("odd") or o.get("price")
                try: p=float(p) if p is not None else None
                except (TypeError,ValueError): p=None
                try: odd=float(odd) if odd is not None else None
                except (TypeError,ValueError): odd=None
                if p is None and odd and odd>1: p=1/odd
                if p is not None and p>1: p=p/100
                if p is not None: parsed.append((label,max(0,min(1,p)),odd))
            if not parsed: continue
            if any(x in name for x in ("1x2","match result","full time result","3 way","three way")):
                for label,p,odd in parsed:
                    if label in {"home","home win","1"}: result["home_probability"]=p; result["home_odds"]=odd
                    elif label in {"draw","x"}: result["draw_probability"]=p; result["draw_odds"]=odd
                    elif label in {"away","away win","2"}: result["away_probability"]=p; result["away_odds"]=odd
            elif "double chance" in name:
                for label,p,odd in parsed:
                    if "1x" in label or "home or draw" in label: result["dc_home_draw_probability"]=p; result["dc_home_draw_odds"]=odd
                    elif "x2" in label or "away or draw" in label: result["dc_away_draw_probability"]=p; result["dc_away_draw_odds"]=odd
            elif "over/under" in name or "over under" in name or "total goals" in name:
                for label,p,odd in parsed:
                    if "over 2.5" in label: result["over_2_5_probability"]=p; result["over_2_5_odds"]=odd
                    elif "under 2.5" in label: result["under_2_5_probability"]=p; result["under_2_5_odds"]=odd
            elif "corner" in name:
                for label,p,odd in parsed:
                    if "over 9.5" in label: result["over_9_5_corners_probability"]=p; result["over_9_5_corners_odds"]=odd
                    elif "under 9.5" in label: result["under_9_5_corners_probability"]=p; result["under_9_5_corners_odds"]=odd
        return result

    def predict(self, db, match: Match, msport_odds=None):
        rows=db.execute(select(Match).where(Match.kickoff < match.kickoff, Match.home_goals.is_not(None))).scalars().all()
        hist=pd.DataFrame([{c:getattr(r,c) for c in ["home_team","away_team","kickoff","home_goals","away_goals","home_corners","away_corners","home_xg","away_xg"]} for r in rows])
        f=build_features(hist,match.home_team,match.away_team,match.kickoff); X=np.asarray([[f[k] for k in self.bundle["features"]]])
        wp=self.bundle["winner"].predict_proba(X)[0]
        market=self._market_probabilities(msport_odds)
        market_wp=np.array([market.get("home_probability",np.nan),market.get("draw_probability",np.nan),market.get("away_probability",np.nan)],float)
        if np.isfinite(market_wp).all():
            s=market_wp.sum()
            if s>0: wp=.70*wp+.30*(market_wp/s)
        wi=int(np.argmax(wp)); labels=["Home Win","Draw","Away Win"]
        double_home_draw=float(wp[0]+wp[1]); double_away_draw=float(wp[1]+wp[2]); dc="Home Or Draw" if double_home_draw>=double_away_draw else "Away Or Draw"; dc_conf=max(double_home_draw,double_away_draw)
        gp=float(self.bundle["goals"].predict_proba(X)[0,1])
        if market.get("over_2_5_probability") is not None and market.get("under_2_5_probability") is not None:
            mp=float(market["over_2_5_probability"]); gp=.70*gp+.30*mp
        corner=float(max(0,self.bundle["corners"].predict(X)[0]))
        return {"winner":{"outcome":labels[wi],"probability":float(wp[wi]),"double_chance":dc,"double_chance_probability":dc_conf},"goals":{"over_2_5_probability":gp,"under_2_5_probability":1-gp},"corners":{"projection":corner},"features":f,"model_version":self.bundle["version"],"msport_odds":market}
