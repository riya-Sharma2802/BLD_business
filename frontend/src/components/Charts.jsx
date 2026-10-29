
import {
  Bar, BarChart, CartesianGrid, Cell, LabelList, Pie, PieChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";

export const PALETTE = [
  "#f59e0b", "#4f46e5", "#10b981", "#ec4899", "#06b6d4", "#f97316", "#8b5cf6",
  "#14b8a6", "#ef4444", "#3b82f6", "#84cc16", "#a855f7", "#eab308", "#64748b",
];

const AXIS = "#64748b";
const GRID = "#e8ecf4";

function ChartTooltip({ active, payload, label, total }) {
  if (!active || !payload?.length) return null;
  const p = payload[0];
  const name = label ?? p.name;
  const pct = total ? ` · ${((p.value / total) * 100).toFixed(1)}%` : "";
  return (
    <div className="tooltip">
      <div className="tooltip-title">{name}</div>
      <div className="tooltip-value">
        {p.value.toLocaleString()} listings{pct}
      </div>
    </div>
  );
}

/** City-wise: vertical gradient bars with value labels. */
export function VBarChart({ data }) {
  const total = data.reduce((s, d) => s + d.count, 0);
  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={data} margin={{ top: 22, right: 8, left: -18, bottom: 0 }}>
        <defs>
          <linearGradient id="gCity" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#fcd34d" />
            <stop offset="100%" stopColor="#d97706" />
          </linearGradient>
          <linearGradient id="gCityTop" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#fb923c" />
            <stop offset="100%" stopColor="#c2410c" />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID} />
        <XAxis
          dataKey="label"
          tick={{ fontSize: 12, fill: AXIS }}
          interval={0}
          angle={-30}
          textAnchor="end"
          height={60}
          axisLine={false}
          tickLine={false}
        />
        <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: AXIS }} axisLine={false} tickLine={false} />
        <Tooltip content={<ChartTooltip total={total} />} cursor={{ fill: "rgba(245,158,11,0.10)" }} />
        <Bar dataKey="count" name="Listings" radius={[8, 8, 0, 0]} maxBarSize={44} animationDuration={900}>
          {data.map((_, i) => (
            <Cell key={i} fill={i === 0 ? "url(#gCityTop)" : "url(#gCity)"} />
          ))}
          <LabelList dataKey="count" position="top" style={{ fontSize: 11, fill: AXIS, fontWeight: 600 }} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

/** Category-wise: horizontal gradient bars (long labels read better). */
export function HBarChart({ data }) {
  const total = data.reduce((s, d) => s + d.count, 0);
  const height = Math.max(260, data.length * 34 + 20);
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ left: 4, right: 36, top: 4, bottom: 0 }}>
        <defs>
          <linearGradient id="gCat" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#818cf8" />
            <stop offset="100%" stopColor="#3730a3" />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke={GRID} />
        <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12, fill: AXIS }} axisLine={false} tickLine={false} />
        <YAxis
          type="category"
          dataKey="label"
          width={150}
          tick={{ fontSize: 12, fill: "#334155" }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip content={<ChartTooltip total={total} />} cursor={{ fill: "rgba(79,70,229,0.08)" }} />
        <Bar dataKey="count" name="Listings" fill="url(#gCat)" radius={[0, 8, 8, 0]} barSize={18} animationDuration={900}>
          <LabelList dataKey="count" position="right" style={{ fontSize: 11, fill: AXIS, fontWeight: 600 }} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

/** Source-wise: donut with the total in the middle and a custom legend. */
export function DonutChart({ data }) {
  const total = data.reduce((s, d) => s + d.count, 0);
  return (
    <div className="donut">
      <div className="donut-chart">
        <ResponsiveContainer width="100%" height={240}>
          <PieChart>
            <Pie
              data={data}
              dataKey="count"
              nameKey="label"
              innerRadius={72}
              outerRadius={106}
              paddingAngle={3}
              cornerRadius={6}
              stroke="none"
              animationDuration={900}
            >
              {data.map((_, i) => (
                <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
              ))}
            </Pie>
            <Tooltip content={<ChartTooltip total={total} />} />
          </PieChart>
        </ResponsiveContainer>
        <div className="donut-center">
          <div className="donut-total">{total.toLocaleString()}</div>
          <div className="donut-caption">listings</div>
        </div>
      </div>

      <ul className="legend">
        {data.map((d, i) => (
          <li key={d.label}>
            <span className="dot" style={{ background: PALETTE[i % PALETTE.length] }} />
            <span className="legend-label">{d.label}</span>
            <span className="legend-count">{d.count.toLocaleString()}</span>
            <span className="legend-pct">{((d.count / total) * 100).toFixed(0)}%</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
