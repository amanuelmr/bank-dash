// SettingsPage.tsx
'use client';
import React, { useState } from 'react';
import EditProfile from '@/components/updateuser';
import Preference from '@/components/updateprefrences';
import Security from '@/components/securityForm';
import PageContainer from '@/components/PageContainer';

const TABS = [
  { id: 'editProfile', label: 'Edit Profile' },
  { id: 'preference', label: 'Preference' },
  { id: 'security', label: 'Security' },
] as const;

type TabId = (typeof TABS)[number]['id'];

const SettingsPage = () => {
  const [activeTab, setActiveTab] = useState<TabId>('editProfile');
  return (
    <PageContainer>
      <div className="w-full max-w-5xl">
        {/* Horizontal tabs below the heading, rather than a 250px rail beside the
            content. The rail existed but rendered nothing at all - an empty
            <aside> that pushed the form 250px right for no reason.

            Styled to match the tabs already used on /transaction
            (font-bold px-4 py-2 rounded-t-lg, border-b-2 when active) so the
            two do not read as two different tab systems. */}
        <div role="tablist" aria-label="Settings sections" className="mb-6 flex flex-wrap gap-2">
          {TABS.map(({ id, label }) => {
            const isActive = activeTab === id;
            return (
              <button
                key={id}
                role="tab"
                id={`tab-${id}`}
                aria-selected={isActive}
                aria-controls={`panel-${id}`}
                onClick={() => setActiveTab(id)}
                className={`rounded-t-lg px-4 py-2 font-bold transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-brand ${
                  isActive
                    ? "border-b-2 border-blue-500 text-content-primary dark:text-white"
                    : "text-gray-600 hover:text-content-primary dark:text-content-secondary"
                }`}
              >
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
