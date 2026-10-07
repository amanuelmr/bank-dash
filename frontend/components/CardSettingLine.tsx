import React from "react";
import { colors } from "@/constants";
import Image from "next/image";

const CardSettingLine = ({
  icon,
  title,
  description,
  background,
}: {
  icon: string;
  title: string;
  description: string;
  background: string;
}) => {
  return (
    <div className="flex items-center gap-4 px-5 py-3">
      <div className="flex items-center gap-4">
        <div
          className={`${background} flex h-11 w-11 shrink-0 items-center justify-center rounded-xl`}
        >
          <Image src={icon} alt="" width={22} height={22} className="object-contain" />
        </div>
        <div>
          <p className="text-[15px] font-medium">
            {title}
          </p>
          <p
            className={`${colors.textgray} text-[13px]`}
          >
            {description}
          </p>
        </div>
      </div>
    </div>
  );
};

export default CardSettingLine;
