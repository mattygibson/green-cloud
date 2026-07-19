# Renewable Energy Options for GreenCloud

## Energy Requirement

GreenCloud needs **307 Wh/day** (112 kWh/year) to run the full stack (Pi + Mini PC + switch).

The Pi alone (the always-on component) needs **120 Wh/day** (44 kWh/year).

## Option 1: Solar Panel

**Best for:** Year-round offset with battery storage. Most practical for a home setup.

### How It Works

Solar panel charges a 12V battery during daylight. A buck converter steps down to 5V USB-C to power the Pi. MPPT charge controller maximises efficiency.

### Sizing for Falkirk, Scotland

| Scenario | Panel Size | Annual Coverage |
|----------|-----------|-----------------|
| Pi only (120 Wh/day) | 50-80W | ~80-100% (annual avg) |
| Full stack (307 Wh/day) | 150-200W | ~80-100% (annual avg) |
| Subsidise ~60% | 100W | ~60-70% |

**Note:** Scotland gets ~2.5 peak sun hours/day annual average. Winter drops to ~0.8 hours. A battery bridges overnight but not prolonged cloudy weeks.

### What to Buy

**Budget starter (Pi only):**

| Item | Example | Est. Cost |
|------|---------|-----------|
| 100W Mono panel | ECO-WORTHY 100W / Renogy 100W | £70-90 |
| MPPT controller | Victron SmartSolar 75/10 | £60-80 |
| LiFePO4 battery | 12V 20Ah (Fogstar Drift) | £80-120 |
| Buck converter | 12V→5V 5A USB-C output | £10-15 |
| Cables + fuses | MC4, inline fuse, connectors | £15-20 |
| **Total** | | **£235-325** |

**Full coverage:**

| Item | Example | Est. Cost |
|------|---------|-----------|
| 200W Mono panel | ECO-WORTHY 200W / Renogy 200W | £120-150 |
| MPPT controller | Victron SmartSolar 75/15 | £70-90 |
| LiFePO4 battery | 12V 40Ah (for overnight + cloudy) | £150-200 |
| Buck converter | 12V→5V 5A USB-C output | £10-15 |
| Cables + fuses | MC4, inline fuse, connectors | £15-20 |
| **Total** | | **£365-475** |

**Pi-specific HAT (cleanest integration):**

| Item | Example | Est. Cost |
|------|---------|-----------|
| PV PI HAT | AutoEcology — MPPT solar HAT for Pi | £45 |
| 12V LiFePO4 battery | 12V 6Ah (enough for overnight) | £40-60 |
| 50W panel | Any 12V 50W mono panel | £40-50 |
| **Total** | | **£125-155** |

### Pros and Cons

| Pros | Cons |
|------|------|
| Silent, no moving parts | Low output in Scottish winter |
| Low maintenance | Needs south-facing location |
| Scales easily (add more panels) | Battery degrades over 5-10 years |
| No planning permission needed (<3m²) | Upfront cost |

---

## Option 2: Micro Wind Turbine

**Best for:** Scotland's strong wind resource. Generates well in winter when solar is weak. Complementary to solar.

### How It Works

Small turbine (roof-mounted or pole-mounted) generates 12V DC from wind. Same charge controller → battery → buck converter setup as solar.

### Sizing

Scotland has excellent wind — Falkirk area averages 5-7 m/s wind speed. A small 12V turbine in a good position can generate significant power, especially in winter when solar output drops.

| Turbine Size | Expected Output (Scotland) | Coverage |
|-------------|---------------------------|----------|
| 100W rated | 50-100 Wh/day avg | Pi only (partial) |
| 300W rated | 150-400 Wh/day avg | Full stack in windy conditions |
| 400-600W rated | 300-800 Wh/day avg | Full stack + surplus |

**Important:** Rated wattage is at high wind speeds. Actual average output in a residential setting is typically 15-30% of rated capacity.

### What to Buy

| Item | Example | Est. Cost |
|------|---------|-----------|
| Micro turbine | Rutland 504 (rated 60W, 12V) | £200-250 |
| Alternative | LE-300 (rated 300W, 12V) | £400-500 |
| Charge controller | Hybrid solar/wind controller | £40-60 |
| Battery | 12V 20Ah LiFePO4 | £80-120 |
| Mounting pole/bracket | Roof mount or 3m pole | £50-100 |
| **Total** | | **£370-1,030** |

### Pros and Cons

| Pros | Cons |
|------|------|
| Works at night and in cloudy weather | Noise (varies by model) |
| Strong output in Scottish winters | Neighbours may object |
| Excellent complement to solar | May need planning permission (>mast height) |
| Scotland's wind resource is world-class | Moving parts need maintenance |
| | Location-dependent (obstructions kill output) |

