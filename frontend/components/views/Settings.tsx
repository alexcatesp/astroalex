'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';

export default function Settings() {
  const [userState, setUserState] = useState<any>(null);
  const [storageConfig, setStorageConfig] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const [state, storage] = await Promise.all([
        apiClient.getUserState(),
        apiClient.getStorageConfig().catch(() => null),
      ]);
      setUserState(state);
      setStorageConfig(storage);
    } catch (error) {
      console.error('Error loading settings:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-400">Cargando configuración...</div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-6">
      <h1 className="text-3xl font-bold text-white mb-8">
        Configuración
      </h1>

      {/* User State */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 mb-6">
        <h2 className="text-xl font-semibold text-white mb-4">Estado de Usuario</h2>
        <div className="space-y-3">
          <div className="flex justify-between items-center p-3 bg-gray-900 rounded-lg">
            <span className="text-gray-300">Onboarding Completado</span>
            <span className={`px-3 py-1 rounded-full text-sm ${
              userState?.onboarding_completed
                ? 'bg-green-900 text-green-300'
                : 'bg-yellow-900 text-yellow-300'
            }`}>
              {userState?.onboarding_completed ? 'Sí' : 'No'}
            </span>
          </div>
          <div className="flex justify-between items-center p-3 bg-gray-900 rounded-lg">
            <span className="text-gray-300">Perfil de Equipo</span>
            <span className={`px-3 py-1 rounded-full text-sm ${
              userState?.has_equipment_profile
                ? 'bg-green-900 text-green-300'
                : 'bg-red-900 text-red-300'
            }`}>
              {userState?.has_equipment_profile ? 'Configurado' : 'No configurado'}
            </span>
          </div>
          <div className="flex justify-between items-center p-3 bg-gray-900 rounded-lg">
            <span className="text-gray-300">Almacenamiento</span>
            <span className={`px-3 py-1 rounded-full text-sm ${
              userState?.storage_configured
                ? 'bg-green-900 text-green-300'
                : 'bg-red-900 text-red-300'
            }`}>
              {userState?.storage_configured ? 'Configurado' : 'No configurado'}
            </span>
          </div>
        </div>
      </div>

      {/* Storage Config */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 mb-6">
        <h2 className="text-xl font-semibold text-white mb-4">Rutas de Almacenamiento</h2>
        {storageConfig ? (
          <div className="space-y-3">
            <div className="p-3 bg-gray-900 rounded-lg">
              <div className="text-sm text-gray-400 mb-1">Raw Data</div>
              <div className="text-white font-mono text-sm">{storageConfig.raw_data_path}</div>
            </div>
            <div className="p-3 bg-gray-900 rounded-lg">
              <div className="text-sm text-gray-400 mb-1">Processed Data</div>
              <div className="text-white font-mono text-sm">{storageConfig.processed_data_path}</div>
            </div>
            <div className="p-3 bg-gray-900 rounded-lg">
              <div className="text-sm text-gray-400 mb-1">Projects</div>
              <div className="text-white font-mono text-sm">{storageConfig.projects_path}</div>
            </div>
          </div>
        ) : (
          <div className="text-gray-400">No configurado</div>
        )}
      </div>

      {/* Preferences */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <h2 className="text-xl font-semibold text-white mb-4">Preferencias</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Idioma</label>
            <select className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-blue-600">
              <option value="es">Español</option>
              <option value="en">English</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Tema</label>
            <select className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-blue-600">
              <option value="dark">Oscuro</option>
              <option value="light">Claro</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Unidades</label>
            <select className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-blue-600">
              <option value="metric">Métricas</option>
              <option value="imperial">Imperiales</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  );
}
