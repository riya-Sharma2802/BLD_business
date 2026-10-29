import { useEffect, useRef, useState } from "react";
import { fetchDashboard, fetchListings } from "./api.js";
import { DonutChart, HBarChart, VBarChart } from "./components/Charts.jsx";
import ListingsTable from "./components/ListingsTable.jsx";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const PAGE_SIZE = 10;
const EMPTY_FILTERS = { city: "", category: "", source: "" };
const FILTER_LABELS = { city: "City", category: "Category", source: "Source" };

const STATS = [
  { key: "total_listings", label: "Total listings", icon: "🏢", tone: "indigo" },
  { key: "total_cities", label: "Cities", icon: "📍", tone: "pink" },
  { key: "total_categories", label: "Categories", icon: "🗂️", tone: "amber" },
  { key: "total_sources", label: "Data sources", icon: "🔗", tone: "cyan" },
  { key: "with_phone", label: "With phone number", icon: "📞", tone: "green" },
];

/* ---------- small hooks ---------- */
function useDebounced(value, ms) {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return v;
}

function useCountUp(target, ms = 700) {
  const [n, setN] = useState(target);
  const from = useRef(target);
  useEffect(() => {
    const start = from.current;
    if (start === target) return;
    let raf;
    const t0 = performance.now();
    const tick = (t) => {
      const k = Math.min(1, (t - t0) / ms);
      const eased = 1 - Math.pow(1 - k, 3);
      setN(Math.round(start + (target - start) * eased));
      if (k < 1) raf = requestAnimationFrame(tick);
      else from.current = target;
    };
    raf = requestAnimationFrame(tick);
    return () => {
      cancelAnimationFrame(raf);
      from.current = target;
    };
  }, [target, ms]);
  return n;
}

function useTheme() {
  const [theme, setTheme] = useState(() => {
    try {
      const saved = localStorage.getItem("theme");
      if (saved) return saved;
    } catch { /* storage unavailable */ }
    return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem("theme", theme); } catch { /* ignore */ }
  }, [theme]);
  return [theme, () => setTheme((t) => (t === "dark" ? "light" : "dark"))];
}

/* ---------- presentational pieces ---------- */
function StatCard({ icon, tone, label, value, note }) {
  const shown = useCountUp(value);
  return (
    <div className={`stat tone-${tone}`}>
      <div className="stat-icon">{icon}</div>
      <div>
        <div className="stat-value">{shown.toLocaleString()}</div>
        <div className="stat-label">{label}</div>
        {note && <div className="stat-note">{note}</div>}
      </div>
    </div>
  );
}

