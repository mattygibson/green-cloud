from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Carbon Engine configuration."""

    # Electricity Maps
    electricity_maps_api_key: str = ""
    electricity_maps_zone: str = "GB"
    electricity_maps_base_url: str = "https://api.electricitymap.org/v3"
    electricity_maps_cache_ttl_seconds: int = 900  # 15 minutes

    # Power estimation (Pi 5)
    pi_idle_watts: float = 4.0
    pi_max_watts: float = 12.0
    minipc_idle_watts: float = 15.0
    minipc_max_watts: float = 65.0

    # Carbon thresholds (gCO2eq/kWh)
    carbon_threshold_low: int = 100
    carbon_threshold_high: int = 300

    # Data storage
    data_dir: str = "/app/data"

    model_config = {"env_prefix": "CARBON_"}


settings = Settings()
