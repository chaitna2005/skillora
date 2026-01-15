import React, { useState } from 'react';

/**
 * Reusable Tabs Component with Tailwind CSS
 * 
 * @param {Array} tabs - Array of tab objects: [{ id, label, count, content }]
 * @param {string} defaultTab - Default active tab ID
 * @param {function} onChange - Callback when tab changes
 * @param {string} className - Additional custom classes
 */
const Tabs = ({ 
  tabs = [], 
  defaultTab,
  onChange,
  className = '',
  ...props 
}) => {
  const [activeTab, setActiveTab] = useState(defaultTab || tabs[0]?.id);

  const handleTabChange = (tabId) => {
    setActiveTab(tabId);
    if (onChange) {
      onChange(tabId);
    }
  };

  const activeTabContent = tabs.find(tab => tab.id === activeTab);

  return (
    <div className={`w-full ${className}`} {...props}>
      {/* Tab Navigation */}
      <div className="flex border-b-2 border-gray-200 bg-gradient-header overflow-x-auto scrollbar-hide">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => handleTabChange(tab.id)}
            className={`
              flex items-center gap-2 px-6 py-4 font-semibold text-sm
              transition-all duration-200 ease-in-out whitespace-nowrap
              border-b-4 -mb-[2px]
              ${
                activeTab === tab.id
                  ? 'text-primary border-primary bg-white'
                  : 'text-gray-600 border-transparent hover:text-gray-900 hover:bg-gray-50'
              }
            `}
          >
            <span>{tab.label}</span>
            {tab.count !== undefined && (
              <span
                className={`
                  px-2 py-0.5 text-xs font-bold rounded-full
                  ${
                    activeTab === tab.id
                      ? 'bg-primary text-white'
                      : 'bg-gray-200 text-gray-700'
                  }
                `}
              >
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="py-6">
        {activeTabContent?.content || (
          <div className="text-center text-gray-500 py-8">
            No content available
          </div>
        )}
      </div>
    </div>
  );
};

// Controlled Tabs (when you want to manage state externally)
export const ControlledTabs = ({ 
  tabs = [], 
  activeTab,
  onTabChange,
  className = '',
  ...props 
}) => {
  return (
    <div className={`w-full ${className}`} {...props}>
      {/* Tab Navigation */}
      <div className="flex border-b-2 border-gray-200 bg-gradient-header overflow-x-auto scrollbar-hide">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`
              flex items-center gap-2 px-6 py-4 font-semibold text-sm
              transition-all duration-200 ease-in-out whitespace-nowrap
              border-b-4 -mb-[2px]
              ${
                activeTab === tab.id
                  ? 'text-primary border-primary bg-white'
                  : 'text-gray-600 border-transparent hover:text-gray-900 hover:bg-gray-50'
              }
            `}
          >
            <span>{tab.label}</span>
            {tab.count !== undefined && (
              <span
                className={`
                  px-2 py-0.5 text-xs font-bold rounded-full
                  ${
                    activeTab === tab.id
                      ? 'bg-primary text-white'
                      : 'bg-gray-200 text-gray-700'
                  }
                `}
              >
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
};

export default Tabs;
