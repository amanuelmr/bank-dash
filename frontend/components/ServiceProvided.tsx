import React from "react";
import {
  Carousel,
  CarouselContent,
  CarouselItem,
} from "@/components/ui/carousel";
import LifeInsuranceIcon from "@/public/icons/LifeInsuranceIcon";
import ShoppingIcon from "@/public/icons/ShoppingIcon";
import SafetyIcon from "@/public/icons/SafetyIcon";

const services = [
  {
    title: "Life Insurance",
    description: "Unlimited protection",
    icon: LifeInsuranceIcon,
  },
  {
    title: "Shopping",
    description: "Buy, Think, Grow",
    icon: ShoppingIcon,
  },
  {
    title: "Safety",
    description: "We are your allies",
    icon: SafetyIcon,
  },
];

const ServiceProvided: React.FC = () => {
  return (
    <div className="w-full">
      <Carousel className="lg:hidden">
        <CarouselContent className="py-4">
          {services.map((service, index) => (
            <CarouselItem
              key={index}
              className="w-[230px] h-[85px] mx-auto mr-4 flex-none"
            >
              <div className="flex h-full items-center gap-3 rounded-2xl border border-slate-200 bg-white p-4 dark:border-line dark:bg-surface-1">
                <service.icon className="h-11 w-11 shrink-0" aria-hidden="true" />
                <div>
                  <h3 className="text-[14px] font-semibold">{service.title}</h3>
                  <p className="text-[12px] text-gray-500">
                    {service.description}
                  </p>
                </div>
              </div>
            </CarouselItem>
          ))}
        </CarouselContent>
      </Carousel>

      {/* For Large Screens. The cards were a fixed w-[350px] in a flex row, so
          three of them overflowed the container and the last was clipped. Each
          card now takes an equal share of whatever width it is given. */}
      <div className="hidden lg:grid lg:grid-cols-3 gap-8">
        {services.map((service, index) => (
          <div
            key={index}
            className="flex h-[110px] items-center gap-4 rounded-2xl border border-slate-200 bg-white p-5 dark:border-line dark:bg-surface-1"
          >
            <service.icon className="h-14 w-14 shrink-0" aria-hidden="true" />
            <div>
              <h3 className="text-lg font-semibold">{service.title}</h3>
              <p className="text-sm text-gray-500">{service.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ServiceProvided;
