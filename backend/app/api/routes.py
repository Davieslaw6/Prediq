from datetime import datetime,timezone
from fastapi import APIRouter,Depends,Header,HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.session import get_db
from app.db.models import Match,PredictionLog
from app.services.predictor import Predictor
from app.services.insights import risk,pct,winner_insight,goals_insight,corners_insight
from app.core.config import settings

router=APIRouter(prefix="/api")
@router.get("/matches/upcoming")
async def upcoming(db:Session=Depends(get_db)):
    now=datetime.now(timezone.utc); rows=db.execute(select(Match).where(Match.kickoff>=now).order_by(Match.kickoff).limit(50)).scalars().all()
    return [{"id":m.id,"external_id":m.external_id,"league":m.league_name,"home":m.home_team,"away":m.away_team,"home_logo":m.home_logo,"away_logo":m.away_logo,"kickoff":m.kickoff.isoformat()} for m in rows]
@router.get("/predictions/{match_id}")
def prediction(match_id:int,db:Session=Depends(get_db)):
    m=db.get(Match,match_id)
    if not m: raise HTTPException(404,"Match not found")
    try:p=Predictor().predict(db,m)
    except FileNotFoundError:raise HTTPException(503,"No trained model. Run the training pipeline first.")
    w=p["winner"]; g=p["goals"]; c=p["corners"]; f=p["features"]
    payload={"match":{"id":m.id,"home":m.home_team,"away":m.away_team,"home_logo":m.home_logo,"away_logo":m.away_logo,"league":m.league_name,"kickoff":m.kickoff.isoformat()},"winner":{"outcome":w["outcome"],"double_chance":w["double_chance"],"confidence":pct(w["double_chance_probability"]),"risk":risk(w["double_chance_probability"]),"insight":winner_insight(m.home_team,m.away_team,f,w)},"over_under":{"outcome":"Over 2.5 Goals" if g["over_2_5_probability"]>=.5 else "Under 2.5 Goals","confidence":pct(max(g["over_2_5_probability"],g["under_2_5_probability"])),"risk":risk(max(g["over_2_5_probability"],g["under_2_5_probability"])),"insight":goals_insight(m.home_team,m.away_team,f,g)},"corners":{"outcome":f"Over 9.5 Corners" if c["projection"]>=9.5 else "Under 9.5 Corners","confidence":pct(min(.99,.55+abs(c["projection"]-9.5)*.04)),"risk":risk(min(.99,.55+abs(c["projection"]-9.5)*.04)),"projection":round(c["projection"],1),"insight":corners_insight(m.home_team,m.away_team,f,c)},"model_version":p["model_version"]}
    db.add(PredictionLog(match_id=m.id,model_version=p["model_version"],payload=payload)); db.commit(); return payload
@router.post("/admin/retrain")
def retrain(authorization:str|None=Header(default=None)):
    if authorization!=f"Bearer {settings.admin_token}":raise HTTPException(401,"Invalid admin token")
    from app.ml.train import train
    return train()
