import React from 'react';
import './Cards.css';

export default function TroubleshootCard({ data = [] }) {
  if (!data.length) return null;

  const symptomDesc = data[0]?.symptom_description || 'Symptom diagnosis';

  return (
    <div className="card troubleshoot-card">
      <div className="card-title">Diagnosis: {symptomDesc}</div>
      <div className="troubleshoot-parts">
        {data.map((fix, i) => (
          <div key={i} className="troubleshoot-part">
            <span className="rank-badge">#{fix.rank}</span>
            <span className="part-info">
              {fix.part_name}{' '}
              <span className="part-num">({fix.part_number})</span>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
