import { TbFileSad } from "react-icons/tb";
import { cn } from "@/lib/utils";

/**
 * What a panel shows when it has nothing to show - no data, or a failed fetch.
 *
 * This was copy-pasted into fourteen files, each with its own message colour
 * (red-500, #993d4b, white, none), its own height, and several with a `w-screen`
 * or `w-[400px]` that overflowed the column it sat in. An empty list and a
 * failed request also looked identical. `tone` separates the two.
 */
const EmptyState: React.FC<{
  message: string;
  tone?: "empty" | "error";
  className?: string;
}> = ({ message, tone = "empty", className }) => (
  <div
    role={tone === "error" ? "alert" : undefined}
    className={cn(
      "flex min-h-[160px] w-full flex-col items-center justify-center gap-3 p-6 text-center",
      className
    )}
  >
    <TbFileSad
      aria-hidden
      strokeWidth={1}
      className={cn(
        "h-12 w-12",
        tone === "error" ? "text-danger" : "text-content-muted"
      )}
    />
    <p
      className={cn(
        "text-sm",
        tone === "error" ? "font-medium text-danger" : "text-content-muted"
      )}
    >
      {message}
    </p>
  </div>
);

export default EmptyState;
