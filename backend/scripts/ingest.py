import asyncio
from datetime import datetime,timezone
from app.db.session import SessionLocal,init_db
from app.db.models import Match
from app.services.provider import ApiFootballProvider
async def main():
    init_db(); provider=ApiFootballProvider(); today=datetime.now(timezone.utc).date().isoformat(); data=await provider.fixtures(today); db=SessionLocal()
    try:
        for x in data:
            f=x["fixture"]; teams=x["teams"]; league=x["league"]; goals=x.get("goals",{})
            m=db.query(Match).filter_by(external_id=f["id"]).first() or Match(external_id=f["id"])
            m.league_id=league["id"]; m.league_name=league["name"]; m.season=league["season"]; m.kickoff=datetime.fromtimestamp(f["timestamp"],tz=timezone.utc); m.home_team=teams["home"]["name"]; m.away_team=teams["away"]["name"]; m.home_logo=teams["home"].get("logo"); m.away_logo=teams["away"].get("logo"); m.home_goals=goals.get("home"); m.away_goals=goals.get("away"); m.raw=x; db.add(m)
        db.commit(); print(f"ingested {len(data)} fixtures")
    finally:db.close()
if __name__=="__main__":asyncio.run(main())
