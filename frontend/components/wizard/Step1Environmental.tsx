'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';

interface Step1Props {
  session: any;
  onComplete: (data: any) => void;
  onCancel: () => void;
}

export default function Step1Environmental({ session, onComplete, onCancel }: Step1Props) {
  const [loading, setLoading] = useState(false);
  const [context, setContext] = useState<any>(null);
  const [calculating, setCalculating] = useState(false);

  useEffect(() => {
    // Si ya tiene contexto, cargarlo
    if (session.ephemeris || session.conditions) {
      setContext({
        ephemeris: session.ephemeris,
        conditions: session.conditions,
      });
    }
  }, [session]);

  const handleCalculate = async () => {
    try {
      setCalculating(true);
      const response = await fetch(`http://localhost:8000/sessions/${session.id}/step1/context`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) throw new Error('Error calculating context');

      const updatedSession = await response.json();
      setContext({
        ephemeris: updatedSession.ephemeris,
        conditions: updatedSession.sky_conditions,
      });
    } catch (error) {
      console.error('Error:', error);
      alert('Error al calcular el contexto ambiental');
    } finally {
      setCalculating(false);
    }
  };

  const handleContinue = () => {
    if (context) {
      onComplete(context);
    }
  };

  return (
    <div className="max-w-5xl mx-auto py-8 px-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">
          Step 1: Contexto Ambiental
        </h1>
        <p className="text-gray-400">
          Analiza las condiciones astronómicas y meteorológicas para esta noche
        </p>
      </div>

      {/* Session Info */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 mb-6">
        <h3 className="text-lg font-semibold text-white mb-4">Información de la Sesión</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-sm text-gray-400">Nombre</div>
            <div className="text-white font-medium">{session.name}</div>
          </div>
          <div>
            <div className="text-sm text-gray-400">Fecha</div>
            <div className="text-white font-medium">
              {new Date(session.date).toLocaleDateString()}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-400">Ubicación</div>
            <div className="text-white font-medium">
              {session.location?.name || 'No especificada'}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-400">Coordenadas</div>
            <div className="text-white font-medium font-mono text-sm">
              {session.location?.latitude.toFixed(4)}°, {session.location?.longitude.toFixed(4)}°
            </div>
          </div>
        </div>
      </div>

      {!context ? (
        <div className="bg-gradient-to-br from-blue-900/30 to-indigo-900/30 rounded-xl p-12 border border-blue-800/50 text-center">
          <div className="text-6xl mb-6">🌍</div>
          <h3 className="text-2xl font-bold text-white mb-4">
            Calcula el Contexto Ambiental
          </h3>
          <p className="text-gray-300 mb-8 max-w-2xl mx-auto">
            Astroalex analizará:
          </p>
          <div className="grid grid-cols-2 gap-4 max-w-2xl mx-auto mb-8 text-left">
            <div className="bg-gray-800/50 rounded-lg p-4">
              <div className="font-medium text-white mb-2">🌙 Efemérides</div>
              <ul className="text-sm text-gray-300 space-y-1">
                <li>• Ventana de oscuridad astronómica</li>
                <li>• Fase lunar</li>
                <li>• Salida y puesta de sol</li>
              </ul>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-4">
              <div className="font-medium text-white mb-2">☁️ Condiciones Meteorológicas</div>
              <ul className="text-sm text-gray-300 space-y-1">
                <li>• Seeing (turbulencia atmosférica)</li>
                <li>• Cobertura de nubes</li>
                <li>• Jet stream</li>
              </ul>
            </div>
          </div>
          <button
            onClick={handleCalculate}
            disabled={calculating}
            className="px-8 py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white font-semibold rounded-lg transition-all shadow-lg"
          >
            {calculating ? 'Calculando...' : '🌍 Calcular Contexto Ambiental'}
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Ephemeris */}
          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <span>🌙</span> Efemérides Astronómicas
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gray-900 rounded-lg p-4">
                <div className="text-xs text-gray-400 mb-1">Oscuridad Inicia</div>
                <div className="text-white font-medium">
                  {context.ephemeris?.darkness_start
                    ? new Date(context.ephemeris.darkness_start).toLocaleTimeString()
                    : 'Calculando...'}
                </div>
              </div>
              <div className="bg-gray-900 rounded-lg p-4">
                <div className="text-xs text-gray-400 mb-1">Oscuridad Termina</div>
                <div className="text-white font-medium">
                  {context.ephemeris?.darkness_end
                    ? new Date(context.ephemeris.darkness_end).toLocaleTimeString()
                    : 'Calculando...'}
                </div>
              </div>
              <div className="bg-gray-900 rounded-lg p-4">
                <div className="text-xs text-gray-400 mb-1">Duración</div>
                <div className="text-white font-medium">
                  {context.ephemeris?.darkness_duration || 'Calculando...'}
                </div>
              </div>
              <div className="bg-gray-900 rounded-lg p-4">
                <div className="text-xs text-gray-400 mb-1">Fase Lunar</div>
                <div className="text-white font-medium">
                  {context.ephemeris?.moon_illumination
                    ? `${context.ephemeris.moon_illumination}%`
                    : 'Calculando...'}
                </div>
              </div>
            </div>
          </div>

          {/* Sky Conditions */}
          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <span>☁️</span> Condiciones del Cielo
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="bg-gray-900 rounded-lg p-4">
                <div className="text-xs text-gray-400 mb-1">Seeing</div>
                <div className="text-2xl font-bold text-white">
                  {context.conditions?.seeing
                    ? `${context.conditions.seeing}"`
                    : 'N/A'}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {context.conditions?.seeing < 2 ? '🟢 Excelente' :
                   context.conditions?.seeing < 3 ? '🟡 Bueno' : '🔴 Mediocre'}
                </div>
              </div>
              <div className="bg-gray-900 rounded-lg p-4">
                <div className="text-xs text-gray-400 mb-1">Nubes</div>
                <div className="text-2xl font-bold text-white">
                  {context.conditions?.clouds !== undefined
                    ? `${context.conditions.clouds}%`
                    : 'N/A'}
                </div>
              </div>
              <div className="bg-gray-900 rounded-lg p-4">
                <div className="text-xs text-gray-400 mb-1">Jet Stream</div>
                <div className="text-2xl font-bold text-white">
                  {context.conditions?.jet_stream
                    ? `${context.conditions.jet_stream} m/s`
                    : 'N/A'}
                </div>
              </div>
            </div>
          </div>

          {/* Assistant Message */}
          {session.assistant_messages && session.assistant_messages.length > 0 && (
            <div className="bg-blue-900/20 border border-blue-800 rounded-xl p-6">
              <div className="flex gap-4">
                <div className="text-4xl">🤖</div>
                <div className="flex-1">
                  <div className="font-semibold text-blue-300 mb-2">Astroalex dice:</div>
                  <div className="text-white whitespace-pre-line">
                    {session.assistant_messages[session.assistant_messages.length - 1].message}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-4 mt-8">
        <button
          onClick={onCancel}
          className="px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
        >
          Cancelar
        </button>
        <button
          onClick={handleContinue}
          disabled={!context}
          className="flex-1 px-6 py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white font-semibold rounded-lg transition-all shadow-lg disabled:cursor-not-allowed"
        >
          Continuar al Paso 2 →
        </button>
      </div>
    </div>
  );
}
