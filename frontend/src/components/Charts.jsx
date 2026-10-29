import {
  Bar, BarChart, CartesianGrid, Cell, LabelList, Pie, PieChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";

export const PALETTE = [
  "#f59e0b", "#6366f1", "#10b981", "#ec4899", "#06b6d4", "#f97316", "#8b5cf6",
  "#14b8a6", "#ef4444", "#3b82f6", "#84cc16", "#a855f7", "#eab308", "#64748b",
];

const AXIS = "var(--axis)";
const GRID = "var(--grid)";
const DIM = 0.28; // opacity of bars that are not selected

const labelOf = (entry) => entry?.payload?.label ?? entry?.label ?? entry?.name;

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
      <div className="tooltip-hint">Click to filter</div>
    </div>
  );
}

const opacityFor = (selected, label) => (selected && selected !== label ? DIM : 1);

/** City-wise: vertical gradient bars. Click a bar to filter the whole dashboard. */
export function VBarChart({ data, selected, onSelect }) {
  const total = data.reduce((s, d) => s + d.count, 0);
  const max = Math.max(...data.map((d) => d.count), 0);
  const topCount = data.filter((d) => d.count === max).length;
  const uniqueTop = topCount === 1;
  return (
    <ResponsiveContainer width="100%" height={330}>
      <BarChart data={data} margin={{ top: 24, right: 8, left: -14, bottom: 0 }}>
        <defs>
          <linearGradient id="gCity" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#fcd34d" />
            <stop offset="100%" stopColor="#d97706" />
          </linearGradient>
          <linearGradient id="gCityTop" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#fb923c" />
            <stop offset="100%" stopColor="#c2410c" />
          </linearGradient>
          <linearGradient id="gCitySel" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#818cf8" />
            <stop offset="100%" stopColor="#4338ca" />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID} />
        <XAxis
          dataKey="label"
          tick={{ fontSize: 12, fill: AXIS }}
          interval={0}
          angle={-30}
          textAnchor="end"
          height={62}
          axisLine={false}
          tickLine={false}
        />
        <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: AXIS }} axisLine={false} tickLine={false} />
        <Tooltip content={<ChartTooltip total={total} />} cursor={{ fill: "rgba(245,158,11,0.10)" }} />
        <Bar
          dataKey="count"
          name="Listings"
          radius={[8, 8, 0, 0]}
          maxBarSize={46}
          animationDuration={800}
          cursor="pointer"
          onClick={(entry) => onSelect(labelOf(entry))}
        >
          {data.map((d) => {
            const isSel = selected === d.label;
            const fill = isSel ? "url(#gCitySel)" : uniqueTop && d.count === max ? "url(#gCityTop)" : "url(#gCity)";
            return <Cell key={d.label} fill={fill} fillOpacity={opacityFor(selected, d.label)} />;
          })}
          <LabelList dataKey="count" position="top" style={{ fontSize: 11, fill: AXIS, fontWeight: 600 }} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

/** Category-wise: horizontal bars (long labels read better). */
export function HBarChart({ data, selected, onSelect }) {
  const total = data.reduce((s, d) => s + d.count, 0);
  const height = Math.max(280, data.length * 34 + 20);
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ left: 4, right: 40, top: 4, bottom: 0 }}>
        <defs>
          <linearGradient id="gCat" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#818cf8" />
            <stop offset="100%" stopColor="#3730a3" />
          </linearGradient>
          <linearGradient id="gCatSel" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#fcd34d" />
            <stop offset="100%" stopColor="#d97706" />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke={GRID} />
        <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12, fill: AXIS }} axisLine={false} tickLine={false} />
        <YAxis
          type="category"
          dataKey="label"
          width={150}
          tick={{ fontSize: 12, fill: "var(--text)" }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip content={<ChartTooltip total={total} />} cursor={{ fill: "rgba(99,102,241,0.08)" }} />
        <Bar
          dataKey="count"
          name="Listings"
          radius={[0, 8, 8, 0]}
          barSize={18}
          animationDuration={800}
          cursor="pointer"
          onClick={(entry) => onSelect(labelOf(entry))}
        >
          {data.map((d) => (
            <Cell
              key={d.label}
              fill={selected === d.label ? "url(#gCatSel)" : "url(#gCat)"}
              fillOpacity={opacityFor(selected, d.label)}
            />
          ))}
          <LabelList dataKey="count" position="right" style={{ fontSize: 11, fill: AXIS, fontWeight: 600 }} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

/** Source-wise: donut with the total in the middle and a clickable legend. */
export function DonutChart({ data, selected, onSelect }) {
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
              animationDuration={800}
              cursor="pointer"
              onClick={(entry) => onSelect(labelOf(entry))}
            >
              {data.map((d, i) => (
                <Cell key={d.label} fill={PALETTE[i % PALETTE.length]} fillOpacity={opacityFor(selected, d.label)} />
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
            <button
              type="button"
              className={`legend-btn${selected === d.label ? " active" : ""}`}
              onClick={() => onSelect(d.label)}
            >
              <span className="dot" style={{ background: PALETTE[i % PALETTE.length] }} />
              <span className="legend-label">{d.label}</span>
              <span className="legend-count">{d.count.toLocaleString()}</span>
              <span className="legend-pct">{total ? ((d.count / total) * 100).toFixed(0) : 0}%</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
