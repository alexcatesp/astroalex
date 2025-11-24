'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import SessionWizard from '../wizard/SessionWizard';

export default function Sessions() {
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showWizard, setShowWizard] = useState(false);
  const [selectedSessionId, setSelectedSessionId] = useState<string | undefined>();
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingName, setEditingName] = useState('');

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

  const handleStartRename = (e: React.MouseEvent, sessionId: string, currentName: string) => {
    e.stopPropagation();
    setEditingSessionId(sessionId);
    setEditingName(currentName);
  };

  const handleCancelRename = (e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingSessionId(null);
    setEditingName('');
  };

  const handleSaveRename = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    if (!editingName.trim()) {
      alert('El nombre no puede estar vacío');
      return;
    }

    try {
      await apiClient.updateSession(sessionId, { name: editingName.trim() });
      await loadSessions();
      setEditingSessionId(null);
      setEditingName('');
    } catch (error) {
      console.error('Error renaming session:', error);
      alert('Error al renombrar la sesión');
    }
  };

  const handleDeleteSession = async (e: React.MouseEvent, sessionId: string, sessionName: string) => {
    e.stopPropagation();

    const confirmDelete = window.confirm(
      `¿Estás seguro de que quieres eliminar la sesión "${sessionName}"?\n\nEsta acción no se puede deshacer.`
    );

    if (!confirmDelete) return;

    try {
      await apiClient.deleteSession(sessionId);
      await loadSessions();
    } catch (error) {
      console.error('Error deleting session:', error);
      alert('Error al eliminar la sesión');
    }
  };

  const getStepProgress = (session: any) => {
    const steps = [
      { key: 'ephemeris', label: 'Contexto' },
      { key: 'camera_profile', label: 'Cámara' },
      { key: 'target', label: 'Objetivo' },
      { key: 'scout_analysis', label: 'Scout' },
      { key: 'acquisition_plan', label: 'Plan' },
    ];

    const completedSteps = steps.filter(step => session[step.key]).length;
    return { completed: completedSteps, total: steps.length };
  };

  const getSeeingColor = (seeing: number) => {
    if (seeing < 1.5) return 'text-green-400';
    if (seeing < 2.0) return 'text-lime-400';
    if (seeing < 2.5) return 'text-yellow-400';
    if (seeing < 3.5) return 'text-orange-400';
    return 'text-red-400';
  };

  const getCloudsColor = (clouds: number) => {
    if (clouds < 10) return 'text-green-400';
    if (clouds < 30) return 'text-lime-400';
    if (clouds < 50) return 'text-yellow-400';
    if (clouds < 70) return 'text-orange-400';
    return 'text-red-400';
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
        <div className="space-y-4">
          {sessions.map((session: any) => {
            const progress = getStepProgress(session);
            const progressPercentage = (progress.completed / progress.total) * 100;

            return (
              <div
                key={session.id}
                onClick={() => handleOpenSession(session.id)}
                className="bg-gray-800 rounded-xl p-6 border-2 border-gray-700 hover:border-blue-600 cursor-pointer transition-all hover:shadow-xl hover:shadow-blue-900/30"
              >
                {/* Header with name, edit button, and delete button */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    {editingSessionId === session.id ? (
                      <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
                        <input
                          type="text"
                          value={editingName}
                          onChange={(e) => setEditingName(e.target.value)}
                          className="flex-1 bg-gray-700 text-white px-3 py-2 rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
                          autoFocus
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') handleSaveRename(e as any, session.id);
                            if (e.key === 'Escape') handleCancelRename(e as any);
                          }}
                        />
                        <button
                          onClick={(e) => handleSaveRename(e, session.id)}
                          className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                        >
                          ✓
                        </button>
                        <button
                          onClick={handleCancelRename}
                          className="px-3 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
                        >
                          ✗
                        </button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-xl font-bold text-white">
                          {session.name}
                        </h3>
                        {progressPercentage === 100 && (
                          <span className="px-3 py-1 bg-green-600 text-white text-xs font-medium rounded-full">
                            COMPLETA
                          </span>
                        )}
                      </div>
                    )}
                    {editingSessionId !== session.id && (
                      <div className="text-sm text-gray-400">
                        {new Date(session.date).toLocaleDateString('es-ES', {
                          weekday: 'long',
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric'
                        })}
                      </div>
                    )}
                  </div>
                  {editingSessionId !== session.id && (
                    <div className="flex gap-2">
                      <button
                        onClick={(e) => handleStartRename(e, session.id, session.name)}
                        className="px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
                        title="Renombrar sesión"
                      >
                        ✏️ Editar
                      </button>
                      <button
                        onClick={(e) => handleDeleteSession(e, session.id, session.name)}
                        className="px-3 py-2 bg-red-900 hover:bg-red-800 text-red-200 rounded-lg transition-colors"
                        title="Eliminar sesión"
                      >
                        🗑️
                      </button>
                    </div>
                  )}
                </div>

                {/* Session Details Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  {/* Progress & Status */}
                  <div className="bg-gray-900 rounded-lg p-4">
                    <div className="text-xs text-gray-500 mb-2">📊 PROGRESO</div>
                    <div className="mb-3">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-xs text-gray-400">Wizard</span>
                        <span className="text-xs text-gray-400">{progress.completed}/{progress.total}</span>
                      </div>
                      <div className="w-full bg-gray-700 rounded-full h-2">
                        <div
                          className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all"
                          style={{ width: `${progressPercentage}%` }}
                        />
                      </div>
                    </div>
                    <span
                      className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${
                        progressPercentage === 100
                          ? 'bg-green-900/50 text-green-300 border border-green-700'
                          : progressPercentage > 0
                          ? 'bg-blue-900/50 text-blue-300 border border-blue-700'
                          : 'bg-gray-700/50 text-gray-300 border border-gray-600'
                      }`}
                    >
                      {progressPercentage === 100 ? '✓ Completa' : progressPercentage > 0 ? '⏳ En progreso' : '📝 Nueva'}
                    </span>
                  </div>

                  {/* Environmental Conditions */}
                  <div className="bg-gray-900 rounded-lg p-4">
                    <div className="text-xs text-gray-500 mb-2">🌙 CONDICIONES</div>
                    <div className="space-y-2">
                      {session.ephemeris && (
                        <>
                          <div className="flex justify-between text-xs">
                            <span className="text-gray-400">Oscuridad:</span>
                            <span className="text-white font-medium">
                              {session.ephemeris.darkness_duration_formatted ||
                               `${Math.floor(session.ephemeris.darkness_duration)}h ${Math.round((session.ephemeris.darkness_duration % 1) * 60)}m`}
                            </span>
                          </div>
                          <div className="flex justify-between text-xs">
                            <span className="text-gray-400">Luna:</span>
                            <span className="text-white font-medium">{session.ephemeris.moon_illumination}%</span>
                          </div>
                        </>
                      )}
                      {session.conditions && (
                        <>
                          <div className="flex justify-between text-xs">
                            <span className="text-gray-400">Seeing:</span>
                            <span className={`font-bold ${getSeeingColor(session.conditions.seeing)}`}>
                              {session.conditions.seeing}"
                            </span>
                          </div>
                          <div className="flex justify-between text-xs">
                            <span className="text-gray-400">Nubes:</span>
                            <span className={`font-bold ${getCloudsColor(session.conditions.clouds)}`}>
                              {session.conditions.clouds}%
                            </span>
                          </div>
                        </>
                      )}
                      {session.location && (
                        <div className="flex items-center gap-1 text-xs text-gray-400 mt-2">
                          <span>📍</span>
                          <span>{session.location.name || 'Ubicación'}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Target & Equipment */}
                  <div className="bg-gray-900 rounded-lg p-4">
                    <div className="text-xs text-gray-500 mb-2">🎯 OBJETIVO</div>
                    {session.target ? (
                      <div>
                        <div className="font-semibold text-white mb-1">{session.target.name}</div>
                        <div className="text-sm text-gray-400">
                          {session.target.catalog_id || session.target.object_type || 'Deep Sky'}
                        </div>
                        <div className="text-xs text-gray-500 mt-2">
                          RA: {session.target.ra?.toFixed(2)}° • Dec: {session.target.dec?.toFixed(2)}°
                          {session.target.size && (
                            <>
                              <br />
                              Tamaño: {session.target.size}' arcmin
                            </>
                          )}
                        </div>
                      </div>
                    ) : (
                      <div className="text-sm text-gray-500">No seleccionado</div>
                    )}
                    {session.camera_profile && (
                      <div className="mt-3 pt-3 border-t border-gray-800">
                        <div className="text-xs text-gray-500">📷 {session.camera_profile.camera_model}</div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
