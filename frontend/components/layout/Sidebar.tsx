'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';

interface SidebarProps {
  currentView: string;
  onNavigate: (view: string) => void;
}

export default function Sidebar({ currentView, onNavigate }: SidebarProps) {
  const [userState, setUserState] = useState<any>(null);
  const [activeProfile, setActiveProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadUserData();
  }, []);

  const loadUserData = async () => {
    try {
      const [state, profile] = await Promise.all([
        apiClient.getUserState(),
        apiClient.getActiveEquipmentProfile().catch(() => null),
      ]);
      setUserState(state);
      setActiveProfile(profile);
    } catch (error) {
      console.error('Error loading user data:', error);
    } finally {
      setLoading(false);
    }
  };

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: '🏠' },
    { id: 'equipment', label: 'Equipos', icon: '📷' },
    { id: 'sessions', label: 'Sesiones', icon: '🌙' },
    { id: 'projects', label: 'Proyectos', icon: '📁' },
    { id: 'settings', label: 'Configuración', icon: '⚙️' },
  ];

  return (
    <div className="w-64 h-screen bg-gray-900 border-r border-gray-800 flex flex-col">
      {/* Logo/Header */}
      <div className="p-6 border-b border-gray-800">
        <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-500 to-purple-600 bg-clip-text text-transparent">
          Astroalex
        </h1>
        <p className="text-xs text-gray-500 mt-1">v2.0.0</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
              currentView === item.id
                ? 'bg-blue-600 text-white shadow-lg'
                : 'text-gray-400 hover:bg-gray-800 hover:text-white'
            }`}
          >
            <span className="text-xl">{item.icon}</span>
            <span className="font-medium">{item.label}</span>
          </button>
        ))}
      </nav>

      {/* User Status Section */}
      <div className="p-4 border-t border-gray-800 space-y-3">
        {loading ? (
          <div className="text-xs text-gray-500">Cargando...</div>
        ) : (
          <>
            {/* Active Profile */}
            {activeProfile ? (
              <div className="bg-gray-800 rounded-lg p-3">
                <div className="text-xs text-gray-500 mb-1">Perfil Activo</div>
                <div className="text-sm font-medium text-white truncate">
                  {activeProfile.name}
                </div>
                <div className="text-xs text-gray-400 mt-1">
                  {activeProfile.camera.model}
                </div>
              </div>
            ) : (
              <div className="bg-yellow-900/20 border border-yellow-800 rounded-lg p-3">
                <div className="text-xs text-yellow-500">
                  Sin perfil de equipo
                </div>
              </div>
            )}

            {/* Onboarding Status */}
            {userState && !userState.onboarding_completed && (
              <div className="bg-blue-900/20 border border-blue-800 rounded-lg p-3">
                <div className="text-xs text-blue-400">
                  ⚠️ Completar configuración inicial
                </div>
              </div>
            )}

            {/* Connection Status */}
            <div className="flex items-center gap-2 text-xs">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-gray-500">Backend conectado</span>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
