import httpx
from datetime import datetime, timezone
from app.core.config import settings

class ApiFootballProvider:
    def __init__(self):
        self.headers={"x-apisports-key":settings.api_football_key}; self.base=settings.api_football_base_url.rstrip("/")
    async def _get(self,path,params):
        if not settings.api_football_key: raise RuntimeError("API_FOOTBALL_KEY is not configured")
        async with httpx.AsyncClient(timeout=30) as c:
            r=await c.get(f"{self.base}/{path.lstrip('/')}",headers=self.headers,params=params); r.raise_for_status(); return r.json().get("response",[])
    async def fixtures(self,date:str):
        out=[]
        for league in settings.leagues: out.extend(await self._get("fixtures",{"date":date,"league":league}))
        return out
    async def results(self,league:int,season:int): return await self._get("fixtures",{"league":league,"season":season,"status":"FT"})

class MSportProvider:
    """Adapter for an MSport odds API exposing get_matches/get_match_odds.

    MSport does not appear to publish a single official public developer API, so the
    base URL and endpoint paths are configurable rather than hard-coded.
    """
    def __init__(self):
        self.base=settings.msport_api_base_url.rstrip("/")
        self.headers={"X-API-Key":settings.msport_api_key,"Accept":"application/json"}

    def _check(self):
        if not settings.msport_enabled:
            raise RuntimeError("MSport integration is disabled")
        if not settings.msport_api_key:
            raise RuntimeError("MSPORT_API_KEY is not configured")
        if not self.base:
            raise RuntimeError("MSPORT_API_BASE_URL is not configured")

    async def _get(self,path,params=None):
        self._check()
        async with httpx.AsyncClient(timeout=20) as c:
            r=await c.get(f"{self.base}/{path.lstrip('/')}",headers=self.headers,params=params or {})
            r.raise_for_status()
            return r.json()

    @staticmethod
    def _walk(value):
        if isinstance(value,dict):
            yield value
            for v in value.values(): yield from MSportProvider._walk(v)
        elif isinstance(value,list):
            for v in value: yield from MSportProvider._walk(v)

    @staticmethod
    def _text(value): return str(value or "").strip().casefold()

    async def find_match_odds(self,home:str,away:str,kickoff:datetime):
        date=kickoff.astimezone(timezone.utc).date().isoformat()
        data=await self._get(settings.msport_matches_path,{"sport_id":settings.msport_sport_id,"date":date})
        home_t=self._text(home); away_t=self._text(away)
        event=None
        for item in self._walk(data):
            h=item.get("home_team") or item.get("home")
            a=item.get("away_team") or item.get("away")
            if isinstance(h,dict): h=h.get("name") or h.get("team_name")
            if isinstance(a,dict): a=a.get("name") or a.get("team_name")
            if self._text(h)==home_t and self._text(a)==away_t:
                event=item; break
        if not event: return None
        event_id=event.get("event_id") or event.get("id") or event.get("match_id")
        if not event_id: return None
        detail=await self._get(settings.msport_match_odds_path,{"event_id":event_id})
        return {"event_id":str(event_id),"match":event,"detail":detail}
