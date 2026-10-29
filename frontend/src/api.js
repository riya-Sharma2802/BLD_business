const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

function query(params = {}) {
  const u = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") u.set(k, v);
  });
  const s = u.toString();
  return s ? `?${s}` : "";
}

async function get(path, params) {
  const res = await fetch(`${BASE}${path}${query(params)}`);
  if (!res.ok) throw new Error(`API ${path} failed (${res.status})`);
  return res.json();
}


export const fetchDashboard = async ({ city, category, source }) => {
  const [summary, cities, categories, sources] = await Promise.all([
    get("/api/dashboard/summary", { city, category, source }),
    get("/api/dashboard/city-wise", { category, source }),
    get("/api/dashboard/category-wise", { city, source }),
    get("/api/dashboard/source-wise", { city, category }),
  ]);
  return { summary, cities, categories, sources };
};

export const fetchListings = (params) => get("/api/listings", params);