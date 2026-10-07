import Image from 'next/image';
import { Card } from './ui/card';  

interface BalanceCardProps {
    iconSrc: string; // Path to the image source
    altText: string;
    title: string;
    amount: string;
  } 

export const BalanceCard: React.FC<{ balance: BalanceCardProps }> = ({ balance }) => {
    const { iconSrc, altText, title, amount } = balance;
  
    return (
      <Card className="flex w-full items-center gap-3 p-4">
        {/* Icon */}
        <div className="rounded-full p-2">
          <Image 
            src={iconSrc} 
            alt={altText} 
            width= {35}
            height={35}
            // className="w-10 h-10" 
          />
        </div>
  
        {/* amount Details */}
        <div>
          <p className="text-xs text-content-muted">{title}</p>
          <p className="text-lg font-bold text-content-primary">{amount}</p>
        </div>
      </Card>
    );
  };