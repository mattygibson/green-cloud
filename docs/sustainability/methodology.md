# Carbon Accounting Methodology

## Scope

GreenCloud tracks Scope 2 (indirect) emissions from electricity consumed by:

- **Raspberry Pi 5** (always-on production host)
- **Mini PC** (on-demand build server, sleeps when idle)

### In Scope

| Source | Measurement | Method |
|--------|------------|--------|
| Pi 5 electricity | Continuous | CPU-based estimation (Option B) |
| Mini PC electricity | During builds | CPU-based estimation |

### Out of Scope

- GitHub hosting energy (third-party infrastructure)
- Network transit energy (ISP, CDN, Cloudflare)
- Embodied carbon (manufacturing of hardware)
- User device energy (visitors loading the app)
- Cooling (passive cooling, no AC needed for Pi)

## Data Sources

### Grid Carbon Intensity

- **Provider**: [Electricity Maps](https://app.electricitymaps.com/)
- **Metric**: Average carbon intensity (gCO2eq/kWh)
- **Zone**: GB (Great Britain) — configurable via `CARBON_ZONE`
- **Resolution**: Updated every 15-60 minutes
- **Type**: Average intensity (not marginal)

We use **average** intensity rather than marginal because:
- It's compatible with GHG Protocol and carbon reporting frameworks
- It represents the actual grid mix at the time of consumption
- Marginal intensity is more appropriate for policy decisions about new generation

### Power Consumption

**Current method: CPU-based estimation (Option B)**

- Pi 5 idle power: ~4W (measured baseline)
- Pi 5 max power: ~12W (under full CPU load)
- Linear interpolation: `watts = idle + (max - idle) * cpu_percent`

This is an approximation. Actual power varies with:
- I/O activity (NVMe, network)
- USB peripherals
- Ambient temperature

**Future improvement: USB power meter (Option A)**

A USB power meter (e.g., UM25C) would provide real measurements. This is planned for when hardware is deployed.

## Calculation

### Real-time Emissions Rate

```
emissions_rate (gCO2/h) = power (W) / 1000 * carbon_intensity (gCO2/kWh)
```

### Cumulative Emissions

Using trapezoidal integration over 60-second intervals:

```
for each interval:
    avg_power = (previous_watts + current_watts) / 2
    energy_kwh = (avg_power / 1000) * (interval_seconds / 3600)
    avg_intensity = (previous_intensity + current_intensity) / 2
    emissions_gco2 = energy_kwh * avg_intensity
    total += emissions_gco2
```

### Per-Deployment Emissions

```
deployment_emissions = (avg_power_during_build / 1000) * (duration_hours) * avg_intensity
```

## Carbon-Aware Scheduling

### Thresholds

| Status | Intensity | Action |
|--------|-----------|--------|
| Low (green) | < 100 gCO2/kWh | All workloads proceed |
| Medium (amber) | 100-300 gCO2/kWh | Non-critical workloads deferred |
| High (red) | > 300 gCO2/kWh | Only production deploys proceed |

### What Gets Deferred

- Dev environment deployments
- Scheduled maintenance tasks
- Registry cleanup operations
- Non-urgent image rebuilds

### What Always Proceeds

- Production deployments (user-facing changes)
- Security patches
- Rollbacks

## Limitations

1. **Estimation accuracy**: CPU-based power estimation has ~20-30% error margin
2. **Grid data latency**: Electricity Maps data may be 15-60 minutes behind real-time
3. **Incomplete scope**: Only measures direct electricity, not full lifecycle
4. **Zone granularity**: GB zone covers all of Great Britain; Scottish grid is typically cleaner
5. **No Scope 3**: Does not account for supply chain, user devices, or network

## Improving Accuracy

Planned improvements (in priority order):

1. **USB power meter** — direct measurement replaces estimation
2. **Smart plug for Mini PC** — real power data during builds
3. **Scotland-specific zone** — if Electricity Maps adds sub-national zones
4. **Embodied carbon amortisation** — spread manufacturing emissions over device lifetime

## References

- [GHG Protocol Scope 2 Guidance](https://ghgprotocol.org/scope-2-guidance)
- [Electricity Maps Methodology](https://www.electricitymaps.com/methodology)
- [Green Software Foundation - SCI Specification](https://sci-guide.greensoftware.foundation/)
- [Raspberry Pi 5 Power Consumption](https://www.raspberrypi.com/documentation/computers/raspberry-pi-5.html)
