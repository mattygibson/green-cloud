# Task 9: Hardware Setup and Migration to Real Infrastructure

## Objective

Set up the physical Raspberry Pi 5 and Mini PC, migrate all services from your Windows dev environment to real hardware, and validate the full pipeline end-to-end on physical infrastructure.

## Prerequisites

- All previous tasks complete (software working locally)
- Hardware procured and in hand:
  - Raspberry Pi 5 (8GB)
  - NVMe HAT + 500GB SSD
  - Official Pi 5 PSU
  - Mini PC (i5 8th Gen+, 16GB RAM)
  - 8-port gigabit switch
  - Ethernet cables
  - Optional: USB power meter, smart plug

## Implementation Steps

### 9.1 Raspberry Pi 5 setup

**OS Installation:**
- Download Ubuntu Server 24.04 LTS (arm64)
- Flash to NVMe SSD using Raspberry Pi Imager
- Configure boot from NVMe (may need initial SD card boot to update firmware)
- Set hostname: `greencloud-node-01`

**Initial configuration:**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Set static IP
sudo nano /etc/netplan/01-netcfg.yaml
# Configure: 192.168.1.100/24 (example)

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose plugin
sudo apt install docker-compose-plugin

# Enable Docker to start on boot
sudo systemctl enable docker

# Configure Docker for local insecure registry
sudo tee /etc/docker/daemon.json << EOF
{
  "insecure-registries": ["192.168.1.100:5000"],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF
sudo systemctl restart docker

# Set up SSH key auth (copy from Windows PC)
mkdir -p ~/.ssh
# Add public key to authorized_keys

# Disable password auth
sudo sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd
```

**Performance tuning:**
- Increase swap (useful for builds if ever needed): 2GB
- Set GPU memory to minimum (16MB) — headless server
- Disable unused services (bluetooth, wifi if using ethernet)

### 9.2 Mini PC setup

**OS Installation:**
- Install Ubuntu Server 24.04 LTS (amd64)
- Set hostname: `greencloud-builder`
- Configure static IP: `192.168.1.101`

**Docker + BuildKit:**
```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Set up BuildKit with QEMU for ARM64 cross-compilation
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes

# Create buildx builder
docker buildx create --name greencloud-builder --use
docker buildx inspect --bootstrap

# Verify ARM64 build capability
docker buildx build --platform linux/arm64 -t test-arm64 . 
```

**Wake-on-LAN configuration:**
```bash
# Enable WoL in BIOS (do this during initial hardware setup)
# Verify WoL is working:
sudo apt install ethtool
sudo ethtool eth0 | grep Wake-on
# Should show: Wake-on: g

# Enable WoL persistence
sudo tee /etc/systemd/system/wol.service << EOF
[Unit]
Description=Enable Wake-on-LAN
After=network.target

[Service]
Type=oneshot
ExecStart=/sbin/ethtool -s eth0 wol g

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl enable wol.service

# Note the MAC address for WoL:
ip link show eth0 | grep ether
```

**Auto-sleep after idle:**
```bash
# Install auto-suspend script
# Sleeps after 15 minutes of no Docker build activity
sudo tee /usr/local/bin/auto-sleep.sh << 'EOF'
#!/bin/bash
IDLE_THRESHOLD=900  # 15 minutes in seconds
while true; do
  if ! docker ps --filter "status=running" --filter "label=greencloud.build=true" -q | grep -q .; then
    IDLE_TIME=$(awk '{print int($1)}' /proc/uptime)  # simplified
    if [ "$IDLE_TIME" -gt "$IDLE_THRESHOLD" ]; then
      systemctl suspend
    fi
  fi
  sleep 60
done
EOF
chmod +x /usr/local/bin/auto-sleep.sh
```

### 9.3 Network setup

**Physical connections:**
```
Router → Switch Port 1
Pi 5   → Switch Port 2 (192.168.1.100)
Mini PC → Switch Port 3 (192.168.1.101)
Windows PC → Switch Port 4 (or via WiFi)
```

**Router configuration:**
- Reserve DHCP leases for Pi and Mini PC (or use static IPs)
- No port forwarding needed (Cloudflare Tunnel handles ingress)

**Verify connectivity:**
```bash
# From Windows PC:
ping 192.168.1.100  # Pi
ping 192.168.1.101  # Mini PC

# From Pi:
ping 192.168.1.101  # Mini PC
```

### 9.4 Deploy services to Pi

```bash
# Clone repo on Pi
git clone https://github.com/yourusername/green-cloud.git
cd green-cloud

# Create environment files
cp infra/.env.example infra/.env.prod
cp infra/.env.example infra/.env.dev
# Edit with real values

# Start infrastructure stack
docker compose -f infra/docker-compose.infra.yml up -d

# Verify registry is running
curl http://localhost:5000/v2/

# Start prod stack
docker compose -f infra/docker-compose.prod.yml up -d

# Verify everything is healthy
docker ps
curl http://localhost/health
```

### 9.5 Configure Cloudflare Tunnel on Pi

```bash
# Install cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb

# Authenticate (one-time)
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create greencloud

# Configure (already in docker-compose.infra.yml, but for systemd alternative):
# Copy tunnel credentials to /etc/cloudflared/
# Copy config.yml to /etc/cloudflared/

# Or just use the Docker container (already configured in Task 6)
```

### 9.6 Test Wake-on-LAN pipeline

```bash
# From Pi, wake the Mini PC:
python3 scripts/wake-on-lan.py --mac AA:BB:CC:DD:EE:FF --broadcast 192.168.1.255

# Wait for Mini PC to boot
# Verify it's reachable:
ping 192.168.1.101

# Trigger a build remotely
ssh greencloud-builder "cd /path/to/green-cloud && docker buildx build ..."
```

### 9.7 End-to-end pipeline test

1. Push a code change to GitHub `prod` branch
2. Verify webhook reaches GreenCloud API on Pi
3. Verify Mini PC wakes up
4. Verify build completes on Mini PC (ARM64 image)
5. Verify image pushed to Pi's local registry
6. Verify agent deploys new image
7. Verify app serves new version at `app.yourdomain.com`
8. Verify Mini PC goes back to sleep after idle timeout

### 9.8 USB power meter setup (optional)

If using a USB-C power meter:
- Connect inline between PSU and Pi
- If it has USB data output (e.g., UM25C):
  ```bash
  # Install python serial library
  pip install pyserial
  # Configure Carbon Engine to read from /dev/ttyUSB0
  ```
- Update Carbon Engine config with `POWER_SOURCE=usb_meter`

### 9.9 Create operational runbooks

Location: `docs/runbooks/`

- `pi-setup.md` — Full Pi setup from scratch
- `minipc-setup.md` — Mini PC setup and WoL config
- `network-diagram.md` — Physical and logical network layout
- `troubleshooting.md` — Common issues and fixes
- `backup-restore.md` — How to backup volumes and restore

## Test Requirements

- Full pipeline works on real hardware (push → build → deploy → serve)
- Cloudflare Tunnel serves traffic from external network
- Wake-on-LAN reliably wakes Mini PC
- Mini PC sleeps after idle timeout
- Pi survives a reboot and all services restart automatically
- Power meter readings (if available) appear in Carbon Engine

## Demo

The entire system running on physical hardware, publicly accessible at your domain, with real energy measurements feeding the carbon dashboard. Push code → it's live on the internet, built on your own hardware, measured for carbon impact.

## Dependencies

- All previous tasks (software is ready)
- Hardware procured and physically set up

## Estimated Effort

- 8-12 hours (including hardware assembly and debugging)
