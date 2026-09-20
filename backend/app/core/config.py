from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://football:football@db:5432/football"
    api_football_key: str = ""
    api_football_base_url: str = "https://v3.football.api-sports.io"
    msport_api_key: str = ""
    msport_api_base_url: str = ""
    msport_matches_path: str = "get_matches"
    msport_match_odds_path: str = "get_match_odds"
    msport_sport_id: str = "sr:sport:1"
    msport_enabled: bool = True
    admin_token: str = "change-me"
    model_dir: str = "/app/models"
    app_env: str = "development"
    league_ids: str = "39,140,135,78,61,88,94,144,203,179,218,207,197,119,103,113,106,345,210,286,283,333,235,253,307"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    @property
    def leagues(self): return [int(x.strip()) for x in self.league_ids.split(",") if x.strip()]

settings = Settings()
