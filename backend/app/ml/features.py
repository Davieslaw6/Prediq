import pandas as pd
import numpy as np

FEATURES = [
    "home_form5", "away_form5", "home_gf5", "away_gf5", "home_ga5", "away_ga5",
    "home_gf_home", "away_gf_away", "home_ga_home", "away_ga_away",
    "home_corners", "away_corners", "home_xg", "away_xg"
]

def build_features(history: pd.DataFrame, home: str, away: str, kickoff=None):
    h = history[history.home_team.eq(home) | history.away_team.eq(home)].sort_values("kickoff").tail(20)
    a = history[history.home_team.eq(away) | history.away_team.eq(away)].sort_values("kickoff").tail(20)
    def stats(df, team):
        rows=[]
        for _,r in df.iterrows():
            is_home=r.home_team==team
            gf=r.home_goals if is_home else r.away_goals
            ga=r.away_goals if is_home else r.home_goals
            corners=r.home_corners if is_home else r.away_corners
            xg=r.home_xg if is_home else r.away_xg
            result=3 if gf>ga else 1 if gf==ga else 0
            rows.append((gf,ga,corners,xg,result,is_home))
        return rows
    hs, as_ = stats(h, home), stats(a, away)
    def avg(vals, i, n=5):
        x=[v[i] for v in vals[-n:] if v[i] is not None]
        return float(np.mean(x)) if x else 0.0
    return {
        "home_form5": avg(hs,4), "away_form5": avg(as_,4),
        "home_gf5": avg(hs,0), "away_gf5": avg(as_,0),
        "home_ga5": avg(hs,1), "away_ga5": avg(as_,1),
        "home_gf_home": avg([x for x in hs if x[5]],0), "away_gf_away": avg([x for x in as_ if not x[5]],0),
        "home_ga_home": avg([x for x in hs if x[5]],1), "away_ga_away": avg([x for x in as_ if not x[5]],1),
        "home_corners": avg(hs,2), "away_corners": avg(as_,2),
        "home_xg": avg(hs,3), "away_xg": avg(as_,3),
    }
