const API_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(
  /\/$/,
  "",
);

export async function searchProducts(message, signal) {
  const response = await fetch(`${API_URL}/api/v1/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
    signal,
  });

  let payload;
  try {
    payload = await response.json();
  } catch {
    throw new Error("The product service returned an unreadable response.");
  }

  if (!response.ok) {
    const detail = typeof payload.detail === "string" ? payload.detail : null;
    throw new Error(detail || "The product search could not be completed.");
  }

  return payload;
}
