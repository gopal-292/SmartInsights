export function inr(value: number | undefined | null) {
  const n = Number(value || 0);
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(n);
}

export function pct(value: number | undefined | null) {
  return `${Number(value || 0).toFixed(1)}%`;
}
