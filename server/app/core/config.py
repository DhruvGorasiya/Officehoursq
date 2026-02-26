from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "OfficeHoursQ"
    API_V1_PREFIX: str = "/api/v1"

    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 10080  # 7 days

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
