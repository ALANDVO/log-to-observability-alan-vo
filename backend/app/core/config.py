import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    app_name: str = "log-to-observability"
    app_version: str = "1.0.0"
    environment: str = Field(default="development", alias="ENVIRONMENT")
    demo_mode: bool = Field(default=True, alias="DEMO_MODE")
    
    host: str = Field(default="127.0.0.1", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    database_url: str = Field(default="sqlite:///./data/observability.db", alias="DATABASE_URL")
    
    # LLM Settings (opt-in advisory only, API key is the only secret)
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_provider: str = Field(default="openai-compatible", alias="LLM_PROVIDER")
    llm_model: str = Field(default="gpt-4o", alias="LLM_MODEL")
    llm_base_url: str = Field(default="https://api.openai.com/v1", alias="LLM_BASE_URL")
    
    # OIDC Keycloak settings
    oidc_issuer_url: str = Field(default="http://127.0.0.1:8080/realms/observability", alias="OIDC_ISSUER_URL")
    oidc_client_id: str = Field(default="observability-app", alias="OIDC_CLIENT_ID")
    oidc_client_secret: str = Field(default="", alias="OIDC_CLIENT_SECRET")
    oidc_audience: str = Field(default="observability-app", alias="OIDC_AUDIENCE")
    jwt_secret: str = Field(default="local-dev-jwt-signing-secret-32-chars-minimum", alias="JWT_SECRET")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def validate_production_safety(self) -> None:
        if self.environment.lower() == "production" and self.demo_mode:
            raise RuntimeError("CRITICAL SECURITY ERROR: Demo mode is prohibited in production.")

settings = Settings()
settings.validate_production_safety()
