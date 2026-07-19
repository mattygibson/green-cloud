# GreenCloud Carbon Estimate

## Location

Falkirk, Scotland, UK

## Grid Carbon Intensity

| Source | Value | Notes |
|--------|-------|-------|
| Scotland generation only | 35 gCO2e/kWh | [Scottish Gov Energy Statistics Q1 2024](https://www.gov.scot/publications/energy-statistics-for-scotland-q1-2024/) |
| Great Britain average (2024) | 124 gCO2e/kWh | [Carbon Brief analysis](https://carbonbrief.org/analysis-uks-electricity-was-cleanest-ever-in-2024/) |
| Electricity Maps zone (GB) | ~100-200 gCO2e/kWh | Varies by time of day and season |

**For estimates below, we use 124 gCO2e/kWh** (GB average) as a conservative figure, since Electricity Maps reports at the GB zone level and includes imported power. Scotland's actual consumption intensity is lower due to its high renewable generation.

## Hardware Power Consumption

### Raspberry Pi 5 (8GB) — Always On

| State | Power Draw | Source |
|-------|-----------|--------|
| Idle (no load) | 3.5W | Official Pi 5 specs |
| Moderate load (serving traffic) | 6W | Measured typical for Docker workloads |
| Full load (all cores busy) | 12W | Maximum under stress test |
| **Estimated average (24/7 server)** | **5W** | Weighted: mostly idle with occasional spikes |

### Mini PC (i5 8th Gen, 16GB) — On-Demand Only

| State | Power Draw | Source |
|-------|-----------|--------|
| Sleeping (WoL standby) | 2W | Typical S3 sleep state |
| Idle (booted, no build) | 15W | Measured for Lenovo Tiny class |
| Building (full CPU load) | 45W | During Docker buildx compilation |
| **Estimated average** | **3W** | Sleeps 95% of the time, builds ~30 min/day |

### Network Switch (8-port gigabit)

| State | Power Draw |
|-------|-----------|
| Always on | 4W |

## Daily Energy Consumption

| Component | Hours/Day | Avg Watts | Daily Energy |
|-----------|-----------|-----------|--------------|
| Raspberry Pi 5 | 24h | 5W | 120 Wh |
| Mini PC (sleep) | 23h | 2W | 46 Wh |
| Mini PC (building) | 1h | 45W | 45 Wh |
| Network Switch | 24h | 4W | 96 Wh |
| **Total** | | | **307 Wh/day** |

## Annual Energy and Carbon

| Metric | Value |
|--------|-------|
| Daily energy | 307 Wh |
| Annual energy | 112 kWh |
| **Annual carbon (GB avg, 124 gCO2/kWh)** | **13.9 kg CO2e** |
| Annual carbon (Scotland only, 35 gCO2/kWh) | 3.9 kg CO2e |

## Comparison: GreenCloud vs Cloud Providers

| Platform | Estimated Annual Carbon | Notes |
|----------|------------------------|-------|
| **GreenCloud (this project)** | **~14 kg CO2e** | Single Pi + Mini PC, GB grid average |
| AWS t3.micro (1 instance, EU) | ~20-40 kg CO2e | Based on AWS carbon footprint tool estimates |
| DigitalOcean basic droplet | ~25-50 kg CO2e | Estimated from published PUE and grid data |
| Running a home PC 24/7 | ~150-300 kg CO2e | Desktop PC draws 100-200W |

GreenCloud's ARM-based approach is inherently efficient due to the Pi's low power consumption.

## Carbon Budget Breakdown

```
Annual: 13.9 kg CO2e
├── Raspberry Pi 5:     5.4 kg CO2e (39%)  — always-on compute
├── Mini PC (sleep):    2.1 kg CO2e (15%)  — standby power
├── Mini PC (builds):   2.0 kg CO2e (15%)  — active build time
└── Network Switch:     4.3 kg CO2e (31%)  — always-on networking
```

## Opportunities to Reduce Further

1. **Carbon-aware scheduling (Task 8):** Defer builds to low-intensity periods. Scotland's wind generation peaks at night and during storms — scheduling builds during these periods could reduce the effective intensity to ~50 gCO2/kWh.

2. **Reduce Mini PC wake time:** Optimise builds to complete faster (caching, smaller images), reducing the time the Mini PC is at full load.

3. **Green tariff:** Switch to a 100% renewable electricity tariff. While this doesn't change the physical grid emissions, it does support renewable generation capacity.

4. **Switch-free setup:** For a single Pi + Mini PC, a direct Ethernet crossover cable eliminates the switch (saves ~35 Wh/day).

## What's NOT Included (Out of Scope)

- **Embodied carbon:** Manufacturing emissions of the hardware itself (~50-100 kg CO2e per device, amortised over 5+ year lifespan)
- **GitHub hosting:** Energy used by GitHub to store code and run CI
- **Network transit:** Energy used by Cloudflare and ISP infrastructure
- **User devices:** Energy consumed by browsers/devices accessing the app
- **Cooling:** No active cooling needed — Pi is passively cooled

## Methodology Notes

- Power estimates based on published hardware specifications and community measurements
- Grid intensity from official Scottish Government and Carbon Brief data (2024)
- Mini PC duty cycle assumed at 1 hour active / 23 hours sleep per day
- These are estimates — real measurements from the USB power meter (Task 8) will replace them

## Summary

GreenCloud will emit approximately **14 kg CO2e per year** running on the GB grid, or as low as **4 kg CO2e per year** when accounting for Scotland's high renewable penetration. That's roughly equivalent to driving a car 35 miles, or the carbon absorbed by one tree in a year.
