"use client";
import React, { useEffect, useState } from "react";
import Link from "next/link";
import { getAllBankServices } from "@/services/bankseervice";
import BusinessLoansIcon from "@/public/icons/BusinessLoansIcon";
import CheckingAccountsIcon from "@/public/icons/CheckingAccountsIcon";
import SavingAccountsIcon from "@/public/icons/SavingAccountsIcon";
import DebitCreditIcon from "@/public/icons/DebitCreditIcon";
import SafetyIcon from "@/public/icons/SafetyIcon";
import Pagination from "./Pagination";
import { TbFileSad } from "react-icons/tb";
import { FaSearch } from "react-icons/fa";
import type { BankService } from "@/types/api";


const icons = [
  BusinessLoansIcon,
  CheckingAccountsIcon,
  SavingAccountsIcon,
  DebitCreditIcon,
  SafetyIcon,
];

const renderShimmer = (count: number) => {

  const shimmers = [];

  for (let i = 0; i < count; i++) {
    shimmers.push(
      <div key={i}>
        {/* Mobile View */}
        <div className="lg:hidden shadow-lg p-4 rounded-md flex items-center justify-between animate-pulse mb-4">
          <div className="flex items-center space-x-4">
            <div className="w-13 h-13 bg-gray-300 rounded-full"></div>
            <div>
              <div className="h-4 bg-gray-300 rounded w-32 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-24"></div>
            </div>
          </div>
          <div className="h-3 bg-gray-200 rounded w-20"></div>
        </div>

        {/* Desktop View */}
        <div
          className="hidden lg:flex shadow-lg p-4 rounded-md items-center animate-pulse mb-4"
          style={{ width: "1110px", height: "90px" }}
        >
          <div className="w-13 h-13 bg-gray-300 rounded-full"></div>
          <div className="flex-1 ml-3">
            <div className="flex justify-between">
              <div>
                <div className="h-4 bg-gray-300 rounded w-32 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-24"></div>
              </div>
              <div className="flex space-x-28">
                <div>
                  <div className="h-4 bg-gray-300 rounded w-20 mb-2"></div>
                  <div className="h-3 bg-gray-200 rounded w-16"></div>
                </div>
                <div>
                  <div className="h-4 bg-gray-300 rounded w-20 mb-2"></div>
                  <div className="h-3 bg-gray-200 rounded w-16"></div>
                </div>
                <div>
                  <div className="h-4 bg-gray-300 rounded w-20 mb-2"></div>
                  <div className="h-3 bg-gray-200 rounded w-16"></div>
                </div>
              </div>
            </div>
          </div>
          <div className="h-3 bg-gray-200 rounded w-28"></div>
        </div>
      </div>
    );
  }

  return shimmers;
};


const ITEMS_PER_PAGE = 10;

