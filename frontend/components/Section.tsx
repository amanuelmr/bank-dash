import Link from "next/link";
import { cn } from "@/lib/utils";

/**
 * A titled block of a page.
 *
 * Section headings were text-2xl bold on the dashboard, text-lg on Accounts,
 * text-[19px] #333B69 on Credit Card and text-[22px] on Investments, so the
 * same kind of heading changed size from page to page. They all use this now.
 */
const Section: React.FC<{
  title: string;
  action?: { href: string; label: string };
  className?: string;
  children: React.ReactNode;
}> = ({ title, action, className, children }) => (
  <section className={cn("flex min-w-0 flex-col gap-4", className)}>
    <div className="flex items-center justify-between gap-4">
      <h2 className="text-xl font-semibold text-[#343C6A] dark:text-brand">{title}</h2>
      {action && (
        <Link href={action.href} className="text-sm font-medium text-[#343C6A] hover:underline dark:text-brand">
          {action.label}
        </Link>
      )}
    </div>
    {children}
  </section>
);

export default Section;
