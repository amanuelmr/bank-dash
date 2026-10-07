import { FC } from "react";
import { cn } from "@/lib/utils";

/**
 * The content area every page sits in.
 *
 * Each page used to roll its own gutter - `ml-72`, `ml-64`, `px-6`, `pr-5`,
 * `max-w-[1110px]`, sometimes several at once. That gave five different content
 * left edges across the app (measured at 250/256/280/288/304px at 1440), so
 * switching pages moved the content sideways. It is also why /services read as
 * "not implemented like the other pages": it was the only page with its own
 * `max-w`, so its column stopped short of the right edge while its neighbours
 * ran to it.
 *
 * The sidebar is w-64 (256px) and fixed, so the content needs a matching offset
 * at lg and up. Below lg the sidebar is an overlay and content is full-bleed,
 * so the offset is only applied where it is needed.
 */
const PageContainer: FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className }) => (
  <div
    className={cn(
      // No w-full here: the sidebar is fixed, not in flow, so the content column
      // is already the full viewport width. Adding w-full alongside the ml-64
      // offset made it 1440 + 256 = 1696px and pushed every child off the right
      // edge.
      "px-4 sm:px-6 lg:ml-64 lg:px-8",
      // One vertical rhythm for every page: each top-level child is a row of
      // sections, one gap apart. Pages used py-6, pt-6, mt-4 or nothing.
      "flex flex-col gap-8 py-6 lg:py-8",
      // Fill the screen below the fixed navbar (pt-[120px], lg:pt-20 in the
      // layout), so a short page doesn't end in a white band under the grey.
      "min-h-[calc(100vh-120px)] lg:min-h-[calc(100vh-5rem)]",
      "bg-gray-100 dark:bg-dark text-gray-900 dark:text-white",
      className
    )}
  >
    {children}
  </div>
);

export default PageContainer;