### Planning Permission (Scotland)

In Scotland, micro wind turbines are permitted development (no planning needed) if:
- Building-mounted: max 1.5m blade diameter, max height 3m above roof
- Free-standing: max 1.1m blade diameter, max 11m height to blade tip
- Not in a conservation area or listed building

---

## Option 3: Hybrid Solar + Wind

**Best for:** Maximum coverage year-round. Solar covers summer, wind covers winter.

### Why Hybrid Works in Scotland

Scotland's renewable profile is seasonally complementary:
- **Summer:** Long daylight hours (17+ hours in June) but calmer winds
- **Winter:** Short days (6-7 hours in December) but strong, persistent winds

A hybrid system provides much more consistent power than either alone.

### Suggested Setup

| Item | Spec | Est. Cost |
|------|------|-----------|
| Solar panel | 100W mono | £70-90 |
| Micro turbine | Rutland 504 or similar 12V | £200-250 |
| Hybrid charge controller | Solar + wind input, 12V | £50-70 |
| LiFePO4 battery | 12V 20Ah | £80-120 |
| Buck converter | 12V→5V USB-C | £10-15 |
| Mounting + cables | Pole, MC4, fuses | £50-80 |
| **Total** | | **£460-625** |

This would cover the Pi's needs year-round with minimal grid dependence.

---

## Option 4: Green Energy Tariff

**Best for:** Zero effort, instant carbon offset. No hardware, no maintenance.

### How It Works

Switch your electricity supplier to a 100% renewable tariff. The supplier guarantees that they buy Renewable Energy Guarantees of Origin (REGOs) certificates matching your usage.

### What to Know

- **Cost:** Often comparable to standard tariffs (sometimes £0-20/month more)
- **Effort:** Phone call or online switch, done in minutes
- **Impact:** Supports renewable investment but doesn't change the physical grid mix
- **Suppliers:** Octopus Energy (100% green), Ecotricity, Good Energy, Bulb

### Pros and Cons

| Pros | Cons |
|------|------|
| Zero effort | Doesn't physically change what powers your home |
| No hardware needed | REGO certificates are controversial |
| Cheap or free | Some argue it's "paper renewable" not real |
| Immediate | Doesn't teach you about energy systems |

---

## Option 5: Thermoelectric Generator (TEG)

**Best for:** Novelty / educational value. Very low output but interesting.

### How It Works

A thermoelectric module generates electricity from a temperature difference. If you have a hot water pipe or radiator near your Pi, a TEG can trickle-charge a small battery.

### Reality Check

- Output: typically 1-5W from a large temperature differential
- Enough to trickle-charge a battery but not power a Pi directly
- More of an educational project than a practical solution

---

## Option 6: Human Power (Exercise Bike Generator)

**Best for:** Fun project, educational value, fitness motivation.

### How It Works

A dynamo attached to an exercise bike generates 12V DC while pedalling. Charges a battery that powers the Pi.

### Reality Check

- A fit cyclist generates ~75-100W sustained
- You'd need to pedal ~1 hour/day to cover the Pi's needs (120 Wh)
- Impractical as a sole power source but fun as a supplement
- "I literally powered my cloud with my legs" is a great talking point

---

## Recommendation for GreenCloud

**Start with:** Option 1 (100W solar + battery) — £235-325

**Then add:** Option 2 (micro wind) if you want year-round independence — additional £200-500

**Immediately:** Option 4 (green tariff) — £0 extra. Do this regardless of other options.

### Phased Approach

1. **Now:** Switch to a green energy tariff (free, immediate)
2. **Phase 1:** 100W solar + 20Ah battery for the Pi (proves the concept)
3. **Phase 2:** Add micro wind turbine for winter coverage (if location allows)
4. **Phase 3:** Upsize to 200W solar + 40Ah battery for full stack coverage

### Carbon Impact

| Approach | Annual Carbon | vs. Grid Only |
|----------|--------------|---------------|
| Grid only (no renewables) | 14 kg CO2e | Baseline |
| Green tariff | 0 kg CO2e (on paper) | -100% |
| 100W solar (covers ~60%) | 5.6 kg CO2e | -60% |
| 100W solar + wind hybrid | ~2 kg CO2e | -85% |
| 200W solar + wind + battery | ~0.5 kg CO2e | -96% |

---

## Summary

For a project in Falkirk, Scotland, the most practical path to genuine carbon-neutral operation is:

1. **Green tariff** (immediate, paperwork-only reduction)
2. **100W solar + battery** (covers the Pi through most of the year)
3. **Micro wind** (fills the winter gap where solar falls short)

Scotland's grid is already one of the cleanest in Europe (35 gCO2/kWh), so your baseline is already very low. Adding even a modest solar panel makes the project genuinely near-zero-carbon in practice.
