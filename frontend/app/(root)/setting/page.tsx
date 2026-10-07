// SettingsPage.tsx
'use client';
import React, { useState } from 'react';
import { usePathname } from 'next/navigation';
import { FaUser, FaSlidersH, FaShieldAlt } from 'react-icons/fa';
import EditProfile from '@/components/updateuser';
import Preference from '@/components/updateprefrences';
import Security from '@/components/securityForm';
import PageContainer from '@/components/PageContainer';

const TABS = [
  { id: 'editProfile', label: 'Edit profile', Icon: FaUser },
  { id: 'preference', label: 'Preference', Icon: FaSlidersH },
  { id: 'security', label: 'Security', Icon: FaShieldAlt },
] as const;

type TabId = (typeof TABS)[number]['id'];

const SettingsPage = () => {
  const [activeTab, setActiveTab] = useState<TabId>('editProfile');
  const pathname = usePathname();

  const active = TABS.find((tab) => tab.id === activeTab)!;

  return (
    <PageContainer>
      <div className="mx-auto w-full max-w-5xl py-8">
        <header className="mb-6">
          <h1 className="text-2xl font-semibold text-content-primary">Settings</h1>
          <p className="mt-1 text-sm text-content-muted">
            Manage your profile, preferences and account security.
          </p>
        </header>

        {/* Horizontal tabs below the heading, rather than a 250px rail beside
            the content. The rail existed but rendered nothing at all - an empty
            <aside> that pushed the form 250px right for no reason. */}
        <div
          role="tablist"
          aria-label="Settings sections"
          className="mb-6 flex flex-wrap gap-1 border-b border-line"
        >
          {TABS.map(({ id, label, Icon }) => {
            const isActive = activeTab === id;
            return (
              <button
                key={id}
                role="tab"
                id={`tab-${id}`}
                aria-selected={isActive}
                aria-controls={`panel-${id}`}
                onClick={() => setActiveTab(id)}
                className={`-mb-px flex items-center gap-2 border-b-2 px-4 py-3 text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-brand ${
                  isActive
                    ? "border-brand text-brand"
                    : "border-transparent text-content-muted hover:border-line-strong hover:text-content-secondary"
                }`}
              >
                <Icon className="text-base" aria-hidden />
                {label}
              </button>
            );
          })}
        </div>

        <div
          role="tabpanel"
          id={`panel-${activeTab}`}
          aria-labelledby={`tab-${activeTab}`}
        >
          {activeTab === 'editProfile' && <EditProfile />}
          {activeTab === 'preference' && <Preference />}
          {activeTab === 'security' && <Security />}
        </div>
      </div>
    </PageContainer>
  );
};

export default SettingsPage;
