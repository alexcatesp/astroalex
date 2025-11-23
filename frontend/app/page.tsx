'use client';

import { useState } from 'react';
import Sidebar from '@/components/layout/Sidebar';
import Dashboard from '@/components/views/Dashboard';
import Equipment from '@/components/views/Equipment';
import Sessions from '@/components/views/Sessions';
import Projects from '@/components/views/Projects';
import Settings from '@/components/views/Settings';

export default function Home() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [viewContext, setViewContext] = useState<any>(null);

  const handleNavigate = (view: string, context?: any) => {
    setCurrentView(view);
    setViewContext(context);
  };

  const renderView = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard onNavigate={handleNavigate} />;
      case 'equipment':
        return <Equipment onNavigate={handleNavigate} />;
      case 'sessions':
        return <Sessions />;
      case 'projects':
        return <Projects />;
      case 'settings':
        return <Settings />;
      default:
        return <Dashboard onNavigate={handleNavigate} />;
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-gray-950">
      {/* Sidebar */}
      <Sidebar currentView={currentView} onNavigate={handleNavigate} />

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto">
        {renderView()}
      </div>
    </div>
  );
}
