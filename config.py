from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    redis_host: str = "localhost"
    redis_port: int = 6379

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

print("LOADED SETTINGS:", settings.model_dump())