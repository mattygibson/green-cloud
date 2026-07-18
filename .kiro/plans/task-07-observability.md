# Task 7: Observability Stack (Prometheus + Grafana + Loki)

## Objective

Add monitoring and logging so you can see what's happening across all services — request rates, error rates, resource usage, deployment events, and container logs — all in one place.

## Prerequisites

- Task 6 complete (Traefik routing working)
- All services running and accessible

## Implementation Steps

### 7.1 Add Prometheus to infrastructure Compose

In `infra/docker-compose.infra.yml`:
```yaml
prometheus:
  image: prom/prometheus:latest
  container_name: greencloud-prometheus
  restart: unless-stopped
  volumes:
    - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    - ./prometheus/rules:/etc/prometheus/rules:ro
    - prometheus-data:/prometheus
  command:
    - '--config.file=/etc/prometheus/prometheus.yml'
    - '--storage.tsdb.path=/prometheus'
    - '--storage.tsdb.retention.time=30d'
  networks:
    - infra-net
  ports:
    - "9090:9090"
```

### 7.2 Configure Prometheus scrape targets

Location: `infra/prometheus/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # Traefik metrics
  - job_name: 'traefik'
    static_configs:
      - targets: ['traefik:8082']

  # GreenCloud API metrics
  - job_name: 'greencloud-api'
    static_configs:
      - targets: ['greencloud-api:8000']
    metrics_path: /metrics

  # Agent metrics
  - job_name: 'agent'
    static_configs:
      - targets: ['greencloud-agent:8000']
    metrics_path: /agent/metrics

  # Node exporter (system metrics)
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

  # Carbon engine metrics (added in Task 8)
  - job_name: 'carbon'
    static_configs:
      - targets: ['carbon-engine:8000']
    metrics_path: /metrics
```

### 7.3 Add Node Exporter for system metrics

```yaml
node-exporter:
  image: prom/node-exporter:latest
  container_name: greencloud-node-exporter
  restart: unless-stopped
  volumes:
    - /proc:/host/proc:ro
    - /sys:/host/sys:ro
    - /:/rootfs:ro
  command:
    - '--path.procfs=/host/proc'
    - '--path.rootfs=/rootfs'
    - '--path.sysfs=/host/sys'
  networks:
    - infra-net
  ports:
    - "9100:9100"
```

### 7.4 Add Loki for log aggregation

```yaml
loki:
  image: grafana/loki:latest
  container_name: greencloud-loki
  restart: unless-stopped
  volumes:
    - ./loki/loki-config.yml:/etc/loki/local-config.yml:ro
    - loki-data:/loki
  command: -config.file=/etc/loki/local-config.yml
  networks:
    - infra-net
  ports:
    - "3100:3100"
```

Location: `infra/loki/loki-config.yml`
```yaml
auth_enabled: false

server:
  http_listen_port: 3100

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2020-10-24
      store: tsdb
      object_store: filesystem
      schema: v13
      index:
        prefix: index_
        period: 24h

limits_config:
  retention_period: 30d
```

### 7.5 Add Promtail for log shipping

```yaml
promtail:
  image: grafana/promtail:latest
  container_name: greencloud-promtail
  restart: unless-stopped
  volumes:
    - ./promtail/promtail-config.yml:/etc/promtail/config.yml:ro
    - /var/lib/docker/containers:/var/lib/docker/containers:ro
    - /var/run/docker.sock:/var/run/docker.sock
  command: -config.file=/etc/promtail/config.yml
  networks:
    - infra-net
```

Location: `infra/promtail/promtail-config.yml`
```yaml
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        target_label: container
      - source_labels: ['__meta_docker_container_label_com_docker_compose_service']
        target_label: service
```

### 7.6 Add Grafana

```yaml
grafana:
  image: grafana/grafana:latest
  container_name: greencloud-grafana
  restart: unless-stopped
  environment:
    GF_SECURITY_ADMIN_USER: ${GRAFANA_USER:-admin}
    GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
    GF_USERS_ALLOW_SIGN_UP: "false"
  volumes:
    - grafana-data:/var/lib/grafana
    - ./grafana/provisioning:/etc/grafana/provisioning:ro
    - ./grafana/dashboards:/var/lib/grafana/dashboards:ro
  networks:
    - infra-net
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.grafana.rule=Host(`grafana.${DOMAIN}`)"
    - "traefik.http.services.grafana.loadbalancer.server.port=3000"
```

### 7.7 Provision Grafana data sources

Location: `infra/grafana/provisioning/datasources/datasources.yml`
```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
```

### 7.8 Create Grafana dashboards

Location: `infra/grafana/dashboards/`

**greencloud-overview.json** — Main dashboard:
- Deployment count (today/week)
- Active containers and their status
- Request rate and error rate (from Traefik)
- CPU and memory usage per container
- Disk usage

**greencloud-deployments.json** — Deployment dashboard:
- Deployment timeline (success/failure)
- Build duration
- Rollback events
- Deployment frequency

**greencloud-sustainability.json** — Placeholder for Task 8:
- Carbon intensity (current)
- Energy usage
- Emissions over time

### 7.9 Add metrics to FastAPI services

Add `prometheus-fastapi-instrumentator` to both GreenCloud API and the sample app API:

```python
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
Instrumentator().instrument(app).expose(app)
```

This auto-exposes:
- `http_requests_total`
- `http_request_duration_seconds`
- `http_request_size_bytes`
- `http_response_size_bytes`

### 7.10 Create alerting rules (optional)

Location: `infra/prometheus/rules/alerts.yml`
```yaml
groups:
  - name: greencloud
    rules:
      - alert: ContainerDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Container {{ $labels.instance }} is down"

      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
        for: 5m
        labels:
          severity: warning

      - alert: DeploymentFailed
        expr: greencloud_deployment_status{status="failed"} > 0
        for: 0m
        labels:
          severity: critical
```

## Test Requirements

- Prometheus scrapes all targets successfully (check Targets page)
- Grafana loads with pre-provisioned dashboards and data sources
- Generate traffic to the app → see request metrics appear in Grafana within 30s
- Container logs visible in Grafana via Loki
- Node exporter shows system CPU/memory/disk metrics
- Grafana accessible via `grafana.yourdomain.com` (with auth)

## Demo

Grafana dashboard showing live metrics and logs from your running application. You can see request rates, error rates, container resource usage, and search through logs — all from a single pane of glass.

## Dependencies

- Task 6 (Traefik routing for Grafana access)
- Task 5 (agent exposes metrics)
- Task 4 (GreenCloud API exposes metrics)

## Estimated Effort

- 6-8 hours (including dashboard creation)
