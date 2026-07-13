import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceArea,
  ReferenceLine,
  Scatter,
} from 'recharts';
import { colorFor } from '../categoryColors';

const toTs = (dateStr) => new Date(dateStr).getTime();

function formatTick(ts) {
  const d = new Date(ts);
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
}

// Find the price-series entry whose date is closest to a target date string,
// used to vertically position an event marker on (near) the price line.
function nearestPrice(prices, targetDateStr) {
  if (!prices.length) return null;
  const target = toTs(targetDateStr);
  let best = prices[0];
  let bestDiff = Math.abs(toTs(prices[0].date) - target);
  for (const p of prices) {
    const diff = Math.abs(toTs(p.date) - target);
    if (diff < bestDiff) {
      best = p;
      bestDiff = diff;
    }
  }
  return best;
}

function EventDot({ cx, cy, fill, onClick, name }) {
  if (cx == null || cy == null || Number.isNaN(cx) || Number.isNaN(cy)) return null;
  return (
    <path
      d={`M ${cx} ${cy - 8} L ${cx + 7} ${cy + 6} L ${cx - 7} ${cy + 6} Z`}
      fill={fill}
      stroke="#fff"
      strokeWidth={1.2}
      style={{ cursor: 'pointer' }}
      onClick={onClick}
    >
      <title>{name}</title>
    </path>
  );
}

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const pricePoint = payload.find((p) => p.dataKey === 'price');
  if (!pricePoint) return null;
  const d = new Date(pricePoint.payload.ts);
  return (
    <div className="chart-tooltip">
      <div className="tooltip-date">{d.toISOString().slice(0, 10)}</div>
      <div className="tooltip-price">${pricePoint.value?.toFixed(2)}</div>
    </div>
  );
}

export default function PriceChart({ prices, events, highlightWindow, highlightDate, onEventClick }) {
  const chartData = prices.map((p) => ({ ...p, ts: toTs(p.date) }));

  const eventPoints = events
    .map((ev) => {
      const nearest = nearestPrice(prices, ev.start_date);
      if (!nearest) return null;
      return { ...ev, ts: toTs(ev.start_date), price: nearest.price };
    })
    .filter(Boolean);

  const tsDomain = chartData.length
    ? [chartData[0].ts, chartData[chartData.length - 1].ts]
    : ['auto', 'auto'];

  return (
    <div className="price-chart-wrapper">
      <ResponsiveContainer width="100%" height={420}>
        <ComposedChart data={chartData} margin={{ top: 20, right: 20, bottom: 10, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
          <XAxis
            dataKey="ts"
            type="number"
            domain={tsDomain}
            tickFormatter={formatTick}
            tick={{ fontSize: 11 }}
            minTickGap={50}
          />
          <YAxis
            tick={{ fontSize: 11 }}
            tickFormatter={(v) => `$${Math.round(v)}`}
            domain={['dataMin - 5', 'dataMax + 5']}
            width={55}
          />
          <Tooltip content={<CustomTooltip />} />

          {highlightWindow && (
            <ReferenceArea
              x1={toTs(highlightWindow.start)}
              x2={toTs(highlightWindow.end)}
              fill="#B5502A"
              fillOpacity={0.08}
              stroke="none"
            />
          )}

          {highlightDate && (
            <ReferenceLine
              x={toTs(highlightDate)}
              stroke="#B5502A"
              strokeWidth={2}
              strokeDasharray="5 3"
              label={{ value: 'Change point', position: 'insideTopRight', fontSize: 11, fill: '#B5502A' }}
            />
          )}

          <Line
            type="monotone"
            dataKey="price"
            stroke="#1F4E5A"
            strokeWidth={1.4}
            dot={false}
            isAnimationActive={false}
          />

          <Scatter
            data={eventPoints}
            dataKey="price"
            shape={(props) => (
              <EventDot
                {...props}
                fill={colorFor(props.payload.category)}
                name={`${props.payload.event_name} (${props.payload.start_date})`}
                onClick={() => onEventClick?.(props.payload)}
              />
            )}
          />
        </ComposedChart>
      </ResponsiveContainer>
      <p className="chart-hint">Click a triangle marker to zoom into that event's window.</p>
    </div>
  );
}
