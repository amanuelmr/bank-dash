"use client";
import React, { useState } from "react";
import { useForm, SubmitHandler } from "react-hook-form";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { createCard } from "@/services/cardfetch";
import { format } from "date-fns";
import Image from "next/image";
import { message } from "antd";
import { inputClass } from "@/components/FormField";
import { FaCalendarAlt } from "react-icons/fa";

type NewCardProps = {
  cardType: string;
  nameOnCard: string;
  balance: string;
  expiryDate: Date;
  passcode: string;
};

const AddNewCard: React.FC = () => {
  const {
    register,
    handleSubmit,
    setValue,
    reset,
    formState: { errors },
  } = useForm<NewCardProps>();

  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [loading, setLoading] = useState(false);
  const [messageApi, contextHolder] = message.useMessage();

  const onSubmit: SubmitHandler<NewCardProps> = async (data) => {
    setLoading(true);
    try {
      const apiData = {
        balance: Number(data.balance),
        cardHolder: data.nameOnCard,
        // The API expects a plain YYYY-MM-DD date.
        expiryDate: format(data.expiryDate, "yyyy-MM-dd"),
        passcode: data.passcode,
        cardType: data.cardType,
      };
      const created = await createCard(apiData);
      if (created) {
        messageApi.open({
          type: "success",
          content: "Successfully created your new card",
          duration: 4,
        });
        setSelectedDate(null); // Reset selected date
        reset(); // Reset the form after successful submission
      }
    } catch (error) {
      messageApi.open({
        type: "error",
        content: "Card creation was not successful. Please try again.",
        duration: 4,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {contextHolder}
      <div
        className={`${
          loading ? "animate-pulse opacity-50 pointer-events-none" : ""
        }`}
      >
        <div className="h-full rounded-2xl border border-slate-200 bg-white p-6 dark:border-line dark:bg-surface-1 dark:text-white">
          <p className="text-[17px] md:text-[15px] text-content-secondary">
            Credit Card generally means a plastic card issued by Scheduled
            Commercial Banks assigned to a Cardholder, with a credit limit, that
            can be used to purchase goods and services on credit or obtain cash
            advances.
          </p>

          <form
            onSubmit={handleSubmit(onSubmit)}
            className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 text-gray-900 dark:text-white"
          >
            <div>
              <label
                htmlFor="cardTypeId"
                className="mb-1.5 block text-sm font-medium text-content-secondary"
              >
                Card Type
              </label>
              <input
                id="cardTypeId"
                {...register("cardType", {
                  required: "Card Type is required",
                })}
                placeholder="Classic"
                className={inputClass}
              />
              {errors.cardType && (
                <span className="mt-1.5 block text-xs font-medium text-danger">
                  {errors.cardType.message}
                </span>
              )}
            </div>

            <div>
              <label
                htmlFor="nameOneCardId"
                className="mb-1.5 block text-sm font-medium text-content-secondary"
              >
                Name On Card
              </label>
              <input
                id="nameOnCardId"
                {...register("nameOnCard", {
                  required: "Name on Card is required",
                })}
                placeholder="My Cards"
                className={inputClass}
              />
              {errors.nameOnCard && (
                <span className="mt-1.5 block text-xs font-medium text-danger">
                  {errors.nameOnCard.message}
                </span>
              )}
            </div>

            <div>
              <label
                htmlFor="balanceId"
                className="mb-1.5 block text-sm font-medium text-content-secondary"
              >
                Balance
              </label>
              <input
                id="balanceId"
                {...register("balance", {
                  required: "Balance is required",
                  pattern: {
                    value: /^\d+$/,
                    message: "Only numbers are allowed in this field",
                  },
                })}
                placeholder="27,000$"
                className={inputClass}
              />
              {errors.balance && (
                <span className="mt-1.5 block text-xs font-medium text-danger">
                  {errors.balance.message}
                </span>
              )}
            </div>

            <div className="relative">
              <label
                htmlFor="expirationDateId"
                className="mb-1.5 block text-sm font-medium text-content-secondary"
              >
                Expiration Date
              </label>
              <div className="relative w-full [&_.react-datepicker-wrapper]:w-full [&_.react-datepicker-input]:w-full [&_.react-datepicker-input]:pr-10">
                <DatePicker
                id="expirationDateId"
                selected={selectedDate}
                onChange={(date) => {
                  if (date) {
                    setSelectedDate(date);
                    setValue("expiryDate", date, { shouldValidate: true });
                  }
                }}
                placeholderText="dd MMMM yyyy"
                className={inputClass}
                dateFormat="dd MMMM yyyy"
                />
                <FaCalendarAlt
                  className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-content-muted"
                  aria-hidden
                />
              </div>
              {errors.expiryDate && (
                <span className="mt-1.5 block text-xs font-medium text-danger">
                  {errors.expiryDate?.message}
                </span>
              )}
            </div>

            <div>
              <label
                htmlFor="passcodeId"
                className="mb-1.5 block text-sm font-medium text-content-secondary"
              >
                Passcode
              </label>
              <input
                id="passcodeId"
                {...register("passcode", {
                  required: "Passcode is required",
                })}
                placeholder="******"
                className={inputClass}
              />
              {errors.passcode && (
                <span className="mt-1.5 block text-xs font-medium text-danger">
                  {errors.passcode.message}
                </span>
              )}
            </div>

            <div className="col-span-full flex items-end">
              <button
                type="submit"
                className="w-full rounded-lg bg-brand-fill px-5 py-2.5 text-sm font-medium text-on-brand-fill transition-opacity hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2 disabled:opacity-60 dark:focus:ring-offset-surface-1 md:w-auto"
              >
                Add Card
              </button>
            </div>
          </form>
        </div>
      </div>
    </>
  );
};

export default AddNewCard;
