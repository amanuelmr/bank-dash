"use client";

import { useEffect, useState } from "react";
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

/**
 * Chart.js draws to a canvas, so it cannot resolve Tailwind's `dark:` variants
 * itself - the colours have to be chosen in JS. This tracks the `.dark` class on
 * <html> so the chart repaints when the theme is toggled rather than keeping
 * whichever palette it started with.
 */
function useIsDark() {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    const root = document.documentElement;
    const sync = () => setIsDark(root.classList.contains("dark"));
    sync();
    const observer = new MutationObserver(sync);
    observer.observe(root, { attributes: true, attributeFilter: ["class"] });
    return () => observer.disconnect();
  }, []);

  return isDark;
}

const ExpensesChart = () => {
  const isDark = useIsDark();

  const data = {
    labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
    datasets: [
      {
        label: "Monthly expenses",
        data: [500, 800, 400, 700, 900, 600],
        // These bars were rgba(237, 240, 247) - a near-white grey on a white
        // panel, which is why they read as empty placeholder shapes rather than
        // data. The brand hue gives them the same presence as every other chart
        // in the app.
        backgroundColor: isDark ? "rgba(104, 157, 255, 0.85)" : "rgba(84, 108, 227, 0.85)",
        hoverBackgroundColor: isDark ? "rgb(104, 157, 255)" : "rgb(84, 108, 227)",
        // Only the top of a bar should be rounded; rounding all four corners made
        // them read as pills floating above the baseline.
        borderRadius: { topLeft: 6, topRight: 6, bottomLeft: 0, bottomRight: 0 },
        borderSkipped: "bottom" as const,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        grid: { display: false },
        border: { display: false },
        ticks: {
          color: isDark ? "rgb(150, 158, 176)" : "rgb(105, 112, 128)",
          font: { size: 12 },
        },
      },
      y: {
        grid: { display: false },
        border: { display: false },
        ticks: { display: false },
        beginAtZero: true,
      },
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (context: { raw: unknown }) => `$${context.raw as number}`,
        },
      },
    },
  };

  return (
    // h-full rather than a fixed h-48, so the chart fills the panel beside the
    // cards instead of floating in the middle of it.
    <div className="h-full w-full min-h-[180px]">
      <Bar data={data} options={options} />
    </div>
  );
};

export default ExpensesChart;
