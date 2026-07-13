import { ALL_CATEGORIES, colorFor } from '../categoryColors';

export default function Filters({
  dateRange,
  onDateRangeChange,
  freq,
  onFreqChange,
  activeCategories,
  onToggleCategory,
  onReset,
  minDate,
  maxDate,
}) {
  return (
    <div className="filters-panel">
      <h3>Filters</h3>

      <div className="filter-group">
        <label className="filter-label">Date range</label>
        <div className="date-inputs">
          <input
            type="date"
            value={dateRange.start}
            min={minDate}
            max={dateRange.end}
            onChange={(e) => onDateRangeChange({ ...dateRange, start: e.target.value })}
          />
          <span className="date-sep">to</span>
          <input
            type="date"
            value={dateRange.end}
            min={dateRange.start}
            max={maxDate}
            onChange={(e) => onDateRangeChange({ ...dateRange, end: e.target.value })}
          />
        </div>
      </div>

      <div className="filter-group">
        <label className="filter-label">Resolution</label>
        <select value={freq} onChange={(e) => onFreqChange(e.target.value)}>
          <option value="D">Daily</option>
          <option value="W">Weekly average</option>
          <option value="M">Monthly average</option>
        </select>
      </div>

      <div className="filter-group">
        <label className="filter-label">Event categories</label>
        <div className="category-list">
          {ALL_CATEGORIES.map((cat) => (
            <label className="category-checkbox" key={cat}>
              <input
                type="checkbox"
                checked={activeCategories.has(cat)}
                onChange={() => onToggleCategory(cat)}
              />
              <span className="category-swatch" style={{ background: colorFor(cat) }} />
              {cat}
            </label>
          ))}
        </div>
      </div>

      <button className="reset-btn" onClick={onReset}>
        Reset filters
      </button>
    </div>
  );
}
