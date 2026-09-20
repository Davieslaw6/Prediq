import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from app.ml.train import train
from app.db.session import SessionLocal, init_db
from app.db.models import Match
from app.services.provider import ApiFootballProvider
from datetime import datetime, timezone, timedelta

def _ingest_recent_results():
    async def run():
        provider=ApiFootballProvider(); db=SessionLocal()
        try:
            for offset in range(3):
                day=(datetime.now(timezone.utc).date()-timedelta(days=offset)).isoformat()
                for item in await provider.fixtures(day):
                    fixture=item["fixture"]; teams=item["teams"]; league=item["league"]; goals=item.get("goals") or {}; stats=item.get("statistics") or []
                    def team_stat(team_name,key):
                        for block in stats:
                            if block.get("team",{}).get("name")==team_name:
                                for stat in block.get("statistics",[]):
                                    if stat.get("type")==key:return stat.get("value")
                        return None
                    def num(v):
                        try:return float(v) if v is not None else None
                        except (TypeError,ValueError):return None
                    m=db.query(Match).filter_by(external_id=fixture["id"]).first() or Match(external_id=fixture["id"])
                    m.league_id=league["id"]; m.league_name=league["name"]; m.season=league["season"]; m.kickoff=datetime.fromtimestamp(fixture["timestamp"],tz=timezone.utc)
                    m.home_team=teams["home"]["name"]; m.away_team=teams["away"]["name"]; m.home_logo=teams["home"].get("logo"); m.away_logo=teams["away"].get("logo")
                    m.home_goals=goals.get("home"); m.away_goals=goals.get("away"); m.home_corners=num(team_stat(m.home_team,"Corner Kicks")); m.away_corners=num(team_stat(m.away_team,"Corner Kicks"))
                    m.home_xg=num(team_stat(m.home_team,"expected_goals")); m.away_xg=num(team_stat(m.away_team,"expected_goals")); m.raw=item; db.add(m)
            db.commit()
        finally: db.close()
    asyncio.run(run())

def scheduled_retrain():
    try:return _ingest_recent_results() or train()
    except Exception as exc: print(f"Scheduled training failed: {exc}"); return None

def start_scheduler():
    init_db(); s=BackgroundScheduler(timezone="UTC"); s.add_job(scheduled_retrain,"cron",day_of_week="mon,thu",hour=5,minute=0,id="model_retrain",replace_existing=True,max_instances=1); s.start(); return s
