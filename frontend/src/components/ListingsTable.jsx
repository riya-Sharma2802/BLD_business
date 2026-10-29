export default function ListingsTable({ data, page, pageSize, search, onSearch, onPage, loading }) {
  const { total, items } = data;
  const pages = Math.max(1, Math.ceil(total / pageSize));
  const from = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const to = Math.min(page * pageSize, total);

  return (
    <div className={`table-wrap${loading ? " is-loading" : ""}`}>
      <div className="table-tools">
        <input
          type="search"
          placeholder="Search business name or address…"
          value={search}
          onChange={(e) => onSearch(e.target.value)}
          aria-label="Search listings"
        />
        <span className="table-count">
          {total === 0 ? "No results" : `${from.toLocaleString()}–${to.toLocaleString()} of ${total.toLocaleString()}`}
        </span>
      </div>

      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Business</th>
              <th>Category</th>
              <th>City</th>
              <th>Phone</th>
              <th>Address</th>
            </tr>
          </thead>
          <tbody>
            {items.map((r) => (
              <tr key={r.id}>
                <td className="strong">{r.business_name}</td>
                <td><span className="pill">{r.category}</span></td>
                <td>{r.city}</td>
                <td className="mono">{r.phone || <span className="muted">—</span>}</td>
                <td className="addr">{r.address || <span className="muted">—</span>}</td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={5} className="empty">No listings match the current filters.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="pager">
        <button type="button" onClick={() => onPage(page - 1)} disabled={page <= 1}>← Prev</button>
        <span>Page {page} of {pages.toLocaleString()}</span>
        <button type="button" onClick={() => onPage(page + 1)} disabled={page >= pages}>Next →</button>
      </div>
    </div>
  );
}
