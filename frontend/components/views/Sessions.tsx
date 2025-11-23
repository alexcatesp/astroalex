'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import SessionWizard from '../wizard/SessionWizard';

export default function Sessions() {
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showWizard, setShowWizard] = useState(false);
  const [selectedSessionId, setSelectedSessionId] = useState<string | undefined>();

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      const data = await apiClient.getSessions();
      setSessions(data);
    } catch (error) {
      console.error('Error loading sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNew = () => {
    setSelectedSessionId(undefined);
    setShowWizard(true);
  };

  const handleOpenSession = (id: string) => {
    setSelectedSessionId(id);
    setShowWizard(true);
  };

  const handleWizardComplete = async () => {
    setShowWizard(false);
    setSelectedSessionId(undefined);
    await loadSessions();
  };

  if (showWizard) {
    return (
      <SessionWizard
        sessionId={selectedSessionId}
        onComplete={handleWizardComplete}
        onCancel={() => {
          setShowWizard(false);
          setSelectedSessionId(undefined);
        }}
      />
    );
  }

  return (
    <div className="max-w-7xl mx-auto py-8 px-6">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">
            Sesiones de Observación
          </h1>
          <p className="text-gray-400">
            Planifica tu noche de astrofotografía
          </p>
        </div>
        <button
          onClick={handleCreateNew}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-all shadow-lg"
        >
          + Nueva Sesión
        </button>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-400">
          Cargando sesiones...
        </div>
      ) : sessions.length === 0 ? (
        <div className="bg-gradient-to-br from-blue-900/30 to-indigo-900/30 rounded-xl p-12 border border-blue-800/50 text-center">
          <div className="text-6xl mb-6">🌙</div>
          <h3 className="text-2xl font-bold text-white mb-4">
            No hay sesiones todavía
          </h3>
          <p className="text-gray-300 mb-8">
            Crea tu primera sesión de observación y deja que Astroalex te guíe a través del proceso
          </p>
          <button
            onClick={handleCreateNew}
            className="px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-all shadow-lg"
          >
            Crear Primera Sesión
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sessions.map((session: any) => (
            <div
              key={session.id}
              onClick={() => handleOpenSession(session.id)}
              className="bg-gray-800 rounded-xl p-6 border border-gray-700 hover:border-blue-600 cursor-pointer transition-all hover:shadow-lg hover:shadow-blue-900/50"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-bold text-white mb-1">
                    {session.name}
                  </h3>
                  <div className="text-sm text-gray-400">
                    {new Date(session.date).toLocaleDateString()}
                  </div>
                </div>
                <div className="text-2xl">🌙</div>
              </div>

              <div className="space-y-2 text-sm">
                {session.location && (
                  <div className="flex items-center gap-2 text-gray-400">
                    <span>📍</span>
                    <span>{session.location.name || 'Ubicación'}</span>
                  </div>
                )}

                <div className="flex items-center gap-2">
                  <span
                    className={`px-2 py-1 rounded text-xs font-medium ${
                      session.status === 'planning'
                        ? 'bg-yellow-900 text-yellow-300'
                        : session.status === 'ready'
                        ? 'bg-green-900 text-green-300'
                        : 'bg-blue-900 text-blue-300'
                    }`}
                  >
                    {session.status === 'planning'
                      ? 'Planificando'
                      : session.status === 'ready'
                      ? 'Lista'
                      : 'En progreso'}
                  </span>
                </div>

                {session.target && (
                  <div className="text-gray-300 font-medium mt-3">
                    🎯 {session.target.name}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
