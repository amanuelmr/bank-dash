import React from "react";
import ServiceProvided from "@/components/ServiceProvided";
import BankservicesList from "@/components/BankservicesList";
import PageContainer from "@/components/PageContainer";

const Services: React.FC = () => {
  return (
    <PageContainer>
      <div className="pt-5 pb-2">
        <ServiceProvided />
      </div>
      <div className="pb-12">
        <BankservicesList />
      </div>
    </PageContainer>
  );
};

export default Services;
