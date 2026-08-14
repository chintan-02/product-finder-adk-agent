import { useState } from "react";

export default function ProductCard({ product }) {
  const [imageFailed, setImageFailed] = useState(false);

  return (
    <article className="product-card">
      <div className="product-image-wrap">
        {imageFailed ? (
          <div className="image-fallback" role="img" aria-label={`${product.name} image unavailable`}>
            <span aria-hidden="true">◇</span>
            <small>Image unavailable</small>
          </div>
        ) : (
          <img
            className="product-image"
            src={product.image}
            alt={product.name}
            loading="lazy"
            onError={() => setImageFailed(true)}
          />
        )}
        <span className="category-badge">{product.category}</span>
      </div>
      <div className="product-content">
        <div className="product-heading">
          <h3>{product.name}</h3>
          <strong>${Number(product.price).toLocaleString()}</strong>
        </div>
        <p>{product.description}</p>
      </div>
    </article>
  );
}
