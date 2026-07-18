# Hardware Procurement Checklist

## Priority Order

Buy in this order to start development incrementally:

### Priority 1: Core Compute (required to run anything)

| Item | Spec | Where to Buy | Est. Cost |
|------|------|--------------|-----------|
| Raspberry Pi 5 | 8GB RAM | [The Pi Hut](https://thepihut.com) / [Pimoroni](https://pimoroni.com) | ~£80 |
| Official Pi 5 PSU | 27W USB-C | Same as above | ~£12 |
| NVMe HAT | PCIe to M.2 adapter for Pi 5 | Pimoroni / The Pi Hut | ~£15 |
| NVMe SSD | 500GB M.2 2230 or 2242 | Amazon | ~£45 |
| MicroSD card | 32GB (for initial boot only) | Amazon | ~£8 |

**Subtotal: ~£160**

### Priority 2: Networking (required for multi-device setup)

| Item | Spec | Where to Buy | Est. Cost |
|------|------|--------------|-----------|
| 8-port Gigabit Switch | Unmanaged (TP-Link, Netgear) | Amazon | ~£20 |
| Ethernet cables | Cat6, various lengths (0.5m, 1m, 2m) | Amazon | ~£10 |

**Subtotal: ~£30**

### Priority 3: Build Server (required for CI/CD pipeline)

| Item | Spec | Where to Buy | Est. Cost |
|------|------|--------------|-----------|
| Mini PC | i5 8th Gen+, 16GB RAM, Ethernet with WoL support | eBay / refurbished | ~£150-200 |

Recommended models (refurbished):
- Lenovo ThinkCentre Tiny (M720q, M920q)
- Dell OptiPlex Micro (3060, 5060, 7060)
- HP EliteDesk 800 G4 Mini

**Important:** Verify Wake-on-LAN support in BIOS before purchasing.

**Subtotal: ~£150-200**

### Priority 4: Energy Monitoring (optional, for carbon tracking)

| Item | Spec | Where to Buy | Est. Cost |
|------|------|--------------|-----------|
| USB-C Power Meter | Inline, with data logging (e.g., ChargerLAB KM003C) | Amazon / AliExpress | ~£15-30 |
| Smart Plug | WiFi, energy monitoring, API accessible (e.g., TP-Link Kasa KP115) | Amazon | ~£15 |

**Subtotal: ~£30-45**

## Total Estimated Cost

| Tier | Items | Cost |
|------|-------|------|
| Minimum viable (Pi only) | Priority 1 | ~£160 |
| Full setup (no monitoring) | Priority 1-3 | ~£340-390 |
| Complete with energy tracking | Priority 1-4 | ~£370-435 |

## Compatibility Notes

### NVMe HAT
- The Pi 5 has a single PCIe lane (Gen 2 x1, ~400MB/s max)
- Use M.2 2230 or 2242 form factor SSDs
- Recommended HATs: Pimoroni NVMe Base, Geekworm X1001
- Some HATs require a taller case — check clearance

### Wake-on-LAN
- Must be enabled in BIOS (usually under Power Management)
- The Ethernet port must support WoL (most built-in NICs do, USB adapters typically don't)
- The switch must pass magic packets (all unmanaged switches do)
- Note the MAC address of the Mini PC's Ethernet port during setup

### Pi 5 Power
- The official 27W PSU is recommended — third-party PSUs may not provide enough power for NVMe + peripherals
- Under full load with NVMe, the Pi 5 draws ~12W
- Idle with NVMe: ~4W

## Pre-Purchase Verification

Before buying the Mini PC:
- [ ] Confirm i5 8th Gen or newer (for performance and efficiency)
- [ ] Confirm 16GB RAM (or upgradeable to 16GB)
- [ ] Confirm WoL support in BIOS specs/manual
- [ ] Confirm Ethernet port is built-in (not USB adapter)
- [ ] Check it can run Ubuntu Server 24.04 (driver compatibility)
