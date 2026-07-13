import { useEffect, useMemo, useState } from 'react';
import { fetchPrices, fetchEvents, fetchChangepoints, fetchMetrics } from './api';
import KpiCards from './components/KpiCards';
import Filters from './components/Filters';
import PriceChart from './components/PriceChart';
import ChangePointPanel from './components/ChangePointPanel';
import { ALL_CATEGORIES } from './categoryColors';
import './App.css';

const MIN_DATE = '1987-05-20';
const MAX_DATE = '2022-09-30';
const DEFAULT_RANGE = { start: MIN_DATE, end: MAX_DATE };

export default function App() {
  const [metrics, setMetrics] = useState(null);
  const [allEvents, setAllEvents] = useState([]);
  const [changepointData, setChangepointData] = useState(null);
  const [prices, setPrices] = useState([]);

  const [dateRange, setDateRange] = useState(DEFAULT_RANGE);
  const [freq, setFreq] = useState('W');
  const [activeCategories, setActiveCategories] = useState(new Set(ALL_CATEGORIES));

  const [highlightWindow, setHighlightWindow] = useState(null);
  const [highlightDate, setHighlightDate] = useState(null);
  const [selectedCpName, setSelectedCpName] = useState(null);
  const [volatilitySelected, setVolatilitySelected] = useState(false);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([fetchMetrics(), fetchEvents(), fetchChangepoints()])
      .then(([m, e, cp]) => {
        setMetrics(m);
        setAllEvents(e.data);
        setChangepointData(cp);
      })
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    setLoading(true);
    fetchPrices({ start: dateRange.start, end: dateRange.end, freq })
      .then((res) => setPrices(res.data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [dateRange, freq]);

  const visibleEvents = useMemo(
    () =>
      allEvents.filter(
        (ev) =>
          activeCategories.has(ev.category) &&
          ev.start_date >= dateRange.start &&
          ev.start_date <= dateRange.end
      ),
    [allEvents, activeCategories, dateRange]
  );

  function handleToggleCategory(cat) {
    setActiveCategories((prev) => {
      const next = new Set(prev);
      if (next.has(cat)) next.delete(cat);
      else next.add(cat);
      return next;
    });
  }

  function handleResetFilters() {
    setDateRange(DEFAULT_RANGE);
    setFreq('W');
    setActiveCategories(new Set(ALL_CATEGORIES));
    setHighlightWindow(null);
    setHighlightDate(null);
    setSelectedCpName(null);
    setVolatilitySelected(false);
  }

  function handleEventClick(event) {
    const d = new Date(event.start_date);
    const start = new Date(d);
    start.setDate(start.getDate() - 120);
    const end = new Date(d);
    end.setDate(end.getDate() + 120);

    setDateRange({
      start: clampDate(start.toISOString().slice(0, 10), MIN_DATE, MAX_DATE),
      end: clampDate(end.toISOString().slice(0, 10), MIN_DATE, MAX_DATE),
    });
    setFreq('D');
    setHighlightDate(event.start_date);
    setHighlightWindow(null);
    setSelectedCpName(null);
    setVolatilitySelected(false);
  }

  function handleSelectChangepoint(cp) {
    setSelectedCpName(cp.name);
    setVolatilitySelected(false);
    setHighlightDate(cp.change_point_date);
    if (cp.window) {
      setDateRange({ start: cp.window[0], end: cp.window[1] });
      setHighlightWindow({ start: cp.window[0], end: cp.window[1] });
      setFreq('D');
    } else {
      setDateRange(DEFAULT_RANGE);
      setHighlightWindow(null);
      setFreq('W');
    }
  }

  function handleSelectVolatility() {
    if (!changepointData?.volatility_changepoint) return;
    const v = changepointData.volatility_changepoint;
    setVolatilitySelected(true);
    setSelectedCpName(null);
    setHighlightDate(v.change_point_date);
    setDateRange({ start: '2019-10-01', end: '2020-12-31' });
    setHighlightWindow({ start: '2019-10-01', end: '2020-12-31' });
    setFreq('D');
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>Brent Crude Oil — Change Point Dashboard</h1>
        <p className="app-subtitle">
          Explore how geopolitical events, OPEC decisions, and economic shocks line up
          with structural breaks in Brent oil prices (1987-2022).
        </p>
      </header>

      {error && <div className="error-banner">Couldn't load data: {error}</div>}

      <KpiCards metrics={metrics} />

      <div className="main-grid">
        <aside className="sidebar">
          <Filters
            dateRange={dateRange}
            onDateRangeChange={(r) => {
              setDateRange(r);
              setHighlightWindow(null);
              setHighlightDate(null);
              setSelectedCpName(null);
              setVolatilitySelected(false);
            }}
            freq={freq}
            onFreqChange={setFreq}
            activeCategories={activeCategories}
            onToggleCategory={handleToggleCategory}
            onReset={handleResetFilters}
            minDate={MIN_DATE}
            maxDate={MAX_DATE}
          />
        </aside>

        <section className="chart-section">
          {loading ? (
            <div className="loading-placeholder">Loading price data...</div>
          ) : (
            <PriceChart
              prices={prices}
              events={visibleEvents}
              highlightWindow={highlightWindow}
              highlightDate={highlightDate}
              onEventClick={handleEventClick}
            />
          )}
        </section>
      </div>

      {changepointData && (
        <ChangePointPanel
          changepoints={changepointData.changepoints}
          volatility={changepointData.volatility_changepoint}
          selectedName={selectedCpName}
          volatilitySelected={volatilitySelected}
          onSelect={handleSelectChangepoint}
          onSelectVolatility={handleSelectVolatility}
        />
      )}

      <footer className="app-footer">
        Data: US EIA (Brent spot price), 1987-2022. Change points estimated via Bayesian
        MCMC (PyMC). Alignment with events indicates temporal correlation, not proven
        causation.
      </footer>
    </div>
  );
}

function clampDate(dateStr, min, max) {
  if (dateStr < min) return min;
  if (dateStr > max) return max;
  return dateStr;
}
