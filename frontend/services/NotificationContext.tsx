import React, { createContext, useContext, useState, useEffect, ReactNode, FC } from 'react';
import { format } from 'date-fns';
import { getAllTransactions } from '@/services/transactionfetch';
import { currentuser } from './userupdate';
import type { Transaction, User } from '@/types/api';

type Notification = {
  id: string;
  message: string;
  isRead: boolean;
  formattedDate: string;
  timestamp: number;
};

type NotificationContextType = {
  notifications: Notification[];
  fetchNotifications: () => void;
  unreadCount: number;
  markAllAsRead: () => void;
};

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export const NotificationProvider: FC<{ children: ReactNode }> = ({ children }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const [info, setInfo] = useState<User | null>(null);

  const fetchUserInfo = async () => {
    try {
      setInfo(await currentuser());
    } catch (error) {
      console.error("Error fetching user info:", error);
    }
  };

  const fetchNotifications = async () => {
    if (!info) return;

    try {
      const response = await getAllTransactions(0, 100);

      if (response && Array.isArray(response.items)) {
        const readNotificationIds = JSON.parse(localStorage.getItem('readNotifications') || '[]');
        
        const currentUser = info.username;

        // Process and format the notifications, adding a sequence number based on the index
        const formattedNotifications = response.items.map(
          (transaction: Transaction, index: number) => {
            const isSender = transaction.senderUsername === currentUser;
            const message = isSender
              ? `You have transferred $${transaction.amount} to ${transaction.receiverUsername}`
              : `${transaction.senderUsername} transferred you $${transaction.amount}`;

            return {
              id: transaction.transactionId,
              message,
              timestamp: new Date(transaction.occurredAt).getTime(),
              formattedDate: format(new Date(transaction.occurredAt), 'MMM dd, yyyy'),
              isRead: readNotificationIds.includes(transaction.transactionId),
              sequence: index,
            };
          },
        );
  
        // Sort notifications by timestamp (and sequence if needed)
        formattedNotifications.sort((a: { timestamp: number; sequence: number; }, b: { timestamp: number; sequence: number; }) => {
          // First, sort by timestamp in descending order
          if (b.timestamp !== a.timestamp) {
            return b.timestamp - a.timestamp;
          }
          // If timestamps are identical, sort by sequence number (descending)
          return b.sequence - a.sequence;
        });
  
        setNotifications(formattedNotifications);
      }
    } catch (error) {
      console.error("Error fetching notifications:", error);
    }
  };
  
  
  
  
  

  const markAllAsRead = () => {
    const readNotificationIds = notifications.map(notification => notification.id);
    localStorage.setItem('readNotifications', JSON.stringify([...readNotificationIds, ...(JSON.parse(localStorage.getItem('readNotifications') || '[]'))]));
  
    setNotifications(prevNotifications =>
      prevNotifications.map(notification => ({
        ...notification,
        isRead: true,
      }))
    );
  };

  useEffect(() => {
    fetchUserInfo();
  }, []);

  useEffect(() => {
    fetchNotifications();
  }, [info]);

  const unreadCount = notifications.filter(notification => !notification.isRead).length;

  return (
    <NotificationContext.Provider value={{ notifications, fetchNotifications, unreadCount, markAllAsRead }}>
      {children}
    </NotificationContext.Provider>
  );
};

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};

