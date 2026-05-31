import React from 'react';
import './Cards.css';

const STATUS_LABELS = {
  confirmed: 'Confirmed Compatible',
  likely:    'Likely Compatible',
  unknown:   'Compatibility Unknown',
};

export default function CompatBadge({ data }) {
  const { part_number, model_number, status, compatible } = data;

  const label = STATUS_LABELS[status] || (compatible ? 'Compatible' : 'Incompatible');
  const cls   = compatible ? 'compat-yes' : 'compat-no';
  const icon  = compatible ? '✓' : '✗';

  return (
    <div className="card compat-badge-card">
      {model_number && <span className="compat-model">{model_number}</span>}
      {part_number  && <span className="part-number">{part_number}</span>}
      <span className={`compat-status ${cls}`}>{icon} {label}</span>
    </div>
  );
}
