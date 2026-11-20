import { useState } from "react";

import { browseCategory } from "../catalogueExamples";

const cataloguePhotos = {
  0: "hoodie",
  6: "backpack",
  7: "t-shirt",
  8: "denim-jacket",
  9: "apples",
  12: "brown-rice",
};

export default function ProductCard({ product }) {
  const photo = cataloguePhotos[product.id];
  const [imageFailed, setImageFailed] = useState(false);

  return (
    <article className="product-card">
      <div className="product-image-wrap">
        {imageFailed || product.color ? (
          <div className="image-fallback" role="img" aria-label={`${product.name} image unavailable`}>
            <span aria-hidden="true">◇</span>
            <small>{product.color ? "Sample product" : "Image unavailable"}</small>
          </div>
        ) : (
          <img
            className="product-image"
            src={photo ? `/catalogue/${photo}.webp` : product.image}
            alt={product.name}
            loading="lazy"
            onError={() => setImageFailed(true)}
          />
        )}
        <span className="category-badge">{browseCategory(product)}</span>
      </div>
      <div className="product-content">
        <div className="product-heading">
          <h3>{product.name}</h3>
          <strong>${Number(product.price).toLocaleString()}</strong>
        </div>
        <p>{product.description}</p>
        {product.color && <p>{product.color} · Sizes {product.sizes.join(", ")}</p>}
      </div>
    </article>
  );
}
