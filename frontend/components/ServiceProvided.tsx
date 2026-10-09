"use client"

import React, { useEffect, useMemo, useState } from "react";
import {
  Carousel,
  CarouselContent,
  CarouselItem,
} from "@/components/ui/carousel";
import LifeInsuranceIcon from "@/public/icons/LifeInsuranceIcon";
import ShoppingIcon from "@/public/icons/ShoppingIcon";
import SafetyIcon from "@/public/icons/SafetyIcon";
import { getAllBankServices } from "@/services/bankseervice";
import type { BankService } from "@/types/api";

/**
 * A service's `type` has no artwork of its own, so each category is given one
 * mark to represent it. These are decorative - the service name is always shown
 * as text beside them.
 */
const ICON_BY_TYPE: Record<string, React.FC<{ className?: string }>> = {
  Insurance: LifeInsuranceIcon,
  Payments: ShoppingIcon,
  Savings: SafetyIcon,
  Checking: SafetyIcon,
  Deposits: SafetyIcon,
  Loans: ShoppingIcon,
  Cards: ShoppingIcon,
  Advisory: SafetyIcon,
};

const ICON_FALLBACK = SafetyIcon;

/**
 * The three most-used services, featured above the full list.
 *
 * This previously showed three invented entries - "Life Insurance / Unlimited
 * protection", "Shopping / Buy, Think, Grow", "Safety / We are your allies" -
 * with copy that appears nowhere in the database. It now reads the same
 * `/bank-services` collection the list below it renders, so the cards and the
 * table can never disagree.
 */
const ServiceProvided: React.FC = () => {
  const [services, setServices] = useState<BankService[] | null>(null);

  useEffect(() => {
    let cancelled = false;
    getAllBankServices(0, 12)
      .then((page) => {
        if (!cancelled) setServices(page.items);
      })
      .catch((error) => {
        console.error("Error fetching featured services:", error);
        if (!cancelled) setServices([]);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const featured = useMemo(() => {
    // Only services a customer can actually join; a suspended or closed product
    // is a poor thing to lead with.
    return (services ?? [])
      .filter((service) => service.status === "ACTIVE")
      .sort((a, b) => b.numberOfUsers - a.numberOfUsers)
      .slice(0, 3);
  }, [services]);

  if (featured.length === 0) {
    return null;
  }

  return (
    <div className="w-full">
      <Carousel className="lg:hidden">
        <CarouselContent className="py-4">
          {featured.map((service) => {
            const Icon = ICON_BY_TYPE[service.type] ?? ICON_FALLBACK;
            return (
              <CarouselItem
                key={service.id}
                className="w-[230px] h-[85px] mx-auto mr-4 flex-none"
              >
                <div className="flex h-full items-center gap-3 rounded-2xl border border-slate-200 bg-white p-4 dark:border-line dark:bg-surface-1">
                  <Icon className="h-11 w-11 shrink-0" aria-hidden="true" />
                  <div className="min-w-0">
                    <h3 className="truncate text-[14px] font-semibold">
                      {service.name}
                    </h3>
                    <p className="truncate text-[12px] text-content-muted">
                      {service.details}
                    </p>
                  </div>
                </div>
              </CarouselItem>
            );
          })}
        </CarouselContent>
      </Carousel>

      {/* Each card takes an equal share of whatever width it is given. */}
      <div className="hidden lg:grid lg:grid-cols-3 gap-8">
        {featured.map((service) => {
          const Icon = ICON_BY_TYPE[service.type] ?? ICON_FALLBACK;
          return (
            <div
              key={service.id}
              className="flex h-[110px] items-center gap-4 rounded-2xl border border-slate-200 bg-white p-5 dark:border-line dark:bg-surface-1"
            >
              <Icon className="h-14 w-14 shrink-0" aria-hidden="true" />
              <div className="min-w-0">
                <h3 className="truncate text-lg font-semibold">{service.name}</h3>
                <p className="truncate text-sm text-content-muted">
                  {service.details}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ServiceProvided;