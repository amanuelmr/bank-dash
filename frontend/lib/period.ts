/**
 * X-axis tick labels for the investment charts.
 *
 * The API sends two shapes: `YYYY` for the yearly series and `YYYY-MM` for the
 * monthly one (see backend/app/services/user.py). Both charts used to format
 * ticks with `value.slice(0, 3)`, which was written for month *names* like
 * "january" and so rendered every year as "202" - all five yearly ticks read
 * identically, and every monthly tick read "202" too.
 */
const MONTHS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

/** `2024` -> `2024`, `2024-03` -> `Mar`. Anything else passes through trimmed. */
export function periodTick(period: string): string {
  if (typeof period !== "string") return "";
  const monthly = /^(\d{4})-(\d{2})$/.exec(period);
  if (monthly) return MONTHS[Number(monthly[2]) - 1] ?? period;
  return period;
}
