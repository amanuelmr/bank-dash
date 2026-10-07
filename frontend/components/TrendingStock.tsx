import React from "react";

type StockData = {
  slNo: string;
  name: string;
  price: string;
  return: string;
};

interface props {
  items: StockData[];
}

/**
 * "Trending Stock", the panel beside My Investment.
 *
 * It shared no visual system with My Investment: a hardcoded `h-[343px]` with its
 * own scrollbar, hardcoded `border-gray-300` and `text-gray-800` that had no
 * dark-mode variant, and rows half the height of the list beside it. It now
 * uses the same panel chrome, tokens and row rhythm, and stretches to match the
 * height of the panel it sits next to instead of asserting one.
 */
const TrendingStock = ({ items }: props) => {
  return (
    <div className="flex h-full flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white dark:border-line dark:bg-surface-1">
      <div className="grid grid-cols-[2.5rem_1fr_auto_auto] gap-4 border-b border-slate-200 px-5 py-3 dark:border-line">
        <span className="text-xs font-medium uppercase tracking-wide text-content-muted">
          #
        </span>
        <span className="text-xs font-medium uppercase tracking-wide text-content-muted">
          Name
        </span>
        <span className="text-right text-xs font-medium uppercase tracking-wide text-content-muted">
          Price
        </span>
        <span className="text-right text-xs font-medium uppercase tracking-wide text-content-muted">
          Return
        </span>
      </div>

      <ul className="flex-1 divide-y divide-slate-100 dark:divide-line">
        {items.map((item) => (
          <li
            key={item.slNo}
            className="grid grid-cols-[2.5rem_1fr_auto_auto] items-center gap-4 px-5 py-4 transition-colors hover:bg-slate-50 dark:hover:bg-surface-2"
          >
            <span className="text-sm tabular-nums text-content-muted">
              {item.slNo.replace(/\D/g, "")}
            </span>
            <span className="truncate text-sm font-medium text-content-primary">
              {item.name}
            </span>
            <span className="text-sm tabular-nums text-content-primary">
              {item.price}
            </span>
            <span
              className={`text-sm font-medium tabular-nums ${
                item.return.includes("+") ? "text-success" : "text-danger"
              }`}
            >
              {item.return}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default TrendingStock;
