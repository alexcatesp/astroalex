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
  const [editingLocation, setEditingLocation] = useState(false);
  const [gettingLocation, setGettingLocation] = useState(false);
  const [locationForm, setLocationForm] = useState({
    name: session.location?.name || '',
    latitude: session.location?.latitude || 0,
    longitude: session.location?.longitude || 0,
  });

  // Helper functions for color coding
  const getSeeingColor = (seeing: number) => {
    if (seeing < 1.5) return 'bg-green-900/50 border-green-700';
    if (seeing < 2.0) return 'bg-lime-900/50 border-lime-700';
    if (seeing < 2.5) return 'bg-yellow-900/50 border-yellow-700';
    if (seeing < 3.5) return 'bg-orange-900/50 border-orange-700';
    return 'bg-red-900/50 border-red-700';
  };

  const getCloudsColor = (clouds: number) => {
    if (clouds < 10) return 'bg-green-900/50 border-green-700';
    if (clouds < 30) return 'bg-lime-900/50 border-lime-700';
    if (clouds < 50) return 'bg-yellow-900/50 border-yellow-700';
    if (clouds < 70) return 'bg-orange-900/50 border-orange-700';
    return 'bg-red-900/50 border-red-700';
  };

  const getWindColor = (wind: number) => {
    if (wind < 5) return 'bg-green-900/50 border-green-700';
    if (wind < 10) return 'bg-lime-900/50 border-lime-700';
    if (wind < 15) return 'bg-yellow-900/50 border-yellow-700';
    if (wind < 20) return 'bg-orange-900/50 border-orange-700';
    return 'bg-red-900/50 border-red-700';
  };

  const getHumidityColor = (humidity: number) => {
    if (humidity < 40) return 'bg-green-900/50 border-green-700';
    if (humidity < 60) return 'bg-lime-900/50 border-lime-700';
    if (humidity < 75) return 'bg-yellow-900/50 border-yellow-700';
    if (humidity < 85) return 'bg-orange-900/50 border-orange-700';
    return 'bg-red-900/50 border-red-700';
  };

  const getTemperatureColor = (temp: number) => {
    // For astrophotography, moderate temps are best
    if (temp >= 0 && temp <= 20) return 'bg-green-900/50 border-green-700';
    if ((temp > -5 && temp < 0) || (temp > 20 && temp < 25)) return 'bg-lime-900/50 border-lime-700';
    if ((temp >= -10 && temp <= -5) || (temp >= 25 && temp < 30)) return 'bg-yellow-900/50 border-yellow-700';
    return 'bg-orange-900/50 border-orange-700';
  };

  useEffect(() => {
    // Si ya tiene contexto, cargarlo
    if (session.ephemeris || session.conditions) {
      setContext({
        ephemeris: session.ephemeris,
        conditions: session.conditions,
      });
    }
  }, [session]);

  const handleGetGeolocation = () => {
    if (!navigator.geolocation) {
      alert('Tu navegador no soporta geolocalización');
      return;
    }

    setGettingLocation(true);
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;

        // Try to get location name from reverse geocoding (using OpenStreetMap Nominatim)
        try {
          const response = await fetch(
            `https://nominatim.openstreetmap.org/reverse?lat=${latitude}&lon=${longitude}&format=json`
          );
          const data = await response.json();
          const locationName = data.address?.city || data.address?.town || data.address?.village || 'Ubicación actual';

          setLocationForm({
            name: locationName,
            latitude,
            longitude,
          });
        } catch (error) {
          console.error('Error getting location name:', error);
          setLocationForm({
            name: 'Ubicación actual',
            latitude,
            longitude,
          });
        }

        setGettingLocation(false);
      },
      (error) => {
        console.error('Error getting geolocation:', error);
        alert('No se pudo obtener tu ubicación. Por favor, permite el acceso a la ubicación.');
        setGettingLocation(false);
      }
    );
  };

  const handleUpdateLocation = async () => {
    try {
      const response = await fetch(`http://localhost:8000/sessions/${session.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          location: {
            name: locationForm.name,
            latitude: locationForm.latitude,
            longitude: locationForm.longitude,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          },
        }),
      });

      if (!response.ok) throw new Error('Error updating location');

      const updatedSession = await response.json();
      session.location = updatedSession.location;
      setEditingLocation(false);

      // Automatically recalculate conditions after location change
      await handleCalculate();
    } catch (error) {
      console.error('Error:', error);
      alert('Error al actualizar la ubicación');
    }
  };

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
        conditions: updatedSession.conditions,
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

      {/* Session Info with Location Editing */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 mb-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-white">Información de la Sesión</h3>
          {!editingLocation && (
            <button
              onClick={() => setEditingLocation(true)}
              className="px-3 py-1 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
            >
              ✏️ Editar Ubicación
            </button>
          )}
        </div>

        {editingLocation ? (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="text-sm text-gray-400 block mb-1">Nombre</label>
                <input
                  type="text"
                  value={locationForm.name}
                  onChange={(e) => setLocationForm({ ...locationForm, name: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white"
                  placeholder="Madrid"
                />
              </div>
              <div>
                <label className="text-sm text-gray-400 block mb-1">Latitud</label>
                <input
                  type="number"
                  step="0.0001"
                  value={locationForm.latitude}
                  onChange={(e) => setLocationForm({ ...locationForm, latitude: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white font-mono"
                  placeholder="40.4168"
                />
              </div>
              <div>
                <label className="text-sm text-gray-400 block mb-1">Longitud</label>
                <input
                  type="number"
                  step="0.0001"
                  value={locationForm.longitude}
                  onChange={(e) => setLocationForm({ ...locationForm, longitude: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white font-mono"
                  placeholder="-3.7038"
                />
              </div>
            </div>

            <div className="flex gap-2">
              <button
                onClick={handleGetGeolocation}
                disabled={gettingLocation}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-700 text-white rounded-lg transition-colors text-sm"
              >
                {gettingLocation ? '🌍 Obteniendo...' : '🌍 Usar Mi Ubicación'}
              </button>
              <button
                onClick={handleUpdateLocation}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm"
              >
                💾 Guardar
              </button>
              <button
                onClick={() => {
                  setEditingLocation(false);
                  setLocationForm({
                    name: session.location?.name || '',
                    latitude: session.location?.latitude || 0,
                    longitude: session.location?.longitude || 0,
                  });
                }}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors text-sm"
              >
                Cancelar
              </button>
            </div>
          </div>
        ) : (
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
                {session.location?.latitude?.toFixed(4)}°, {session.location?.longitude?.toFixed(4)}°
              </div>
            </div>
          </div>
        )}
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
              <div className="font-medium text-white mb-2">☁️ Condiciones Meteorológicas (Open-Meteo)</div>
              <ul className="text-sm text-gray-300 space-y-1">
                <li>• Seeing estimado</li>
                <li>• Cobertura de nubes en tiempo real</li>
                <li>• Viento y jet stream</li>
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
                    ? new Date(context.ephemeris.darkness_start).toLocaleTimeString('es-ES', {
                        hour: '2-digit',
                        minute: '2-digit'
                      })
                    : 'Calculando...'}
                </div>
              </div>
              <div className="bg-gray-900 rounded-lg p-4">
                <div className="text-xs text-gray-400 mb-1">Oscuridad Termina</div>
                <div className="text-white font-medium">
                  {context.ephemeris?.darkness_end
                    ? new Date(context.ephemeris.darkness_end).toLocaleTimeString('es-ES', {
                        hour: '2-digit',
                        minute: '2-digit'
                      })
                    : 'Calculando...'}
                </div>
              </div>
              <div className="bg-gray-900 rounded-lg p-4">
                <div className="text-xs text-gray-400 mb-1">Duración</div>
                <div className="text-white font-medium">
                  {context.ephemeris?.darkness_duration_formatted || 'Calculando...'}
                </div>
              </div>
              <div className="bg-gray-900 rounded-lg p-4">
                <div className="text-xs text-gray-400 mb-1">Fase Lunar</div>
                <div className="text-white font-medium">
                  {context.ephemeris?.moon_illumination !== undefined
                    ? `${context.ephemeris.moon_illumination}%`
                    : 'Calculando...'}
                </div>
              </div>
            </div>
          </div>

          {/* Sky Conditions */}
          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                <span>☁️</span> Condiciones del Cielo
                {context.conditions?.source && (
                  <span className="text-xs text-gray-400 font-normal">
                    (Fuente: {context.conditions.source})
                  </span>
                )}
              </h3>
              <button
                onClick={handleCalculate}
                disabled={calculating}
                className="px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white rounded-lg transition-colors text-sm flex items-center gap-2"
                title="Refrescar condiciones"
              >
                <span className={calculating ? 'animate-spin' : ''}>🔄</span>
                {calculating ? 'Actualizando...' : 'Refrescar'}
              </button>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className={`rounded-lg p-4 border ${context.conditions?.seeing ? getSeeingColor(context.conditions.seeing) : 'bg-gray-900 border-gray-700'}`}>
                <div className="text-xs text-gray-300 mb-1">Seeing</div>
                <div className="text-2xl font-bold text-white">
                  {context.conditions?.seeing
                    ? `${context.conditions.seeing}"`
                    : 'N/A'}
                </div>
                <div className="text-xs text-gray-300 mt-1">
                  {context.conditions?.seeing < 1.5 ? '🟢 Excelente' :
                   context.conditions?.seeing < 2.0 ? '🟢 Muy bueno' :
                   context.conditions?.seeing < 2.5 ? '🟡 Bueno' :
                   context.conditions?.seeing < 3.5 ? '🟠 Regular' : '🔴 Malo'}
                </div>
              </div>
              <div className={`rounded-lg p-4 border ${context.conditions?.clouds !== undefined ? getCloudsColor(context.conditions.clouds) : 'bg-gray-900 border-gray-700'}`}>
                <div className="text-xs text-gray-300 mb-1">Nubes</div>
                <div className="text-2xl font-bold text-white">
                  {context.conditions?.clouds !== undefined
                    ? `${context.conditions.clouds}%`
                    : 'N/A'}
                </div>
                <div className="text-xs text-gray-300 mt-1">
                  {context.conditions?.clouds < 10 ? '🟢 Despejado' :
                   context.conditions?.clouds < 30 ? '🟢 Pocas nubes' :
                   context.conditions?.clouds < 50 ? '🟡 Parcial' :
                   context.conditions?.clouds < 70 ? '🟠 Nublado' : '🔴 Muy nublado'}
                </div>
              </div>
              <div className={`rounded-lg p-4 border ${context.conditions?.wind_speed !== undefined ? getWindColor(context.conditions.wind_speed) : 'bg-gray-900 border-gray-700'}`}>
                <div className="text-xs text-gray-300 mb-1">Viento</div>
                <div className="text-2xl font-bold text-white">
                  {context.conditions?.wind_speed !== undefined
                    ? `${context.conditions.wind_speed} m/s`
                    : 'N/A'}
                </div>
                <div className="text-xs text-gray-300 mt-1">
                  {context.conditions?.wind_speed < 5 ? '🟢 Calma' :
                   context.conditions?.wind_speed < 10 ? '🟢 Suave' :
                   context.conditions?.wind_speed < 15 ? '🟡 Moderado' :
                   context.conditions?.wind_speed < 20 ? '🟠 Fuerte' : '🔴 Muy fuerte'}
                </div>
              </div>
              <div className={`rounded-lg p-4 border ${context.conditions?.temperature !== undefined ? getTemperatureColor(context.conditions.temperature) : 'bg-gray-900 border-gray-700'}`}>
                <div className="text-xs text-gray-300 mb-1">Temperatura</div>
                <div className="text-2xl font-bold text-white">
                  {context.conditions?.temperature !== undefined
                    ? `${context.conditions.temperature}°C`
                    : 'N/A'}
                </div>
                <div className="text-xs text-gray-300 mt-1">
                  {context.conditions?.temperature >= 0 && context.conditions?.temperature <= 20 ? '🟢 Óptima' :
                   ((context.conditions?.temperature > -5 && context.conditions?.temperature < 0) ||
                    (context.conditions?.temperature > 20 && context.conditions?.temperature < 25)) ? '🟢 Buena' :
                   '🟡 Aceptable'}
                </div>
              </div>
              <div className={`rounded-lg p-4 border ${context.conditions?.humidity !== undefined ? getHumidityColor(context.conditions.humidity) : 'bg-gray-900 border-gray-700'}`}>
                <div className="text-xs text-gray-300 mb-1">Humedad</div>
                <div className="text-2xl font-bold text-white">
                  {context.conditions?.humidity !== undefined
                    ? `${context.conditions.humidity}%`
                    : 'N/A'}
                </div>
                <div className="text-xs text-gray-300 mt-1">
                  {context.conditions?.humidity < 40 ? '🟢 Muy baja' :
                   context.conditions?.humidity < 60 ? '🟢 Baja' :
                   context.conditions?.humidity < 75 ? '🟡 Moderada' :
                   context.conditions?.humidity < 85 ? '🟠 Alta' : '🔴 Muy alta'}
                </div>
              </div>
              <div className={`rounded-lg p-4 border ${context.conditions?.jet_stream !== undefined ? getWindColor(context.conditions.jet_stream) : 'bg-gray-900 border-gray-700'}`}>
                <div className="text-xs text-gray-300 mb-1">Jet Stream (100m)</div>
                <div className="text-2xl font-bold text-white">
                  {context.conditions?.jet_stream !== undefined
                    ? `${context.conditions.jet_stream} m/s`
                    : 'N/A'}
                </div>
                <div className="text-xs text-gray-300 mt-1">
                  {context.conditions?.jet_stream < 10 ? '🟢 Excelente' :
                   context.conditions?.jet_stream < 20 ? '🟢 Bueno' :
                   context.conditions?.jet_stream < 30 ? '🟡 Regular' :
                   context.conditions?.jet_stream < 40 ? '🟠 Alto' : '🔴 Muy alto'}
                </div>
              </div>
            </div>
          </div>

          {/* Assistant Message */}
          {session.messages && session.messages.length > 0 && (
            <div className="bg-blue-900/20 border border-blue-800 rounded-xl p-6">
              <div className="flex gap-4">
                <div className="text-4xl">🤖</div>
                <div className="flex-1">
                  <div className="font-semibold text-blue-300 mb-2">Astroalex dice:</div>
                  <div className="text-white whitespace-pre-line">
                    {session.messages[session.messages.length - 1].message}
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
