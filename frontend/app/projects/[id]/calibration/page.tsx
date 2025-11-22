'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';
import Link from 'next/link';
import MasterCreator from '@/components/calibration/MasterCreator';

type FrameType = 'bias' | 'darks' | 'flats';

export default function CalibrationPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;

  const [project, setProject] = useState<any>(null);
  const [sessions, setSessions] = useState<any[]>([]);
  const [masters, setMasters] = useState<any[]>([]);
  const [selectedSession, setSelectedSession] = useState<any>(null);
  const [selectedFrameType, setSelectedFrameType] = useState<FrameType | null>(null);
  const [frames, setFrames] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreator, setShowCreator] = useState(false);

  // New session modal state
  const [showNewSession, setShowNewSession] = useState(false);
  const [newSessionName, setNewSessionName] = useState('');
  const [newSessionDate, setNewSessionDate] = useState(
    new Date().toISOString().split('T')[0]
  );

  useEffect(() => {
    loadData();
  }, [projectId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [projectData, sessionsData, mastersData] = await Promise.all([
        apiClient.getProject(projectId),
        apiClient.getCalibrationSessions(projectId),
        apiClient.getMasters(projectId),
      ]);

      setProject(projectData);
      setSessions(sessionsData);
      setMasters(mastersData);
    } catch (err) {
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSession = async () => {
    if (!newSessionName.trim()) {
      alert('Ingresa un nombre para la sesión');
      return;
    }

    try {
      await apiClient.createCalibrationSession(projectId, {
        name: newSessionName.trim(),
        date: newSessionDate,
      });

      await loadData();
      setShowNewSession(false);
      setNewSessionName('');
      setNewSessionDate(new Date().toISOString().split('T')[0]);
    } catch (err: any) {
      alert(`Error al crear sesión: ${err.message}`);
    }
  };

  const handleScanFrames = async (session: any, frameType: FrameType) => {
    try {
      const result = await apiClient.scanCalibrationFrames(
        projectId,
        session.name,
        frameType
      );

      setSelectedSession(session);
      setSelectedFrameType(frameType);
      setFrames(result.frames || []);
      setShowCreator(true);
    } catch (err: any) {
      alert(`Error al escanear frames: ${err.message}`);
    }
  };

  const handleMasterCreated = async () => {
    setShowCreator(false);
    await loadData();
  };

  if (loading) {
    return (
      <div className="min-h-screen p-8 flex items-center justify-center">
        <div className="text-gray-400">Cargando...</div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="min-h-screen p-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-red-900/20 border border-red-800 rounded-lg p-4 text-red-400">
            Proyecto no encontrado
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link
            href={`/projects/${projectId}`}
            className="text-blue-400 hover:text-blue-300 mb-4 inline-block"
          >
            ← Volver al proyecto
          </Link>
          <h1 className="text-4xl font-bold text-white mb-2">
            Masters de Calibración
          </h1>
          <p className="text-gray-400">{project.name}</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Sessions */}
          <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-white">
                Sesiones de Calibración
              </h2>
              <button
                onClick={() => setShowNewSession(true)}
                className="text-sm px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
              >
                + Nueva
              </button>
            </div>

            {sessions.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No hay sesiones todavía
              </div>
            ) : (
              <div className="space-y-3">
                {sessions.map((session) => (
                  <div
                    key={session.id}
                    className="bg-gray-800 rounded-lg p-4 border border-gray-700"
                  >
                    <div className="font-semibold text-white mb-2">
                      {session.name}
                    </div>
                    <div className="text-sm text-gray-400 mb-3">
                      Fecha: {session.date}
                    </div>

                    <div className="flex flex-wrap gap-2">
                      <button
                        onClick={() => handleScanFrames(session, 'bias')}
                        className="text-xs px-3 py-1 bg-purple-900/30 hover:bg-purple-900/50 text-purple-300 rounded transition-colors"
                      >
                        Master Bias
                      </button>
                      <button
                        onClick={() => handleScanFrames(session, 'darks')}
                        className="text-xs px-3 py-1 bg-blue-900/30 hover:bg-blue-900/50 text-blue-300 rounded transition-colors"
                      >
                        Master Dark
                      </button>
                      <button
                        onClick={() => handleScanFrames(session, 'flats')}
                        className="text-xs px-3 py-1 bg-yellow-900/30 hover:bg-yellow-900/50 text-yellow-300 rounded transition-colors"
                      >
                        Master Flat
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Masters Created */}
          <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
            <h2 className="text-xl font-semibold text-white mb-4">
              Masters Creados ({masters.length})
            </h2>

            {masters.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No hay masters todavía
              </div>
            ) : (
              <div className="space-y-3 max-h-[600px] overflow-y-auto">
                {masters.map((master) => (
                  <div
                    key={master.id}
                    className="bg-gray-800 rounded-lg p-4 border border-gray-700"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <div className="font-semibold text-white">
                          {master.filename}
                        </div>
                        <div className="text-sm text-gray-400 mt-1">
                          Tipo: {master.type} • {master.num_frames} frames
                        </div>
                        {master.exposure_time && (
                          <div className="text-sm text-gray-400">
                            Exposición: {master.exposure_time}s
                          </div>
                        )}
                        {master.gain && (
                          <div className="text-sm text-gray-400">
                            Gain: {master.gain}
                          </div>
                        )}
                        {master.filter && (
                          <div className="text-sm text-gray-400">
                            Filtro: {master.filter}
                          </div>
                        )}
                      </div>
                      <span
                        className={`text-xs px-2 py-1 rounded ${
                          master.type === 'Bias'
                            ? 'bg-purple-900/30 text-purple-300'
                            : master.type === 'Dark'
                            ? 'bg-blue-900/30 text-blue-300'
                            : 'bg-yellow-900/30 text-yellow-300'
                        }`}
                      >
                        {master.type}
                      </span>
                    </div>
                    <div className="text-xs text-gray-500 mt-2">
                      Creado: {new Date(master.created_at).toLocaleString('es-ES')}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* New Session Modal */}
        {showNewSession && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-gray-900 rounded-lg p-6 max-w-md w-full mx-4 border border-gray-800">
              <h2 className="text-2xl font-bold mb-4 text-white">
                Nueva Sesión de Calibración
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Nombre de la Sesión *
                  </label>
                  <input
                    type="text"
                    value={newSessionName}
                    onChange={(e) => setNewSessionName(e.target.value)}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white"
                    placeholder="2025-01-22_Newton200_ASI533"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Fecha
                  </label>
                  <input
                    type="date"
                    value={newSessionDate}
                    onChange={(e) => setNewSessionDate(e.target.value)}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white"
                  />
                </div>
              </div>

              <div className="flex gap-3 justify-end mt-6">
                <button
                  onClick={() => setShowNewSession(false)}
                  className="px-4 py-2 text-gray-400 hover:text-white"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleCreateSession}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md"
                >
                  Crear Sesión
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Master Creator Modal */}
        {showCreator && selectedSession && selectedFrameType && (
          <MasterCreator
            projectId={projectId}
            sessionId={selectedSession.id}
            sessionName={selectedSession.name}
            frameType={
              selectedFrameType === 'bias'
                ? 'Bias'
                : selectedFrameType === 'darks'
                ? 'Dark'
                : 'Flat'
            }
            frames={frames}
            onMasterCreated={handleMasterCreated}
            onCancel={() => setShowCreator(false)}
          />
        )}
      </div>
    </div>
  );
}
