import React from "react";
import Image from "next/image";
import { cardTones, type CardTone } from "@/constants";

interface ResponsiveCreditCardProps {
  tone: CardTone;
  balance: number;
  cardHolder: string;
  expiryDate: string;
  maskedNumber: string;
}

/**
 * A credit card.
 *
 * Appearance comes from `cardTones`, which pairs every background with its own
 * foreground, chip artwork and bottom strip. Previously the component branched
 * on whether the background was the brand blue and hardcoded orange
 * `text-orange-400` for everything else, which is why a light card next to a
 * blue one looked unrelated - orange on white also sits at roughly 2.3:1, well
 * under the WCAG AA threshold for text this size.
 */
const ResponsiveCreditCard: React.FC<ResponsiveCreditCardProps> = ({
  tone,
  balance,
  cardHolder,
  expiryDate,
  maskedNumber,
}) => {
  const t = cardTones[tone];

  return (
    <div
      className={`${t.bg} ${t.fg} relative h-[170px] w-[231px] max-w-full rounded-xl sm:h-[170px] sm:w-[265px] md:h-[235px] md:w-[350px] ${
        tone === "light"
          ? "border border-slate-200 dark:border-line"
          : ""
      }`}
    >
      <div className="flex w-[95%] justify-between">
        <div className="ml-3 mt-1 p-2">
          <span className={`${t.muted} text-[11px] md:text-[12px]`}>Balance</span>
          <span className={`${t.fg} block text-[16px] font-bold tabular-nums md:text-[20px]`}>
            {balance}
          </span>
        </div>
        <Image
          src={t.chip}
          width={30}
          height={29}
          alt=""
          className="mr-2 mt-4 h-[29px]"
        />
      </div>

      <div className="flex w-[90%] justify-between">
        <div className="ml-3 pl-1.5 md:p-2">
          <span className={`${t.muted} text-[10px] md:text-[12px]`}>
            CARD HOLDER
          </span>
          <span className={`${t.fg} block text-[13px] font-bold md:text-[15px]`}>
            {cardHolder}
          </span>
        </div>

        <div className="mr-3 md:mr-9 md:p-2">
          <span className={`${t.muted} text-[10px] md:text-[12px]`}>
            VALID THRU
          </span>
          <span className={`${t.fg} block text-[13px] font-bold tabular-nums md:text-[15px]`}>
            {expiryDate}
          </span>
        </div>
      </div>

      <div
        className={`absolute bottom-0 left-0 right-0 flex items-center justify-between ${t.strip}`}
      >
        <span className={`${t.fg} ml-2 p-3 text-[15px] tabular-nums sm:text-[15px] md:text-[22px]`}>
          {maskedNumber}
        </span>
        <Image
          src="/icons/masterCard.png"
          width={35}
          height={33}
          alt=""
          className="mr-3 mt-0.5 md:h-[42px] md:w-[44px]"
        />
      </div>
    </div>
  );
};

export default ResponsiveCreditCard;
