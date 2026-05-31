import React from 'react';
import './Cards.css';

export default function EscalationBanner() {
  return (
    <div className="escalation-banner">
      <div className="escalation-icon">⚠️</div>
      <div className="escalation-text">
        <strong>Safety Concern Detected</strong>
        <p>
          Please stop using the appliance immediately and contact PartSelect support at{' '}
          <a href="tel:18887384871">1-888-738-4871</a>, or call a licensed technician.
        </p>
      </div>
    </div>
  );
}
