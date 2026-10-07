import React from "react";
import ServiceProvided from "@/components/ServiceProvided";
import BankservicesList from "@/components/BankservicesList";
import PageContainer from "@/components/PageContainer";

const Services: React.FC = () => {
  return (
    <PageContainer>
      <div>
        <ServiceProvided />
      </div>
      <div>
        <BankservicesList />
      </div>
    </PageContainer>
  );
};

export default Services;
