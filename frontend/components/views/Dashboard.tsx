'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';

interface DashboardProps {
  onNavigate: (view: string, context?: any) => void;
}

export default function Dashboard({ onNavigate }: DashboardProps) {
  const [userState, setUserState] = useState<any>(null);
  const [activeProfile, setActiveProfile] = useState<any>(null);
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [state, profile, sessionsData] = await Promise.all([
        apiClient.getUserState(),
        apiClient.getActiveEquipmentProfile().catch(() => null),
        apiClient.getSessions().catch(() => []),
      ]);
      setUserState(state);
      setActiveProfile(profile);
      setSessions(sessionsData);
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-400">Cargando dashboard...</div>
      </div>
    );
  }

  // Si es primera vez, mostrar onboarding
  if (userState?.first_time && !userState?.onboarding_completed) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-6">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-white mb-4">
            ¡Bienvenido a Astroalex! 🌟
          </h1>
          <p className="text-xl text-gray-400">
            Tu asistente inteligente de astrofotografía
          </p>
        </div>

        <div className="bg-gray-800 rounded-xl p-8 mb-8 border border-gray-700">
          <h2 className="text-2xl font-semibold text-white mb-4">
            ¿Qué hace Astroalex?
          </h2>
          <div className="space-y-4 text-gray-300">
            <p>
              Astroalex te guía paso a paso a través de todo el flujo de trabajo de astrofotografía:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li><strong>Fase Nocturna:</strong> Planificación de sesión, condiciones ambientales, selección de objetivos</li>
              <li><strong>Fase Diurna:</strong> Procesamiento automático, control de calidad con IA, apilado y resultado final</li>
            </ul>
            <p className="text-sm text-gray-400 mt-6">
              No es una caja de herramientas pasiva - Astroalex te dice exactamente qué hacer a continuación.
            </p>
          </div>
        </div>

        <div className="bg-gradient-to-br from-blue-900/30 to-purple-900/30 rounded-xl p-8 border border-blue-800/50">
          <h3 className="text-xl font-semibold text-white mb-4">
            Vamos a configurar tu sistema
          </h3>
          <p className="text-gray-300 mb-6">
            Necesitamos algunos datos para personalizar tu experiencia:
          </p>

          <div className="space-y-4">
            <div className="flex items-center gap-4 p-4 bg-gray-800/50 rounded-lg">
              <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold">
                1
              </div>
              <div className="flex-1">
                <div className="font-medium text-white">Configura rutas de almacenamiento</div>
                <div className="text-sm text-gray-400">Define dónde guardar tus archivos FITS y proyectos</div>
              </div>
              <div className={`w-6 h-6 rounded-full ${userState?.storage_configured ? 'bg-green-600' : 'bg-gray-700'}`}>
                {userState?.storage_configured && '✓'}
              </div>
            </div>

            <div className="flex items-center gap-4 p-4 bg-gray-800/50 rounded-lg">
              <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold">
                2
              </div>
              <div className="flex-1">
                <div className="font-medium text-white">Crea tu perfil de equipo</div>
                <div className="text-sm text-gray-400">Cámara, telescopio, montura y filtros</div>
              </div>
              <div className={`w-6 h-6 rounded-full ${userState?.has_equipment_profile ? 'bg-green-600' : 'bg-gray-700'}`}>
                {userState?.has_equipment_profile && '✓'}
              </div>
            </div>

            <div className="flex items-center gap-4 p-4 bg-gray-800/50 rounded-lg opacity-50">
              <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-gray-400 font-bold">
                3
              </div>
              <div className="flex-1">
                <div className="font-medium text-gray-400">Caracteriza tu cámara (opcional)</div>
                <div className="text-sm text-gray-500">Para optimización avanzada</div>
              </div>
              <div className="w-6 h-6 rounded-full bg-gray-700"></div>
            </div>
          </div>

          <button
            onClick={() => onNavigate('equipment')}
            className="w-full mt-8 px-6 py-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-all shadow-lg hover:shadow-xl"
          >
            Comenzar Configuración →
          </button>
        </div>
      </div>
    );
  }

  // Dashboard principal para usuarios configurados
  return (
    <div className="max-w-7xl mx-auto py-8 px-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">
          ¿Qué quieres hacer hoy?
        </h1>
        <p className="text-gray-400">
          Elige tu flujo de trabajo
        </p>
      </div>

      {/* Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {/* Night Phase - Plan Session */}
        <button
          onClick={() => onNavigate('sessions', { mode: 'create' })}
          className="group bg-gradient-to-br from-blue-900/40 to-indigo-900/40 border-2 border-blue-800 hover:border-blue-600 rounded-xl p-8 text-left transition-all hover:scale-105 hover:shadow-2xl"
        >
          <div className="text-5xl mb-4">🌙</div>
          <h2 className="text-2xl font-bold text-white mb-3">
            Planificar Sesión de Observación
          </h2>
          <p className="text-gray-300 mb-4">
            Fase nocturna: Analiza condiciones, selecciona objetivo, genera plan de captura
          </p>
          <div className="text-sm text-blue-400 group-hover:text-blue-300">
            Steps 1-5: Environmental → Target → Scout → Flight Plan
          </div>
        </button>

        {/* Day Phase - Process Data */}
        <button
          onClick={() => onNavigate('projects')}
          className="group bg-gradient-to-br from-purple-900/40 to-pink-900/40 border-2 border-purple-800 hover:border-purple-600 rounded-xl p-8 text-left transition-all hover:scale-105 hover:shadow-2xl"
        >
          <div className="text-5xl mb-4">☀️</div>
          <h2 className="text-2xl font-bold text-white mb-3">
            Procesar Datos
          </h2>
          <p className="text-gray-300 mb-4">
            Fase diurna: Organiza, calibra, apila y obtén tu imagen final
          </p>
          <div className="text-sm text-purple-400 group-hover:text-purple-300">
            Steps 6-8: Ingest → Quality Control → Processing
          </div>
        </button>
      </div>

      {/* Recent Sessions */}
      {sessions.length > 0 && (
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h3 className="text-xl font-semibold text-white mb-4">
            Sesiones Recientes
          </h3>
          <div className="space-y-2">
            {sessions.slice(0, 5).map((session: any) => (
              <div
                key={session.id}
                className="flex items-center justify-between p-4 bg-gray-900 rounded-lg hover:bg-gray-750 cursor-pointer transition-colors"
                onClick={() => onNavigate('sessions', { sessionId: session.id })}
              >
                <div>
                  <div className="font-medium text-white">{session.name}</div>
                  <div className="text-sm text-gray-400">{new Date(session.date).toLocaleDateString()}</div>
                </div>
                <div className="text-sm text-gray-500">{session.status}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick Stats */}
      <div className="grid grid-cols-3 gap-4 mt-6">
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <div className="text-gray-400 text-sm mb-1">Sesiones</div>
          <div className="text-2xl font-bold text-white">{sessions.length}</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <div className="text-gray-400 text-sm mb-1">Perfil Activo</div>
          <div className="text-sm font-medium text-white truncate">
            {activeProfile?.name || 'Ninguno'}
          </div>
        </div>
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <div className="text-gray-400 text-sm mb-1">Estado</div>
          <div className="text-sm font-medium text-green-400">Listo</div>
        </div>
      </div>
    </div>
  );
}
