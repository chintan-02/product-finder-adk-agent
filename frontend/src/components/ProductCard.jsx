import { useState } from "react";

import { browseCategory } from "../catalogueExamples";

const cataloguePhotos = {
  0: "hoodie",
  6: "backpack",
  7: "t-shirt",
  8: "denim-jacket",
  9: "apples",
  12: "brown-rice",
  100: "trail-jacket",
  101: "ridge-jacket",
  102: "summit-jacket",
  103: "coast-jacket",
};

export default function ProductCard({ product }) {
  const isGrocery = browseCategory(product) === "groceries";
  const photo = cataloguePhotos[product.id];
  const [imageFailed, setImageFailed] = useState(false);

  return (
    <article className="product-card">
      <div className={isGrocery ? "product-image-wrap product-image-wrap--grocery" : "product-image-wrap"}>
        {imageFailed || (!photo && product.color) ? (
          <div className="image-fallback" role="img" aria-label={`${product.name} image unavailable`}>
            <span aria-hidden="true">◇</span>
            <small>{product.color ? "Sample product" : "Image unavailable"}</small>
          </div>
        ) : (
          <img
            className="product-image"
            src={photo ? `/catalogue/${photo}.webp` : product.image}
            alt={product.color && photo ? `${product.name} illustration` : product.name}
            loading="lazy"
            decoding="async"
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
