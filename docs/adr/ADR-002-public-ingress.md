# ADR-002: Use Cloudflare Tunnel for Public Ingress

## Status

Accepted

## Context

GreenCloud needs to serve web applications publicly from a home network. The operator (project owner) is not experienced with networking and wants to avoid exposing the home network to security risks.

Options considered:
- **Port forwarding + Dynamic DNS**: Classic approach, but opens ports on the router. Requires firewall management and exposes the home IP.
- **Tailscale/WireGuard**: Secure, but only accessible to authenticated users on the mesh network — not suitable for public-facing apps.
- **Cloudflare Tunnel**: Outbound-only connections from Pi to Cloudflare edge. No open ports, free HTTPS, DDoS protection included.
- **ngrok**: Similar concept but paid for custom domains and persistent tunnels.

## Decision

Use Cloudflare Tunnel (`cloudflared` daemon) running on the Pi to expose services publicly.

- The `cloudflared` container creates outbound-only connections to Cloudflare's global network
- Traffic flows: Internet → Cloudflare Edge → Tunnel → Traefik → Service
- DNS records point to the tunnel (CNAME to `<tunnel-id>.cfargotunnel.com`)
- HTTPS is terminated at Cloudflare's edge (free SSL certificates)

## Consequences

**Positive:**
- Zero ports opened on the home router
- Free HTTPS with automatic certificate management
- DDoS protection and CDN caching included on free tier
- Simple setup — no firewall rules, no port forwarding, no dynamic DNS
- Custom domain support

**Negative:**
- Dependent on Cloudflare's availability (single point of failure for external access)
- Requires a registered domain name (small annual cost)
- Traffic routes through Cloudflare — added latency for local access (use direct IP for LAN)
- Cloudflare can inspect traffic (acceptable for a personal project)

**Mitigations:**
- For local development, access services directly via LAN IP or `*.localhost`
- If Cloudflare goes down, services still run — just not publicly accessible