const BankservicesList: React.FC = () => {

  const [currentPage, setCurrentPage] = useState(0);
  const [filtered, setfiltered] = useState<BankService[]>([])
  const [services, setServices] = useState<BankService[]>([])
  const randomIcons = icons;
  const [totalPages, setTotalPages] = useState(0);
  // const token = Cookie.get("accessToken") || 'null'

  
  const [status, setStatus] = useState<"loading" | "error" | "success">(
    "loading"
  );
  const filter = (e: any) => {
    const keyword = e.target.value;
    if (keyword !== "") {
      const results = services.filter((service: any) => {
        return service.name.toLowerCase().startsWith(keyword.toLowerCase());
      });
      setfiltered(results);
    } else {
      setfiltered(services);}}

  useEffect(() => {
    const fetchData = async () => {
      setStatus("loading");

      try {
        const page = await getAllBankServices(currentPage, ITEMS_PER_PAGE);
        setStatus("success");
        setServices(page.items ?? []);
        setfiltered(page.items ?? []);
        setTotalPages(page.totalPages);
      } catch (error) {
        setStatus("error");
        console.error("Error fetching bank services:", error);
      }
    };
    fetchData();
  }, [currentPage]);

  if (status === "loading") {
    return (
      <div className="w-full">
        <h2 className="text-xl font-bold mb-4 dark:text-brand animate-pulse">
          Bank Services List
        </h2>
        {renderShimmer(3)}
      </div>
    );
  } else if (status === "error") {
    return (
      <div className="w-full">
        <h2 className="text-xl font-bold mb-4 dark:text-brand animate-pulse">
          Bank Services List
        </h2>
        <div className="text-xl w-[100%] text-center gap-4 flex flex-col items-center  font-bold mb-4 text-red-500">
        <TbFileSad
          className={`text-gray-300 dark:text-danger w-[400px] h-[70px] pb-2 block mx-auto`}
          strokeWidth={1}
        />
          <div> Failed to fetch the data</div>
        </div>
      </div>
    );
  } else if (status === "success") {
    return (
      <>
        {services.length == 0 ? (
          <div className="w-full mt-4">
            <div className="shadow-lg p-4 rounded-md flex items-center justify-between bg-gray-100 dark:bg-surface-2">
              <div className="flex items-center space-x-4">
                <div className="w-13 h-13 bg-gray-300 rounded-full"></div>
                <div>
                  <h3 className="text-[16px] font-semibold text-gray-700">
                    No Data Available
                  </h3>
                  <p className="text-[14px] text-gray-500">
                    There are no bank services to display at the moment.
                  </p>
                </div>
              </div>
            </div>
          </div>
        
      )
  
        : (
          <div className="w-full">
            <h2 className="text-xl font-bold mb-4 dark:text-brand">
              Bank Services List
            </h2>
            <div className="relative mb-6 max-w-sm">
              <FaSearch
                className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 dark:text-content-muted"
                size={18}
                aria-hidden
              />
              <input
                type="search"
                onChange={filter}
                placeholder="Search services"
                aria-label="Search services"
                className="w-full rounded-full border border-gray-300 dark:border-line bg-gray-100 dark:bg-surface-2 py-2 pl-11 pr-4 text-content-primary placeholder:text-content-muted focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-brand"
              />
            </div>
            {filtered.map((service: any, index: any) => (
              <div key={index} className="mb-4">
             
                {/* Mobile View */}
                <div className="lg:hidden shadow-lg p-4 rounded-md flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    {icons[index % icons.length] &&
                      React.createElement(icons[index % icons.length], {
                        className: "w-13 h-13",
                        "aria-hidden": "true",
                      })}
                    <div>
                      <h3 className="text-[14px] font-semibold">
                        {service.name}
                      </h3>
                      <p className="text-[12px] text-gray-500">
                        {service.details}
                      </p>
                    </div>
                  </div>
                  <Link href="/details" className="text-[12px] text-blue-600">
                    View Details
                  </Link>
                </div>

                {/* Larger Screens. This row carried an inline
                    style={{ width: "1110px" }} plus `space-x-28` gaps, so its
                    width was fixed in pixels and ignored the container
                    entirely - which is why the View Details button fell off the
                    right edge whenever the page was not exactly 1110px wide. A
                    grid of fractions tracks whatever width it is given. */}
                <div className="hidden lg:grid lg:grid-cols-[1.5rem_minmax(0,1fr)_7rem_5rem_5rem_auto] lg:items-center lg:gap-6 shadow-lg p-4 rounded-md bg-white dark:bg-surface-1 border border-slate-200 dark:border-line">
                  {icons[index % icons.length] &&
                    React.createElement(icons[index % icons.length], {
                      className: "w-6 h-6",
                      "aria-hidden": "true",
                    })}
                  <div className="min-w-0">
                    <h3 className="truncate text-[16px] font-semibold text-content-primary">
                      {service.name}
                    </h3>
                    <p className="truncate text-[14px] text-content-muted">
                      {service.details}
                    </p>
                  </div>
                  <div>
                    <h4 className="text-[14px] font-semibold text-content-primary">
                      {service.type}
                    </h4>
                    <p className="text-[12px] text-content-muted">type</p>
                  </div>
                  <div>
                    <h4 className="text-[14px] font-semibold text-content-primary">
                      {service.status}
                    </h4>
                    <p className="text-[12px] text-content-muted">status</p>
                  </div>
                  <div>
                    <h4 className="text-[14px] font-semibold tabular-nums text-content-primary">
                      {service.numberOfUsers}
                    </h4>
                    <p className="text-[12px] text-content-muted">users</p>
                  </div>
                  <Link
                    href="/details"
                    className="justify-self-end whitespace-nowrap text-[14px] text-blue-600 border border-blue-600 px-3 py-1 rounded-full transition-colors hover:bg-blue-600 hover:text-white"
                  >
                    View Details
                  </Link>
                </div>
              </div>
              
            ))}
          <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={setCurrentPage}
      />
          </div>)
  }
   </>
  )
  }

    
  return null; // fallback, though it shouldn't reach here
};

export default BankservicesList;
