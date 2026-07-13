export default function KpiCards({ metrics }) {
  if (!metrics) return null;

  const cards = [
    {
      label: 'Date Range',
      value: `${metrics.date_range?.[0]} to ${metrics.date_range?.[1]}`,
      sub: `${metrics.n_observations?.toLocaleString()} daily observations`,
    },
    {
      label: 'Average Price',
      value: `$${metrics.overall_mean_price?.toFixed(2)}`,
      sub: 'per barrel, full history',
    },
    {
      label: 'Avg. Daily Volatility',
      value: `${(metrics.overall_price_volatility_30d_avg * 100).toFixed(2)}%`,
      sub: '30-day rolling std. of log returns',
    },
    {
      label: 'All-Time High',
      value: `$${metrics.max_price?.toFixed(2)}`,
      sub: metrics.max_price_date,
    },
    {
      label: 'All-Time Low',
      value: `$${metrics.min_price?.toFixed(2)}`,
      sub: metrics.min_price_date,
    },
  ];

  return (
    <div className="kpi-grid">
      {cards.map((c) => (
        <div className="kpi-card" key={c.label}>
          <div className="kpi-label">{c.label}</div>
          <div className="kpi-value">{c.value}</div>
          <div className="kpi-sub">{c.sub}</div>
        </div>
      ))}
    </div>
  );
}
