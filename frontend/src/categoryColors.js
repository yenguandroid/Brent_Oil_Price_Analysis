// categoryColors.js — shared color mapping for event categories,
// used by both the chart markers and the filter legend so colors stay in sync.

export const CATEGORY_COLORS = {
  'Geopolitical Conflict': '#B5502A',
  'OPEC Decision': '#1F4E5A',
  'Economic Shock': '#8E44AD',
  'Market Price Extreme': '#3D8361',
  'Sanctions / Policy': '#C79A00',
};

export const ALL_CATEGORIES = Object.keys(CATEGORY_COLORS);

export function colorFor(category) {
  return CATEGORY_COLORS[category] || '#666666';
}
