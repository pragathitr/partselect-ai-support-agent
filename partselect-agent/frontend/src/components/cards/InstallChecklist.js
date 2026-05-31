import React, { useState } from 'react';
import './Cards.css';

export default function InstallChecklist({ data }) {
  const { part_number, steps = [] } = data;
  const [checked, setChecked] = useState({});

  const toggle = (i) =>
    setChecked((prev) => ({ ...prev, [i]: !prev[i] }));

  return (
    <div className="card install-checklist">
      <div className="card-title">
        Installation Guide{part_number ? ` — ${part_number}` : ''}
      </div>
      <ol className="install-steps">
        {steps.map((step, i) => (
          <li
            key={i}
            className={`install-step ${checked[i] ? 'done' : ''}`}
            onClick={() => toggle(i)}
          >
            <input
              type="checkbox"
              checked={!!checked[i]}
              onChange={() => toggle(i)}
              onClick={(e) => e.stopPropagation()}
            />
            <div className="install-step-text">
              {step.title && <strong>{step.title}</strong>}
              <p>{step.description || step.instruction}</p>
              {step.tool_required && (
                <div className="install-step-meta">Tool: {step.tool_required}</div>
              )}
              {step.safety_note && (
                <div className="install-step-safety">{step.safety_note}</div>
              )}
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
