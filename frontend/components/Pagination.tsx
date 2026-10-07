// src/components/TransactionTable/Pagination.tsx

import React from "react";

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

/** How many numbered buttons to show either side of the current page. */
const SIBLINGS = 1;

const Pagination: React.FC<PaginationProps> = ({ currentPage, totalPages, onPageChange }) => {
  // It rendered every page in one non-wrapping row, so 19 pages ran off the right
  // edge of the viewport. It now shows a window around the current page with
  // ellipses, which keeps the control a fixed width at any page count.
  const current = currentPage + 1; // callers pass a 0-based index
  const last = Math.max(totalPages, 1);

  const pages: (number | "gap")[] = [];
  for (let page = 1; page <= last; page++) {
    const inWindow =
      page === 1 ||
      page === last ||
      (page >= current - SIBLINGS && page <= current + SIBLINGS);

    if (inWindow) {
      pages.push(page);
    } else if (pages[pages.length - 1] !== "gap") {
      pages.push("gap");
    }
  }

  const navButton = (label: string, target: number, disabled: boolean) => (
    <button
      type="button"
      disabled={disabled}
      onClick={() => onPageChange(target)}
      aria-label={label}
      className={`shrink-0 rounded-lg border px-3 py-2 text-sm font-medium transition-colors ${
        disabled
          ? "cursor-default border-slate-200 text-content-muted dark:border-line"
          : "border-blue-500 text-blue-600 hover:bg-blue-50 dark:hover:bg-surface-2"
      }`}
    >
      {label}
    </button>
  );

  return (
    <nav
      aria-label="Pagination"
      className="my-6 flex flex-wrap items-center justify-center gap-2"
    >
      {navButton("Previous", currentPage - 1, currentPage <= 0)}

      {pages.map((page, index) =>
        page === "gap" ? (
          <span
            key={`gap-${index}`}
            aria-hidden
            className="px-1 text-sm text-content-muted"
          >
            …
          </span>
        ) : (
          <button
            key={page}
            type="button"
            onClick={() => onPageChange(page - 1)}
            aria-current={page === current ? "page" : undefined}
            className={`min-w-[2.5rem] rounded-lg border px-3 py-2 text-sm font-medium tabular-nums transition-colors ${
              page === current
                ? "border-blue-600 bg-blue-600 text-white"
                : "border-blue-500 text-blue-600 hover:bg-blue-50 dark:hover:bg-surface-2"
            }`}
          >
            {page}
          </button>
        )
      )}

      {navButton("Next", currentPage + 1, currentPage >= totalPages)}
    </nav>
  );
};

export default Pagination;
