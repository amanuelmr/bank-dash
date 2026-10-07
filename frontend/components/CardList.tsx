import React from "react";
import { colors, sidebarLinks } from "../constants/index";
import { CgCreditCard } from "react-icons/cg";
import type { Card } from "@/types/api";
import Image from "next/image";

interface Props {
  card_list: Card[];
}

const CardList: React.FC<Props> = ({ card_list }) => {
  return (
    <div className="max-h-[400px] w-full divide-y divide-slate-100 overflow-y-auto rounded-2xl border border-slate-200 bg-white scrollbar-thin scrollbar-thumb-[#b5c2d9] scrollbar-thumb-rounded-full dark:divide-line dark:border-line dark:bg-surface-1">
      {Array.isArray(card_list) && card_list.length > 0 ? (
        card_list.map((card, index) => (
        <div
          key={index}
          className="grid w-full grid-cols-[3rem_minmax(0,1fr)_minmax(0,1fr)_auto] items-center gap-4 px-5 py-4 sm:grid-cols-[3rem_repeat(4,minmax(0,1fr))_auto] dark:text-white"
        >
          {/* Icon */}
          <div className="h-12 w-12 rounded-xl bg-[#E7EDFF] dark:bg-[#E7EDFF]/15 flex items-center justify-center">
            <CgCreditCard className="w-7 h-7" />
          </div>

          {/* Card Type */}
          <div className="flex flex-col">
            <p className="text-sm font-medium">Card Type</p>
            <p className={`${colors.textgray} text-xs `}>{card.cardType}</p>
          </div>

          {/* Bank */}
          <div className="flex flex-col">
            <p className="text-sm font-medium">Bank</p>
            <p className={`${colors.textgray} text-xs`}>BankDash.</p>
          </div>

          {/* Card Number - Hide on small screens */}
          <div className="hidden sm:flex flex-col min-w-0">
            <p className="text-sm font-medium hidden sm:block">Card Number</p>
            <p className={`${colors.textgray} text-xs hidden sm:block`}>
              {card.maskedNumber}
            </p>
          </div>

          {/* Card Name - Hide on small screens */}
          <div className="hidden sm:flex flex-col min-w-0">
            <p className="text-sm font-medium hidden sm:block">Card Name</p>
            <p className={`${colors.textgray} text-xs hidden sm:block`}>
              {card.cardHolder.split(' ')[0]}
            </p>
          </div>

          {/* View Details Link */}
          <a
            href="#"
            className="text-[#1814F3] font-semibold text-sm sm:text-xs dark:text-brand"
          >
            View Details
          </a>
        </div>
      ))) : (
        <div className=" pr-6 py-32 bg-surface-1 w-full flex flex-col justify-center align-middle rounded-xl scrollbar-none">
          <Image
                src="/icons/null.png"
                width={80}
                height={80}
                alt="null"
                className="mx-auto pb-2 block"
              />
          <span className="mx-auto my-auto md:text-xl text-sm text-[#993d4b] font-bold">
            There is no cards for now!
            </span>
        </div>
      )}
    </div>
  );
};

export default CardList;

/* Group 343 */
