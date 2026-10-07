import React from "react";
import Image from "next/image";

/**
 * One row of "My Investment".
 *
 * This and TrendingStock sit side by side, so they are built from the same
 * panel chrome and the same row rhythm. Previously this row was ~86px tall with
 * `lg:justify-evenly` and a set of `lg:text-start` / `lg:text-end` overrides
 * fighting the parent, while the table next to it ran at ~40px a row - the two
 * halves of the row read as unrelated components.
 *
 * Return colouring uses the success/danger tokens rather than hardcoded
 * red-500/green-500, which had no dark-mode variant.
 */
const MyInvestment = ({
  icon,
  color,
  name,
  category,
  amount,
  percentage,
}: {
  icon: string;
  color: string;
  colortext: string;
  category: string;
  categorycolor: string;
  name: string;
  amount: string;
  percentage: string;
}) => {
  const negative = percentage.includes("-");

  return (
    <div className="flex items-center gap-4 px-5 py-4 transition-colors hover:bg-slate-50 dark:hover:bg-surface-2">
      <div
        className={`${color} flex h-11 w-11 shrink-0 items-center justify-center rounded-xl`}
      >
        <Image
          src={icon}
          alt={`${name} logo`}
          width={22}
          height={22}
          className="object-contain"
        />
      </div>

      <div className="min-w-0">
        <p className="truncate text-sm font-medium text-content-primary">
          {name}
        </p>
        <p className="truncate text-xs text-content-muted">{category}</p>
      </div>

      {/* ml-auto pins the figures to the right edge, which is what the
          justify-evenly variant was reaching for and did not quite achieve. */}
      <div className="ml-auto flex items-center gap-6 text-right">
        <div className="hidden sm:block">
          <p className="text-sm font-medium tabular-nums text-content-primary">
            {amount}
          </p>
          <p className="text-xs text-content-muted">Investment value</p>
        </div>
        <div>
          <p
            className={`text-sm font-medium tabular-nums ${
              negative ? "text-danger" : "text-success"
            }`}
          >
            {percentage}
          </p>
          <p className="text-xs text-content-muted">Return</p>
        </div>
      </div>
    </div>
  );
};

export default MyInvestment;
