import React from 'react';
import './Cards.css';

export default function ValidatorBadge({ verdict }) {
  if (!verdict || verdict === 'escalate') return null;

  if (verdict === 'pass') {
    return <div className="validator-badge pass">✓ Response verified</div>;
  }

  return (
    <div className="validator-badge warn">
      ⚠ We recommend confirming compatibility with your model number before ordering.
    </div>
  );
}
