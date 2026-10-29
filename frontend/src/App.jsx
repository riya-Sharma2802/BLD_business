import { useEffect, useState } from "react";
import { fetchDashboard } from "./api.js";
import { DonutChart, HBarChart, VBarChart } from "./components/Charts.jsx";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const STATS = [
  { key: "total_listings", label: "Total listings", icon: "🏢", tone: "indigo" },
  { key: "total_cities", label: "Cities covered", icon: "📍", tone: "pink" },
  { key: "total_categories", label: "Categories", icon: "🗂️", tone: "amber" },
  { key: "total_sources", label: "Data sources", icon: "🔗", tone: "cyan" },
  { key: "with_phone", label: "With phone number", icon: "📞", tone: "green" },
];

function StatCard({ icon, tone, label, value, note }) {
  return (
    <div className={`stat tone-${tone}`}>
      <div className="stat-icon">{icon}</div>
      <div>
        <div className="stat-value">{value.toLocaleString()}</div>
        <div className="stat-label">{label}</div>
        {note && <div className="stat-note">{note}</div>}
      </div>
    </div>
  );
}

function Insight({ title, item, total }) {
  if (!item) return null;
  return (
    <div className="insight">
      <div className="insight-title">{title}</div>
      <div className="insight-name">{item.label}</div>
      <div className="insight-meta">
        {item.count.toLocaleString()} listings · {((item.count / total) * 100).toFixed(1)}%
      </div>
    </div>
  );
}

function Card({ title, subtitle, children, wide }) {
  return (
    <section className={`card${wide ? " wide" : ""}`}>
      <div className="card-head">
        <h2>{title}</h2>
        <p>{subtitle}</p>
      </div>
      {children}
    </section>
  );
}

function Skeleton() {
  return (
    <>
      <div className="stats">
        {[...Array(5)].map((_, i) => <div key={i} className="skeleton stat-skel" />)}
      </div>
      <div className="grid">
        <div className="skeleton chart-skel wide" />
        <div className="skeleton chart-skel" />
        <div className="skeleton chart-skel" />
      </div>
    </>
  );
}

export default function App() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updated, setUpdated] = useState(null);

  const load = () => {
    setLoading(true);
    setError(null);
    fetchDashboard()
      .then((d) => {
        setData(d);
        setUpdated(new Date());
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };
  useEffect(load, []);

  const total = data?.summary.total_listings ?? 0;
  const phonePct = total ? Math.round((data.summary.with_phone / total) * 100) : 0;

  return (
    <>
      <div className="hero">
        <div className="hero-inner">
          <div>
            <span className="badge">Live from MySQL · FastAPI</span>
            <h1>Business Listings Dashboard</h1>
            <p>City, category and source insights across all collected business listings.</p>
          </div>
          <div className="hero-actions">
            <button onClick={load} disabled={loading}>
              <span className={loading ? "spin" : ""}>↻</span> {loading ? "Loading" : "Refresh"}
            </button>
            {updated && <span className="updated">Updated {updated.toLocaleTimeString()}</span>}
          </div>
        </div>
      </div>

      <main className="container">
        {error && (
          <div className="notice error">
            <strong>Could not load data.</strong> {error}. Is the API running on {API_URL}?
          </div>
        )}

        {loading && !data && !error && <Skeleton />}

        {data && (
          <>
            <div className="stats">
              {STATS.map((s) => (
                <StatCard
                  key={s.key}
                  icon={s.icon}
                  tone={s.tone}
                  label={s.label}
                  value={data.summary[s.key]}
                  note={s.key === "with_phone" ? `${phonePct}% of all listings` : null}
                />
              ))}
            </div>

            <div className="insights">
              <Insight title="🏆 Top city" item={data.cities[0]} total={total} />
              <Insight title="⭐ Top category" item={data.categories[0]} total={total} />
              <Insight title="🔥 Top source" item={data.sources[0]} total={total} />
            </div>

            <div className="grid">
              <Card title="City-wise count" subtitle="Number of listings per city (top city highlighted)" wide>
                <VBarChart data={data.cities} />
              </Card>
              <Card title="Source-wise count" subtitle="Share of listings by data source">
                <DonutChart data={data.sources} />
              </Card>
              <Card title="Category-wise count" subtitle="Listings per business category">
                <HBarChart data={data.categories} />
              </Card>
            </div>

            <footer>
              Data shown is a sample dataset (sources marked “sample”), loaded into MySQL via the bulk-insert API.
            </footer>
          </>
        )}
      </main>
    </>
  );
}
