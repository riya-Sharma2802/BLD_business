const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function get(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`API ${path} failed (${res.status})`);
  return res.json();
}

export const fetchDashboard = async () => {
  const [summary, cities, categories, sources] = await Promise.all([
    get("/api/dashboard/summary"),
    get("/api/dashboard/city-wise"),
    get("/api/dashboard/category-wise"),
    get("/api/dashboard/source-wise"),
  ]);
  return { summary, cities, categories, sources };
};
