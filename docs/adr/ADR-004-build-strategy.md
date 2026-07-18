# ADR-004: Cross-Compile ARM64 Images on Mini PC with Wake-on-LAN

## Status

Accepted

## Context

The Raspberry Pi 5 runs ARM64 (aarch64) architecture. Docker images must be built for this platform. Building images directly on the Pi is slow (especially for compiled dependencies like Python packages with C extensions) and consumes the Pi's limited resources while it should be serving traffic.

Options considered:
- **Build on Pi directly**: Simple but slow. Compiling large Python/Node dependencies on ARM can take 10-20 minutes. Uses resources meant for serving.
- **GitHub Actions (cloud build)**: Free tier available, but produces x86 images by default. ARM builds via QEMU in CI are slow. Adds external dependency.
- **Dedicated always-on build server**: Fast builds, but wastes energy running 24/7 when builds happen infrequently.
- **Mini PC with Wake-on-LAN**: Fast builds (x86 with QEMU cross-compilation), sleeps when idle, wakes on demand.

## Decision

Use a Mini PC (i5 8th Gen+, 16GB RAM) as a build server that:
1. Sleeps when idle (after 15 minutes of no build activity)
2. Wakes via Wake-on-LAN magic packet sent by the GreenCloud API on the Pi
3. Builds ARM64 images using `docker buildx` with QEMU emulation
4. Pushes built images to the local Docker registry on the Pi
5. Returns to sleep after idle timeout

## Consequences

**Positive:**
- Fast builds (x86 CPU with 16GB RAM handles cross-compilation well)
- Energy efficient — only draws power during active builds
- Pi stays free to serve traffic during builds
- No external dependency (builds happen on local network)
- Wake-on-LAN adds ~30 seconds latency — acceptable for a deployment pipeline

**Negative:**
- Added complexity: WoL networking, sleep/wake management, health checking
- QEMU cross-compilation is slower than native ARM builds (but still faster than building on Pi)
- Requires Mini PC hardware investment (~£150-200)
- Network must support WoL (switch must pass magic packets — most unmanaged switches do)

**Mitigations:**
- For local development (before hardware arrives), builds run on Windows PC targeting `linux/amd64`
- WoL has a stub implementation initially — real implementation when hardware arrives
- If cross-compilation is too slow for specific packages, consider multi-stage builds with pre-built base images
