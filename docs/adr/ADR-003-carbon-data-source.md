# ADR-003: Use Electricity Maps Average Intensity API for Carbon Awareness

## Status

Accepted

## Context

GreenCloud aims to be carbon-aware — measuring and minimising the carbon emissions of its infrastructure. To calculate emissions, we need real-time grid carbon intensity data (gCO2eq per kWh) for the electricity zone where the hardware is located.

Options considered:
- **Electricity Maps (average intensity)**: Industry standard, compatible with GHG Protocol Scope 2 reporting, covers 130+ zones globally.
- **Electricity Maps (marginal intensity)**: Discontinued by Electricity Maps in 2025 due to concerns about accuracy and regulatory incompatibility.
- **National Grid ESO Carbon Intensity API (UK-specific)**: Free, good coverage, but UK-only.
- **WattTime**: Provides marginal signals — same concerns as above.
- **Static/estimated values**: No API dependency, but inaccurate and not useful for real-time decisions.

## Decision

Use the Electricity Maps API with **average** (not marginal) carbon intensity signals.

- Endpoint: `GET /v3/carbon-intensity/latest?zone={zone}`
- Data: gCO2eq/kWh at hourly granularity
- Free tier: 14-day trial, then free for non-commercial personal use
- Zone configured via environment variable (e.g., `GB` for Great Britain)

## Consequences

**Positive:**
- Compatible with GHG Protocol Scope 2 reporting guidelines
- Compatible with EU and US regulatory frameworks
- Widely accepted methodology — defensible claims
- Covers 130+ zones globally (portable if hardware moves)
- Provides historical data and forecasts

**Negative:**
- Requires API key (free for personal use, paid for commercial)
- Rate limited on free tier — need to cache responses
- Average intensity changes slowly (hourly) — not suitable for second-by-second decisions
- Limited to zones Electricity Maps covers

**Mitigations:**
- Cache API responses locally (intensity doesn't change faster than every 15-60 minutes)
- Fallback to last known value if API is unreachable
- For UK specifically, could add National Grid ESO as a secondary source if more granularity is needed
