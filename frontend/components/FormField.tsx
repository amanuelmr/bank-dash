import React from "react";

/**
 * A labelled form field.
 *
 * Every input on the settings page previously identified itself only by its
 * placeholder, which disappears the moment the field has a value - so a field
 * containing "10000" was indistinguishable between a postcode and a street
 * number, and there was no accessible name on any of them at all.
 *
 * The label is a real <label> bound to the control by id, so clicking it focuses
 * the input and screen readers announce it.
 */
export const inputClass =
  "w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-content-primary " +
  "placeholder:text-content-muted transition-colors " +
  "focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/25 " +
  "dark:border-line dark:bg-surface-2";

const Field: React.FC<{
  id: string;
  label: string;
  hint?: string;
  error?: string;
  className?: string;
  children: React.ReactElement;
}> = ({ id, label, hint, error, className = "", children }) => {
  const child = React.cloneElement(children, { id });

  return (
    <div className={className}>
      <label
        htmlFor={id}
        className="mb-1.5 block text-sm font-medium text-content-secondary"
      >
        {label}
      </label>
      {child}
      {hint && !error && (
        <p className="mt-1.5 text-xs text-content-muted">{hint}</p>
      )}
      {error && (
        <p role="alert" className="mt-1.5 text-xs font-medium text-danger">
          {error}
        </p>
      )}
    </div>
  );
};

export default Field;
