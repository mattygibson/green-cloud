from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    environment: str = "development"

    # Domain
    domain: str = "green-cloud.uk"

    # GitHub webhook
    github_webhook_secret: str = "changeme"

    # Docker registry
    registry_host: str = "localhost:5000"  # For API health checks (container network)
    build_registry_host: str = "localhost:5000"  # For buildx push (host network)

    # Build server (Mini PC)
    build_server_mac: str = "AA:BB:CC:DD:EE:FF"
    build_server_ip: str = "192.168.1.101"
    build_server_broadcast: str = "192.168.1.255"
    build_platform: str = "linux/amd64"  # Use linux/arm64 for Pi target

    # Database
    database_url: str = "sqlite:///./data/greencloud.db"

    # Repository
    repo_url: str = "https://github.com/mattygibson/green-cloud.git"

    model_config = {"env_file": ".env", "env_prefix": "GREENCLOUD_"}


settings = Settings()
