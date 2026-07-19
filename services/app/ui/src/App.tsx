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
  healthUrl: string;
  status: "healthy" | "unhealthy" | "unknown";
  internal: boolean;
}

interface UserApp {
  name: string;
  url: string;
  health_url: string;
  status: string;
  container_name: string;
}

interface AppsResponse {
  apps: UserApp[];
  count: number;
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
    name: "GreenCloud API",
    url: "https://api.green-cloud.uk/docs",
    healthUrl: "https://api.green-cloud.uk/health",
    description: "Deployment management and webhooks",
    status: "unknown",
    internal: false,
  },
  {
    name: "Carbon Engine",
    url: "https://carbon.green-cloud.uk/docs",
    healthUrl: "https://carbon.green-cloud.uk/health",
    description: "Carbon intensity and emissions tracking",
    status: "unknown",
    internal: false,
  },
  {
    name: "Grafana",
    url: "https://grafana.green-cloud.uk",
    healthUrl: "https://grafana.green-cloud.uk/api/health",
    description: "Metrics dashboards and log viewer",
    status: "unknown",
    internal: false,
  },
  {
    name: "Prometheus",
    url: "/",
    healthUrl: "",
    description: "Metrics collection and alerting",
    status: "unknown",
    internal: true,
  },
  {
    name: "Docker Registry",
    url: "/",
    healthUrl: "",
    description: "Local image storage",
    status: "unknown",
    internal: true,
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

function InternalBadge() {
  return (
    <span className="internal-badge">Internal</span>
  );
}

// Determine URLs based on current hostname
function getBaseUrl(): string {
  const host = window.location.hostname;
  if (host === "app.localhost" || host === "localhost") {
    return "http://localhost";
  }
  return "https://green-cloud.uk";
}

function getCarbonUrl(): string {
  const host = window.location.hostname;
  if (host === "app.localhost" || host === "localhost") {
    return "http://carbon.localhost/carbon/status";
  }
  return "https://carbon.green-cloud.uk/carbon/status";
}

function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [carbon, setCarbon] = useState<CarbonStatus | null>(null);
  const [services, setServices] = useState<Service[]>(SERVICES);
  const [userApps, setUserApps] = useState<UserApp[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
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

    fetch("/api/v1/stats")
      .then((res) => res.json())
      .then((data: SystemStats) => setStats(data))
      .catch(() => {});

    fetch(getCarbonUrl())
      .then((res) => res.json())
      .then((data: CarbonStatus) => setCarbon(data))
      .catch(() => {});

    // Fetch running user apps
    const apiBase = window.location.hostname.includes("localhost")
      ? "http://api.localhost"
      : "https://api.green-cloud.uk";
    fetch(`${apiBase}/api/v1/apps`)
      .then((res) => res.json())
      .then((data: AppsResponse) => setUserApps(data.apps))
      .catch(() => {});

    SERVICES.forEach((service, index) => {
      if (!service.healthUrl) return;
      fetch(service.healthUrl, { mode: "no-cors" })
        .then(() => {
          setServices((prev) => {
            const updated = [...prev];
            updated[index] = { ...updated[index], status: "healthy" };
            return updated;
          });
        })
        .catch(() => {
          setServices((prev) => {
            const updated = [...prev];
            updated[index] = { ...updated[index], status: "unhealthy" };
            return updated;
          });
        });
    });
  }, []);

  const healthyCount = services.filter((s) => s.status === "healthy").length;
  const checkableCount = services.filter((s) => s.healthUrl).length;

  return (
    <div className="dashboard">
      <header className="header">
        <a href={getBaseUrl()} className="logo-link">
          <span className="logo">&#127793;</span>
        </a>
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
            <div className="stat-label">Services</div>
            <div className="stat-value">
              {healthyCount}/{checkableCount} healthy
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
              {carbon && carbon.status !== "unknown"
                ? `${carbon.carbon_intensity_gco2_kwh.toFixed(0)} gCO\u2082/kWh (${carbon.status.toUpperCase()})`
                : "--"}
            </div>
          </div>
        </div>
      </section>

      {/* User Apps */}
      {userApps.length > 0 && (
        <section className="section">
          <h2>Hosted Applications</h2>
          <div className="services-list">
            {userApps.map((app) => (
              <div key={app.container_name} className="service-row app-row">
                <div className="service-info">
                  <StatusDot status={app.status} />
                  <div>
                    <div className="service-name">{app.name}</div>
                    <div className="service-desc">{app.container_name}</div>
                  </div>
                </div>
                <div className="service-meta">
                  <span className="app-badge">App</span>
                  <a
                    href={app.url}
                    target="_blank"
                    rel="noopener"
                    className="service-link"
                  >
                    Visit &rarr;
                  </a>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Deployed Services */}
      <section className="section">
        <h2>Deployed Services</h2>
        <div className="services-list">
          {services.map((service) => (
            <div key={service.name} className="service-row">
              <div className="service-info">
                {service.internal ? <InternalBadge /> : <StatusDot status={service.status} />}
                <div>
                  <div className="service-name">{service.name}</div>
                  <div className="service-desc">{service.description}</div>
                </div>
              </div>
              <div className="service-meta">
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
