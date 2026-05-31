import React from 'react';
import './Cards.css';

export default function ProductCard({ part }) {
  const {
    part_number,
    name,
    price,
    in_stock,
    manufacturer,
    brand,
    oem_number,
    mfr_part_number,
    cart_url,
    quantity,
  } = part;
  const manufacturerName = manufacturer || brand;
  const oemNumber = oem_number || mfr_part_number;
  const cartUrl = cart_url || (
    part_number
      ? `https://www.partselect.com/cart/add?partNumber=${encodeURIComponent(part_number)}&quantity=1`
      : null
  );

  return (
    <div className="card product-card">
      <div className="product-card-header">
        <span className="part-number">{part_number}</span>
        <span className={`badge ${in_stock ? 'in-stock' : 'out-of-stock'}`}>
          {in_stock ? 'In Stock' : 'Out of Stock'}
        </span>
      </div>
      <div className="product-name">{name}</div>
      {manufacturerName && <div className="product-meta">By {manufacturerName}</div>}
      {oemNumber && <div className="product-meta">OEM: {oemNumber}</div>}
      {quantity && <div className="product-meta">Quantity: {quantity}</div>}
      {price != null && <div className="product-price">${Number(price).toFixed(2)}</div>}
      {cartUrl && (
        <a className="cart-link" href={cartUrl} target="_blank" rel="noreferrer">
          Add to cart (demo)
        </a>
      )}
    </div>
  );
}
