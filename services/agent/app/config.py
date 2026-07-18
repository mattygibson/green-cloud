from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: str = "development"
    registry_host: str = "localhost:5000"
    compose_project_dir: str = "/infra"
    greencloud_api_url: str = "http://greencloud-api:8000"

    # Health check settings
    health_check_timeout: int = 60  # seconds
    health_check_interval: int = 5  # seconds

    model_config = {"env_file": ".env", "env_prefix": "AGENT_"}


settings = Settings()
