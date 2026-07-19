import { useEffect, useState } from "react";

interface HealthStatus {
  status: string;
  database: string;
  environment: string;
}

interface Service {
  name: string;
  url: string;
  description: string;
  status: "healthy" | "unhealthy" | "unknown";
  port: number;
}

interface SystemStats {
  cpu_percent: number | null;
  memory: {
    total_bytes: number;
    used_bytes: number;
    percent: number;
  } | null;
  disk: {
    total_bytes: number;
    used_bytes: number;
    percent: number;
  } | null;
  containers: {
    running: number;
  };
}

interface CarbonStatus {
  status: string;
  carbon_intensity_gco2_kwh: number;
  thresholds: {
    low_below: number;
    high_above: number;
  };
  description: string;
}

const SERVICES: Service[] = [
  {
    name: "Production App",
    url: "https://app.green-cloud.uk",
    description: "React frontend + FastAPI backend",
    status: "unknown",
    port: 80,
  },
  {
    name: "GreenCloud API",
    url: "https://api.green-cloud.uk/docs",
    description: "Deployment management and webhooks",
    status: "unknown",
    port: 8000,
  },
  {
    name: "Carbon Engine",
    url: "https://carbon.green-cloud.uk/docs",
    description: "Carbon intensity and emissions tracking",
    status: "unknown",
    port: 8002,
  },
  {
    name: "Grafana",
    url: "https://grafana.green-cloud.uk",
    description: "Metrics dashboards and log viewer",
    status: "unknown",
    port: 3000,
  },
  {
    name: "Prometheus",
    url: "/",
    description: "Metrics collection and alerting",
    status: "unknown",
    port: 9090,
  },
  {
    name: "Docker Registry",
    url: "/",
    description: "Local image storage",
    status: "unknown",
    port: 5000,
  },
];

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

function StatusDot({ status }: { status: string }) {
  const color =
    status === "healthy" || status === "connected"
      ? "#16a34a"
      : status === "unhealthy" || status === "disconnected"
        ? "#dc2626"
        : "#9ca3af";
  return (
    <span
      style={{
        display: "inline-block",
        width: 8,
        height: 8,
        borderRadius: "50%",
        backgroundColor: color,
        marginRight: 6,
      }}
    />
  );
}

function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [carbon, setCarbon] = useState<CarbonStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch health
    fetch("/health")
      .then((res) => res.json())
      .then((data: HealthStatus) => {
        setHealth(data);
        setLoading(false);
      })
      .catch((err: Error) => {
        setError(err.message);
        setLoading(false);
      });

    // Fetch system stats from agent
    fetch("/api/v1/stats")
      .then((res) => res.json())
      .then((data: SystemStats) => setStats(data))
      .catch(() => {});

    // Fetch carbon status
    fetch("/api/v1/carbon")
      .then((res) => res.json())
      .then((data: CarbonStatus) => setCarbon(data))
      .catch(() => {});
  }, []);

  return (
    <div className="dashboard">
      <header className="header">
        <h1>GreenCloud</h1>
        <p className="subtitle">Carbon-aware self-hosted PaaS</p>
      </header>

      {loading && <p className="loading">Loading...</p>}
      {error && <div className="card error">Unable to connect: {error}</div>}

      {/* System Overview */}
      <section className="section">
        <h2>System Overview</h2>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">Status</div>
            <div className="stat-value">
              <StatusDot status={health?.status || "unknown"} />
              {health?.status?.toUpperCase() || "CHECKING"}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Containers</div>
            <div className="stat-value">
              {stats?.containers?.running ?? "--"} running
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-label">CPU</div>
            <div className="stat-value">
              {stats?.cpu_percent != null ? `${stats.cpu_percent}%` : "--"}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Memory</div>
            <div className="stat-value">
              {stats?.memory
                ? `${stats.memory.percent}% (${formatBytes(stats.memory.used_bytes)} / ${formatBytes(stats.memory.total_bytes)})`
                : "--"}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Disk</div>
            <div className="stat-value">
              {stats?.disk
                ? `${stats.disk.percent}% (${formatBytes(stats.disk.used_bytes)} / ${formatBytes(stats.disk.total_bytes)})`
                : "--"}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Carbon</div>
            <div className={`stat-value carbon-${carbon?.status || "unknown"}`}>
              {carbon
                ? `${carbon.carbon_intensity_gco2_kwh.toFixed(0)} gCO\u2082/kWh (${carbon.status.toUpperCase()})`
                : "--"}
            </div>
          </div>
        </div>
      </section>

      {/* Deployed Services */}
      <section className="section">
        <h2>Deployed Services</h2>
        <div className="services-list">
          {SERVICES.map((service) => (
            <div key={service.name} className="service-row">
              <div className="service-info">
                <div className="service-name">{service.name}</div>
                <div className="service-desc">{service.description}</div>
              </div>
              <div className="service-meta">
                <span className="service-port">:{service.port}</span>
                {service.url !== "/" && (
                  <a
                    href={service.url}
                    target="_blank"
                    rel="noopener"
                    className="service-link"
                  >
                    Open &rarr;
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Environment */}
      <section className="section">
        <h2>Environment</h2>
        <div className="env-grid">
          <div className="env-item">
            <span className="env-label">Environment</span>
            <span className="env-value">{health?.environment?.toUpperCase() || "--"}</span>
          </div>
          <div className="env-item">
            <span className="env-label">Database</span>
            <span className="env-value">
              <StatusDot status={health?.database || "unknown"} />
              {health?.database || "--"}
            </span>
          </div>
          <div className="env-item">
            <span className="env-label">Domain</span>
            <span className="env-value">green-cloud.uk</span>
          </div>
        </div>
      </section>

      <footer className="footer">
        <a href="https://github.com/mattygibson/green-cloud" target="_blank" rel="noopener">
          Source on GitHub
        </a>
      </footer>
    </div>
  );
}

export default App;
