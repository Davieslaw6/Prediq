import httpx
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
