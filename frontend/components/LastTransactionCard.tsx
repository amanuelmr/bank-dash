
import { useEffect, useState } from "react";
import { getAllTransactions } from "@/services/transactionfetch";
import TransactionCard from "./TransactionCard";
import type { Transaction } from "@/types/api";
import { TbFileSad } from "react-icons/tb";
import TransactionCardShimmer from './TransactionCardShimmer';
import { Card } from './ui/card';

// App Component
const App: React.FC = () => {
  const [status, setStatus] = useState<'loading' | 'error' | 'success'>('loading');
  const [transactions, setTransactions] = useState<Transaction[]>([]);

  useEffect(() => {
    const fetchTransactions = async () => {
      try {
        const transactionData = await getAllTransactions(0, 5);

        if (Array.isArray(transactionData.items)) {
          setTransactions(transactionData.items);
          setStatus('success');
        } else {
          console.error("Transaction data is not an array");
          setStatus('error');
        }
      } catch (error) {
        console.error("Failed to fetch transactions", error);
        setStatus('error');
      }
    };

    fetchTransactions();
  }, []);

  if (status === 'loading') {
    return (
      <div className="flex flex-col gap-4">
      {[...Array(3)].map((_, index) => (
        <TransactionCardShimmer key={index} />
      ))}
    </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="p-3 gap-4  flex flex-col justify-center items-center h-auto  dark:bg-dark   text-center ">
        <TbFileSad
          className={`text-gray-300 dark:text-danger w-[400px] h-[70px] pb-2 block mx-auto`}
          strokeWidth={1}
        />
        <p className="text-red-500" >Failed to fetch</p>
      </div>
    );
  }

  if (status === 'success' && transactions.length === 0) {
    return (
      <div className="p-3 gap-4 flex-1 h-auto bg-gray-50 dark:bg-dark dark:text-white text-center text-gray-500">
        No transactions to display.
      </div>
    );
  }

  return (
    <Card className="divide-y divide-slate-100 overflow-hidden dark:divide-line">
      {transactions.map((transaction) => (
        <TransactionCard key={transaction.id} transaction={transaction} />
      ))}
    </Card>
  );
};

export default App;


// import React, { useEffect, useState } from 'react';
// import { getAllTransactions } from '@/services/transactionfetch';
// import { currentuser } from '@/services/userupdate';
// import TransactionCard from './TransactionCard';
