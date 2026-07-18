# Task 8: Carbon Engine — Electricity Maps Integration and Energy Dashboard

## Objective

Build the carbon-aware layer that tracks energy usage and grid carbon intensity, calculates emissions, surfaces this in a sustainability dashboard, and enables carbon-aware scheduling of non-critical workloads.

## Prerequisites

- Task 7 complete (Prometheus + Grafana running)
- Electricity Maps API key (free trial: https://api-portal.electricitymaps.com/)
- Optional: USB power meter connected to Pi

## Implementation Steps

### 8.1 Create the Carbon Engine service

Location: `services/carbon-engine/`

```
services/carbon-engine/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Settings (API key, zone, thresholds)
│   ├── routers/
│   │   ├── carbon.py        # Carbon data endpoints
│   │   ├── energy.py        # Energy usage endpoints
│   │   └── scheduler.py     # Carbon-aware scheduling endpoints
│   ├── services/
│   │   ├── electricity_maps.py  # API client
│   │   ├── power_monitor.py     # Power measurement
│   │   ├── calculator.py        # Emissions calculator
│   │   └── scheduler.py         # Carbon-aware scheduling logic
│   ├── models/
│   │   ├── carbon.py        # Carbon intensity models
│   │   └── energy.py        # Energy measurement models
│   └── db/
│       └── database.py      # Time-series storage
├── tests/
│   ├── test_calculator.py
│   ├── test_scheduler.py
│   ├── test_electricity_maps.py
│   └── conftest.py
├── Dockerfile
└── requirements.txt
```

### 8.2 Implement Electricity Maps API client

Service: `app/services/electricity_maps.py`

Endpoints to use:
- `GET /v3/carbon-intensity/latest?zone={zone}` — current carbon intensity (gCO2eq/kWh)
- `GET /v3/carbon-intensity/history?zone={zone}` — historical data (last 24h)
- `GET /v3/carbon-intensity/forecast?zone={zone}` — forecast (if available)

Implementation:
- Async HTTP client (httpx)
- Cache responses (intensity doesn't change faster than every 15-60 min)
- Handle rate limiting gracefully (free tier has limits)
- Fallback: if API is unavailable, use last known value
- Configure zone via environment variable (e.g., `GB` for UK)

### 8.3 Implement power monitoring

Service: `app/services/power_monitor.py`

**Option A: USB power meter (hardware available)**
- Read from USB serial device (e.g., UM25C or similar)
- Parse voltage, current, power readings
- Sample every 10 seconds

**Option B: Software estimation (no hardware meter)**
- Estimate power from CPU usage:
  - Pi 5 idle: ~3-4W
  - Pi 5 full load: ~12W
  - Linear interpolation based on CPU percentage
- Read CPU usage from `/proc/stat` or Docker stats API
- Formula: `estimated_watts = idle_watts + (max_watts - idle_watts) * cpu_percentage`

**Option C: Smart plug (for Mini PC)**
- Query smart plug API for real-time power draw
- Useful for tracking build server energy

Expose as Prometheus metrics:
```
greencloud_power_watts{source="pi"} 4.2
greencloud_power_watts{source="minipc"} 0  # 0 when sleeping
```

### 8.4 Implement emissions calculator

Service: `app/services/calculator.py`

Core formula:
```
emissions_gCO2 = energy_kWh * carbon_intensity_gCO2_per_kWh
```

Calculate:
- **Real-time emissions rate**: current power (W) × current intensity (gCO2/kWh) ÷ 1000
- **Cumulative emissions**: integrate over time (sum of 15-min intervals)
- **Per-deployment emissions**: energy used during build + deploy × average intensity during that period
- **Daily/weekly/monthly totals**

Store results:
- Prometheus metrics for real-time dashboards
- SQLite or time-series file for historical reporting

### 8.5 Implement carbon-aware scheduling

Service: `app/services/scheduler.py`

Logic:
- Define intensity thresholds:
  - `low` (green): < 100 gCO2/kWh — all workloads proceed
  - `medium` (amber): 100-300 gCO2/kWh — defer non-critical builds
  - `high` (red): > 300 gCO2/kWh — only critical (prod) deploys proceed
- Non-critical workloads: dev deployments, scheduled maintenance tasks, registry cleanup
- Critical workloads: prod deployments (always immediate)

Integration with GreenCloud API:
- Before triggering a dev build, check carbon intensity
- If above threshold, queue the build and set estimated execution time based on forecast
- Notify user: "Build queued — grid intensity is high. Estimated start: 14:30"

### 8.6 Create carbon API endpoints

```
GET  /carbon/current          # Current carbon intensity for configured zone
GET  /carbon/forecast         # Next 24h forecast
GET  /carbon/history          # Historical intensity data
GET  /carbon/emissions        # Cumulative emissions (today/week/month/all-time)
GET  /carbon/per-deployment   # Emissions attributed to each deployment
GET  /carbon/status           # Overall carbon status (green/amber/red)
POST /carbon/threshold        # Update scheduling thresholds
```

### 8.7 Create Grafana sustainability dashboard

Location: `infra/grafana/dashboards/greencloud-sustainability.json`

Panels:
- **Current Grid Status**: big gauge showing gCO2/kWh with color zones
- **Carbon Intensity Timeline**: line chart (last 24h) with forecast overlay
- **Power Usage**: real-time watts drawn by Pi and Mini PC
- **Cumulative Emissions**: counter showing total gCO2 emitted (today/all-time)
- **Emissions per Deployment**: bar chart of recent deployments with their carbon cost
- **Deferred Builds**: count of builds waiting for lower intensity
- **Carbon Savings**: estimated emissions avoided by deferring builds

### 8.8 Expose Prometheus metrics

```
# Carbon intensity
greencloud_carbon_intensity_gco2_per_kwh{zone="GB"} 142.5

# Power consumption
greencloud_power_watts{node="pi5"} 4.2
greencloud_power_watts{node="minipc"} 0

# Emissions
greencloud_emissions_gco2_total 1523.4
greencloud_emissions_gco2_today 42.1

# Scheduling
greencloud_carbon_status{status="medium"} 1
greencloud_builds_deferred_total 3
greencloud_carbon_savings_gco2_total 89.2
```

### 8.9 Add Carbon Engine to infrastructure Compose

```yaml
carbon-engine:
  build: ../services/carbon-engine
  container_name: greencloud-carbon
  restart: unless-stopped
  environment:
    ELECTRICITY_MAPS_API_KEY: ${ELECTRICITY_MAPS_API_KEY}
    ELECTRICITY_MAPS_ZONE: ${CARBON_ZONE:-GB}
    CARBON_THRESHOLD_LOW: 100
    CARBON_THRESHOLD_HIGH: 300
    PI_IDLE_WATTS: 4
    PI_MAX_WATTS: 12
  volumes:
    - carbon-data:/app/data
  networks:
    - infra-net
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.carbon.rule=Host(`carbon.${DOMAIN}`)"
```

### 8.10 Document sustainability methodology

Create `docs/sustainability/methodology.md`:
- Carbon accounting boundary (what's in scope, what's not)
- Data sources and their accuracy
- Calculation methodology
- Limitations (GitHub hosting out of scope, network energy not measured)
- How to improve accuracy over time

## Test Requirements

- Unit test: emissions calculator produces correct results for known inputs
- Unit test: scheduler correctly defers builds when intensity is high
- Unit test: scheduler allows prod builds regardless of intensity
- Integration test: mock Electricity Maps API → verify carbon metrics appear in Prometheus
- Integration test: trigger dev build during "high" intensity → build is queued
- Grafana dashboard shows real data (or realistic mock data)

## Demo

Dashboard showing "your cloud emitted X grams of CO2 today" with a timeline of grid carbon intensity and your energy usage overlaid. When grid intensity is high, dev builds are automatically deferred until conditions improve.

## Dependencies

- Task 7 (Prometheus + Grafana for dashboards)
- Task 4 (GreenCloud API for build deferral integration)
- Electricity Maps API key

## Estimated Effort

- 10-12 hours
