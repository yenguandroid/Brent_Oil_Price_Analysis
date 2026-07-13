function fmtMoney(v) {
  return `$${Number(v).toFixed(2)}`;
}

export default function ChangePointPanel({ changepoints, volatility, selectedName, onSelect, onSelectVolatility, volatilitySelected }) {
  return (
    <div className="cp-panel">
      <h3>Detected Change Points</h3>
      <p className="cp-intro">
        Each row is a Bayesian change point model fit (PyMC). Click "View" to zoom the
        chart to that window and highlight the detected break.
      </p>
      <div className="cp-table-scroll">
        <table className="cp-table">
          <thead>
            <tr>
              <th>Event / Window</th>
              <th>Change Point</th>
              <th>Before</th>
              <th>After</th>
              <th>% Change</th>
              <th>r&#770;</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {changepoints.map((cp) => (
              <tr key={cp.name} className={selectedName === cp.name ? 'cp-row-active' : ''}>
                <td>{cp.name}</td>
                <td>{cp.change_point_date}</td>
                <td>{fmtMoney(cp.before_mean)}</td>
                <td>{fmtMoney(cp.after_mean)}</td>
                <td className={cp.pct_change >= 0 ? 'pct-up' : 'pct-down'}>
                  {cp.pct_change >= 0 ? '+' : ''}
                  {cp.pct_change}%
                </td>
                <td>{cp.r_hat_tau}</td>
                <td>
                  <button className="view-btn" onClick={() => onSelect(cp)}>
                    View
                  </button>
                </td>
              </tr>
            ))}
            {volatility && (
              <tr className={volatilitySelected ? 'cp-row-active' : ''}>
                <td>{volatility.name}</td>
                <td>{volatility.change_point_date}</td>
                <td>{(volatility.sigma_before * 100).toFixed(2)}% daily vol</td>
                <td>{(volatility.sigma_after * 100).toFixed(2)}% daily vol</td>
                <td className={volatility.pct_change >= 0 ? 'pct-up' : 'pct-down'}>
                  {volatility.pct_change >= 0 ? '+' : ''}
                  {volatility.pct_change}%
                </td>
                <td>{volatility.r_hat_tau}</td>
                <td>
                  <button className="view-btn" onClick={onSelectVolatility}>
                    View
                  </button>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {selectedName && (
        <div className="cp-detail">
          {changepoints
            .filter((cp) => cp.name === selectedName)
            .map((cp) => (
              <div key={cp.name}>
                <strong>{cp.name}:</strong> the model detects a change point around{' '}
                <strong>{cp.change_point_date}</strong> (89% credible interval:{' '}
                {cp.credible_interval[0]} to {cp.credible_interval[1]}), with the average
                daily price shifting from <strong>{fmtMoney(cp.before_mean)}</strong> to{' '}
                <strong>{fmtMoney(cp.after_mean)}</strong>, a{' '}
                {cp.pct_change >= 0 ? 'increase' : 'decrease'} of{' '}
                <strong>{Math.abs(cp.pct_change)}%</strong>.
                {cp.nearby_events?.length > 0 && (
                  <>
                    {' '}
                    Nearest compiled event: <em>{cp.nearby_events[0].event_name}</em> (
                    {cp.nearby_events[0].start_date},{' '}
                    {Math.abs(cp.nearby_events[0].days_from_changepoint)} days{' '}
                    {cp.nearby_events[0].days_from_changepoint < 0 ? 'before' : 'after'} the
                    change point).
                  </>
                )}
              </div>
            ))}
        </div>
      )}
    </div>
  );
}
