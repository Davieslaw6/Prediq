from pathlib import Path
from datetime import datetime, timezone
import joblib
import pandas as pd
import numpy as np
from sqlalchemy import select
from sklearn.metrics import accuracy_score, mean_absolute_error
from xgboost import XGBClassifier, XGBRegressor
from app.core.config import settings
from app.db.session import SessionLocal
from app.db.models import Match, ModelRun
from app.ml.features import FEATURES, build_features

def train():
    db = SessionLocal()
    try:
        rows = db.execute(select(Match).where(Match.home_goals.is_not(None), Match.away_goals.is_not(None)).order_by(Match.kickoff)).scalars().all()
        if len(rows) < 30: raise RuntimeError("Need at least 30 completed matches before training")
        data = pd.DataFrame([{c:getattr(r,c) for c in ["home_team","away_team","kickoff","home_goals","away_goals","home_corners","away_corners","home_xg","away_xg"]} for r in rows])
        X=[]; y_w=[]; y_goals=[]; corner_X=[]; y_corners=[]
        for i,r in data.iterrows():
            past=data.iloc[:i]; f=build_features(past,r.home_team,r.away_team,r.kickoff)
            X.append([f[k] for k in FEATURES]); y_w.append(0 if r.home_goals>r.away_goals else 1 if r.home_goals==r.away_goals else 2); y_goals.append(int(r.home_goals+r.away_goals>=3))
            if pd.notna(r.home_corners) and pd.notna(r.away_corners): corner_X.append([f[k] for k in FEATURES]); y_corners.append(float(r.home_corners+r.away_corners))
        X=np.asarray(X,float); y_w=np.asarray(y_w,int); y_goals=np.asarray(y_goals,int); corner_X=np.asarray(corner_X,float); y_corners=np.asarray(y_corners,float)
        if len(np.unique(y_w))<3: raise RuntimeError("Winner model needs historical examples of home wins, draws and away wins")
        if len(np.unique(y_goals))<2: raise RuntimeError("Goals model needs both Over and Under 2.5 historical examples")
        if len(y_corners)<20: raise RuntimeError("Need at least 20 completed matches with corner statistics")
        models_dir=Path(settings.model_dir); models_dir.mkdir(parents=True,exist_ok=True); version=datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        winner=XGBClassifier(n_estimators=300,max_depth=4,learning_rate=.04,subsample=.85,colsample_bytree=.85,objective="multi:softprob",num_class=3,eval_metric="mlogloss",random_state=42)
        goals=XGBClassifier(n_estimators=250,max_depth=3,learning_rate=.05,subsample=.9,objective="binary:logistic",eval_metric="logloss",random_state=42)
        corners=XGBRegressor(n_estimators=300,max_depth=4,learning_rate=.04,subsample=.9,objective="reg:squarederror",random_state=42)
        winner.fit(X,y_w); goals.fit(X,y_goals); corners.fit(corner_X,y_corners)
        bundle={"version":version,"features":FEATURES,"winner":winner,"goals":goals,"corners":corners}; joblib.dump(bundle,models_dir/f"models_{version}.joblib"); joblib.dump(bundle,models_dir/"latest.joblib")
        metrics={"winner_accuracy_train":float(accuracy_score(y_w,winner.predict(X))),"goals_accuracy_train":float(accuracy_score(y_goals,goals.predict(X))),"corners_mae_train":float(mean_absolute_error(y_corners,corners.predict(corner_X)))}
        db.add(ModelRun(version=version,rows=len(X),metrics=metrics,successful=True)); db.commit(); return {"version":version,"rows":len(X),"metrics":metrics}
    except Exception:
        db.rollback(); raise
    finally: db.close()
