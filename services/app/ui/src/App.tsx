import { useEffect, useState } from "react";

interface HealthStatus {
  status: string;
  database: string;
  environment: string;
}

function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/health")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data: HealthStatus) => {
        setHealth(data);
        setLoading(false);
      })
      .catch((err: Error) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return (
    <div className="container">
      <h1>GreenCloud</h1>
      <p className="subtitle">Carbon-aware self-hosted PaaS</p>

      {loading && <p className="status loading">Checking system status...</p>}

      {error && (
        <div className="status error">
          <p>Unable to connect to API</p>
          <code>{error}</code>
        </div>
      )}

      {health && (
        <div className={`status ${health.status}`}>
          <div className="status-row">
            <span className="label">Status:</span>
            <span className={`value ${health.status}`}>{health.status}</span>
          </div>
          <div className="status-row">
            <span className="label">Database:</span>
            <span className={`value ${health.database}`}>
              {health.database}
            </span>
          </div>
          <div className="status-row">
            <span className="label">Environment:</span>
            <span className="value env">{health.environment.toUpperCase()}</span>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