function Insight({ title, items }) {
  if (!items?.length) return null;
  const total = items.reduce((sum, i) => sum + i.count, 0); // share of *this* chart
  const top = items[0];
  const tied = items.filter((i) => i.count === top.count).length;
  const isTie = items.length > 1 && tied > 1;
  return (
    <div className="insight">
      <div className="insight-title">{title}</div>
      <div className="insight-name">{isTie ? `${tied}-way tie` : top.label}</div>
      <div className="insight-meta">
        {isTie
          ? `${tied} of ${items.length} are equal at ${top.count.toLocaleString()} listings`
          : `${top.count.toLocaleString()} listings · ${total ? ((top.count / total) * 100).toFixed(1) : 0}%`}
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

/* ---------- app ---------- */
export default function App() {
  const [theme, toggleTheme] = useTheme();
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [tick, setTick] = useState(0); // bump to force a refresh

  const [data, setData] = useState(null);
  const [listings, setListings] = useState({ total: 0, items: [] });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tableLoading, setTableLoading] = useState(false);
  const [updated, setUpdated] = useState(null);

  const debouncedSearch = useDebounced(search, 300);
  const active = Object.entries(filters).filter(([, v]) => v);

  // charts + cards
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchDashboard(filters)
      .then((d) => {
        if (cancelled) return;
        setData(d);
        setUpdated(new Date());
      })
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));
    return () => { cancelled = true; };
  }, [filters, tick]);

  // table
  useEffect(() => {
    let cancelled = false;
    setTableLoading(true);
    fetchListings({ ...filters, search: debouncedSearch, page, page_size: PAGE_SIZE })
      .then((d) => !cancelled && setListings(d))
      .catch(() => {})
      .finally(() => !cancelled && setTableLoading(false));
    return () => { cancelled = true; };
  }, [filters, debouncedSearch, page, tick]);

  const toggleFilter = (key) => (value) => {
    setFilters((f) => ({ ...f, [key]: f[key] === value ? "" : value }));
    setPage(1);
  };
  const clearFilters = () => { setFilters(EMPTY_FILTERS); setPage(1); };
  const onSearch = (v) => { setSearch(v); setPage(1); };

  const total = data?.summary.total_listings ?? 0;
  const phonePct = total ? Math.round((data.summary.with_phone / total) * 100) : 0;
  const filteredTitle = active.length ? active.map(([, v]) => v).join(" · ") : null;

  return (
    <>
      <div className="hero">
        <div className="hero-inner">
          <div>
            <span className="badge">Live from MySQL · FastAPI</span>
            <h1>Business Listings Dashboard</h1>
            <p>Click any bar or slice to explore: every chart, card and the table below follow your selection.</p>
          </div>
          <div className="hero-actions">
            <div className="hero-buttons">
              <button className="ghost" onClick={toggleTheme} aria-label="Toggle theme" title="Toggle light / dark">
                {theme === "dark" ? "☀️" : "🌙"}
              </button>
              <button onClick={() => setTick((t) => t + 1)} disabled={loading}>
                <span className={loading ? "spin" : ""}>↻</span> {loading ? "Loading" : "Refresh"}
              </button>
            </div>
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

        {!data && loading && !error && <Skeleton />}

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
                  note={s.key === "with_phone" ? `${phonePct}% of listings` : null}
                />
              ))}
            </div>

            <div className={`filterbar${active.length ? " on" : ""}`}>
              {active.length === 0 ? (
                <span className="hint">💡 Tip: click a city, category or source to filter everything.</span>
              ) : (
                <>
                  <span className="filter-label">Filtering by</span>
                  {active.map(([key, value]) => (
                    <button key={key} className="chip" onClick={() => toggleFilter(key)(value)} title="Remove filter">
                      <span className="chip-key">{FILTER_LABELS[key]}</span> {value} <span className="chip-x">✕</span>
                    </button>
                  ))}
                  <button className="link" onClick={clearFilters}>Clear all</button>
                </>
              )}
            </div>

            <div className="insights">
              <Insight title="🏆 Top city" items={data.cities} />
              <Insight title="⭐ Top category" items={data.categories} />
              <Insight title="🔥 Top source" items={data.sources} />
            </div>

            <div className="grid">
              <Card
                title="City-wise count"
                subtitle={filters.city ? `Selected: ${filters.city}. Click it again to clear.` : "Listings per city. Click a bar to see its categories and sources."}
                wide
              >
                <VBarChart data={data.cities} selected={filters.city} onSelect={toggleFilter("city")} />
              </Card>
              <Card
                title="Source-wise count"
                subtitle={filters.source ? `Selected: ${filters.source}` : "Share of listings by data source"}
              >
                <DonutChart data={data.sources} selected={filters.source} onSelect={toggleFilter("source")} />
              </Card>
              <Card
                title="Category-wise count"
                subtitle={filters.category ? `Selected: ${filters.category}` : "Listings per business category"}
              >
                <HBarChart data={data.categories} selected={filters.category} onSelect={toggleFilter("category")} />
              </Card>
              <Card
                title="Listings"
                subtitle={filteredTitle ? `Businesses matching: ${filteredTitle}` : "Browse and search all collected businesses"}
                wide
              >
                <ListingsTable
                  data={listings}
                  page={page}
                  pageSize={PAGE_SIZE}
                  search={search}
                  onSearch={onSearch}
                  onPage={setPage}
                  loading={tableLoading}
                />
              </Card>
            </div>

            <footer>
              {data.sources.some((s) => /sample/i.test(s.label))
                ? "Data shown includes a sample dataset (sources marked “sample”), loaded into MySQL via the bulk-insert API."
                : "Business data © OpenStreetMap contributors (ODbL), loaded into MySQL via the bulk-insert API."}
            </footer>
          </>
        )}
      </main>
    </>
  );
}
