'use client';

import { useState } from 'react';

interface Frame {
  path: string;
  filename: string;
  mean?: number;
  median?: number;
  std?: number;
}

interface MasterCreatorProps {
  projectId: string;
  sessionId: string;
  sessionName: string;
  frameType: 'Bias' | 'Dark' | 'Flat';
  frames: Frame[];
  onMasterCreated: () => void;
  onCancel: () => void;
}

export default function MasterCreator({
  projectId,
  sessionId,
  sessionName,
  frameType,
  frames,
  onMasterCreated,
  onCancel,
}: MasterCreatorProps) {
  const [selectedFrames, setSelectedFrames] = useState<Set<string>>(
    new Set(frames.map(f => f.path))
  );
  const [method, setMethod] = useState<'median' | 'average'>('median');
  const [rejection, setRejection] = useState<'sigma_clip' | 'minmax' | 'none'>('sigma_clip');
  const [exposureTime, setExposureTime] = useState('');
  const [gain, setGain] = useState('');
  const [filter, setFilter] = useState('');
  const [creating, setCreating] = useState(false);

  const toggleFrame = (path: string) => {
    const newSelected = new Set(selectedFrames);
    if (newSelected.has(path)) {
      newSelected.delete(path);
    } else {
      newSelected.add(path);
    }
    setSelectedFrames(newSelected);
  };

  const toggleAll = () => {
    if (selectedFrames.size === frames.length) {
      setSelectedFrames(new Set());
    } else {
      setSelectedFrames(new Set(frames.map(f => f.path)));
    }
  };

  const handleCreate = async () => {
    if (selectedFrames.size === 0) {
      alert('Selecciona al menos un frame');
      return;
    }

    setCreating(true);

    try {
      const { apiClient } = await import('@/lib/api');

      await apiClient.createMaster(projectId, {
        session_id: sessionId,
        frame_type: frameType,
        file_paths: Array.from(selectedFrames),
        method,
        rejection: rejection === 'none' ? null : rejection,
        exposure_time: exposureTime ? parseFloat(exposureTime) : null,
        gain: gain ? parseInt(gain) : null,
        filter: filter || null,
      });

      alert(`Master ${frameType} creado exitosamente`);
      onMasterCreated();
    } catch (err: any) {
      alert(`Error al crear master: ${err.message}`);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 rounded-lg border border-gray-800 w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-800">
          <h2 className="text-2xl font-bold text-white mb-2">
            Crear Master {frameType}
          </h2>
          <p className="text-gray-400 text-sm">
            Sesión: {sessionName} • {frames.length} frames disponibles
          </p>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Configuration */}
          <div className="bg-gray-800 rounded-lg p-4 space-y-4">
            <h3 className="text-lg font-semibold text-white">Configuración</h3>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {/* Method */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Método de Combinación
                </label>
                <select
                  value={method}
                  onChange={(e) => setMethod(e.target.value as any)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white"
                >
                  <option value="median">Median</option>
                  <option value="average">Average</option>
                </select>
              </div>

              {/* Rejection */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Método de Rechazo
                </label>
                <select
                  value={rejection}
                  onChange={(e) => setRejection(e.target.value as any)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white"
                >
                  <option value="sigma_clip">Sigma Clipping</option>
                  <option value="minmax">Min/Max</option>
                  <option value="none">Ninguno</option>
                </select>
              </div>

              {/* Exposure Time (for Darks/Flats) */}
              {frameType !== 'Bias' && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Exposición (s)
                  </label>
                  <input
                    type="number"
                    value={exposureTime}
                    onChange={(e) => setExposureTime(e.target.value)}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white"
                    placeholder="300"
                  />
                </div>
              )}

              {/* Gain */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Gain (opcional)
                </label>
                <input
                  type="number"
                  value={gain}
                  onChange={(e) => setGain(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white"
                  placeholder="100"
                />
              </div>

              {/* Filter (for Flats) */}
              {frameType === 'Flat' && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Filtro
                  </label>
                  <input
                    type="text"
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white"
                    placeholder="L, R, G, B, Ha..."
                  />
                </div>
              )}
            </div>
          </div>

          {/* Frame Selection */}
          <div>
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-lg font-semibold text-white">
                Selección de Frames ({selectedFrames.size}/{frames.length})
              </h3>
              <button
                onClick={toggleAll}
                className="text-sm text-blue-400 hover:text-blue-300"
              >
                {selectedFrames.size === frames.length ? 'Deseleccionar todo' : 'Seleccionar todo'}
              </button>
            </div>

            <div className="bg-gray-800 rounded-lg overflow-hidden">
              <div className="max-h-64 overflow-y-auto">
                {frames.map((frame, idx) => (
                  <div
                    key={frame.path}
                    className={`p-3 border-b border-gray-700 hover:bg-gray-750 cursor-pointer ${
                      selectedFrames.has(frame.path) ? 'bg-blue-900/20' : ''
                    }`}
                    onClick={() => toggleFrame(frame.path)}
                  >
                    <div className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={selectedFrames.has(frame.path)}
                        onChange={() => {}}
                        className="w-4 h-4"
                      />
                      <div className="flex-1">
                        <div className="text-white text-sm font-mono">{frame.filename}</div>
                        {frame.mean !== undefined && (
                          <div className="text-xs text-gray-400 mt-1">
                            Mean: {frame.mean.toFixed(2)} | Median: {frame.median?.toFixed(2)} | Std: {frame.std?.toFixed(2)}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-800 flex gap-3 justify-end">
          <button
            onClick={onCancel}
            disabled={creating}
            className="px-4 py-2 text-gray-400 hover:text-white transition-colors disabled:opacity-50"
          >
            Cancelar
          </button>
          <button
            onClick={handleCreate}
            disabled={creating || selectedFrames.size === 0}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-md transition-colors font-medium"
          >
            {creating ? 'Creando...' : `Crear Master (${selectedFrames.size} frames)`}
          </button>
        </div>
      </div>
    </div>
  );
}
