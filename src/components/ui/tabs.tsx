import React, { useState } from 'react';

interface TabsProps {
  children: React.ReactNode;
  defaultValue: string;
}

export const Tabs: React.FC<TabsProps> = ({ children, defaultValue }) => {
  const [activeTab, setActiveTab] = useState(defaultValue);

  const tabListChildren = React.Children.map(children, child => 
    React.isValidElement(child) && child.type === TabsList ? child : null
  );

  const tabContentChildren = React.Children.map(children, child => 
    React.isValidElement(child) && child.type === TabsContent ? child : null
  );

  return (
    <div>
      {tabListChildren}
      {tabContentChildren?.find((child: React.ReactElement) => child.props.value === activeTab)}
    </div>
  );
};

interface TabsListProps {
  children: React.ReactNode;
}

export const TabsList: React.FC<TabsListProps> = ({ children }) => {
  return (
    <div className="flex space-x-2 border-b mb-4">
      {children}
    </div>
  );
};

interface TabsTriggerProps {
  value: string;
  children: React.ReactNode;
}

export const TabsTrigger: React.FC<TabsTriggerProps> = ({ value, children }) => {
  return (
    <div 
      className="px-4 py-2 border-b-2 border-transparent hover:border-blue-500 cursor-pointer"
    >
      {children}
    </div>
  );
};

interface TabsContentProps {
  value: string;
  children: React.ReactNode;
  className?: string;
}

export const TabsContent: React.FC<TabsContentProps> = ({ value, children, className = '' }) => {
  return (
    <div className={className}>
      {children}
    </div>
  );
};
