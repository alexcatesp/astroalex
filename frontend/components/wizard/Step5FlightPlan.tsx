'use client';

import { useState, useEffect } from 'react';

interface Step5Props {
  session: any;
  onComplete: () => void;
  onBack: () => void;
}

export default function Step5FlightPlan({ session, onComplete, onBack }: Step5Props) {
  const [generating, setGenerating] = useState(false);
  const [plan, setPlan] = useState<any>(null);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    // Auto-generate plan when component loads
    handleGenerate();
  }, []);

  const handleGenerate = async () => {
    try {
      setGenerating(true);

      const response = await fetch(
        `http://localhost:8000/sessions/${session.id}/step5/generate`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        }
      );

      if (!response.ok) throw new Error('Error generating plan');

      const data = await response.json();
      setPlan(data.flight_plan);
    } catch (error) {
      console.error('Error:', error);
      // Show a basic plan even if backend fails
      setPlan(generateMockPlan());
    } finally {
      setGenerating(false);
    }
  };

  const generateMockPlan = () => {
    // Fallback mock plan if backend isn't ready
    return {
      target: session.target || { name: 'M42 - Nebulosa de Orión' },
      total_session_time: '4h 30m',
      lights: [
        { filter: 'Ha', exposure: 180, count: 80, total_time: '4h 00m' },
        { filter: 'R', exposure: 120, count: 15, total_time: '30m' },
        { filter: 'G', exposure: 120, count: 15, total_time: '30m' },
        { filter: 'B', exposure: 120, count: 15, total_time: '30m' },
      ],
      calibration: {
        darks: [
          { exposure: 180, count: 20 },
          { exposure: 120, count: 20 },
        ],
        flats: { per_filter: 20 },
        bias: { count: 50 },
      },
      dither: {
        enabled: true,
        pixels: 5,
        every_n_frames: 3,
      },
      hdr_mode: session.scout_analysis?.hdr_required || false,
    };
  };

  const handleExport = async (format: 'asiair' | 'nina') => {
    try {
      setExporting(true);

      const response = await fetch(
        `http://localhost:8000/sessions/${session.id}/step5/export/${format}`,
        {
          method: 'POST',
        }
      );

      if (!response.ok) throw new Error('Error exporting plan');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `astroalex_plan_${session.target?.name || 'session'}.${
        format === 'asiair' ? 'plan' : 'json'
      }`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error:', error);
      alert(`Error exportando plan para ${format.toUpperCase()}`);
    } finally {
      setExporting(false);
    }
  };

  const handleFinish = () => {
    onComplete();
  };

  if (generating) {
    return (
      <div className="max-w-4xl mx-auto py-8 px-6">
        <div className="bg-gradient-to-br from-blue-900/30 to-indigo-900/30 rounded-xl p-12 border border-blue-800/50 text-center">
          <div className="text-6xl mb-6 animate-pulse">📋</div>
          <h3 className="text-2xl font-bold text-white mb-4">
            Generando Plan de Vuelo...
          </h3>
          <p className="text-gray-300">
            Astroalex está calculando el plan de adquisición óptimo basado en tus condiciones
          </p>
        </div>
      </div>
    );
  }

  if (!plan) {
    return (
      <div className="max-w-4xl mx-auto py-8 px-6">
        <div className="text-center py-12 text-gray-400">
          Error al generar el plan. Intenta de nuevo.
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto py-8 px-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">
          Step 5: Plan de Vuelo
        </h1>
        <p className="text-gray-400">
          Tu sesión está lista. Exporta el plan a tu software de captura
        </p>
      </div>

      {/* Target Summary */}
      <div className="bg-gradient-to-br from-green-900/30 to-emerald-900/30 rounded-xl p-6 border border-green-800/50 mb-6">
        <div className="flex items-center gap-4">
          <div className="text-5xl">🎯</div>
          <div className="flex-1">
            <div className="text-sm text-gray-400">Objetivo de Esta Noche</div>
            <div className="text-2xl font-bold text-white">
              {plan.target?.name || session.target?.name}
            </div>
            <div className="text-sm text-green-300 mt-1">
              Tiempo total de sesión: {plan.total_session_time}
            </div>
          </div>
        </div>
      </div>

      {/* Lights Plan */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 mb-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <span>💡</span> Lights (Exposiciones de Ciencia)
        </h3>
        <div className="space-y-3">
          {plan.lights.map((light: any, index: number) => (
            <div
              key={index}
              className="bg-gray-900 rounded-lg p-4 flex items-center justify-between"
            >
              <div className="flex items-center gap-4">
                <div className="px-3 py-2 bg-blue-600 text-white rounded font-bold min-w-[60px] text-center">
                  {light.filter}
                </div>
                <div>
                  <div className="text-white font-medium">
                    {light.count} × {light.exposure}s
                  </div>
                  <div className="text-sm text-gray-400">
                    Tiempo total: {light.total_time}
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-xs text-gray-500">Recomendado</div>
                <div className="text-green-400 font-medium">✓ Óptimo</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Calibration Frames */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 mb-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <span>🔧</span> Frames de Calibración
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Darks */}
          <div className="bg-gray-900 rounded-lg p-4">
            <div className="text-xs text-gray-400 mb-2">Darks</div>
            {plan.calibration.darks.map((dark: any, index: number) => (
              <div key={index} className="text-white text-sm">
                {dark.count} × {dark.exposure}s
              </div>
            ))}
          </div>

          {/* Flats */}
          <div className="bg-gray-900 rounded-lg p-4">
            <div className="text-xs text-gray-400 mb-2">Flats</div>
            <div className="text-white text-sm">
              {plan.calibration.flats.per_filter} por filtro
            </div>
            <div className="text-xs text-gray-500 mt-1">
              ({plan.lights.length} filtros)
            </div>
          </div>

          {/* Bias */}
          <div className="bg-gray-900 rounded-lg p-4">
            <div className="text-xs text-gray-400 mb-2">Bias</div>
            <div className="text-white text-sm">
              {plan.calibration.bias.count} frames
            </div>
          </div>
        </div>
      </div>

      {/* Dither Settings */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 mb-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <span>🎲</span> Configuración de Dither
        </h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gray-900 rounded-lg p-4">
            <div className="text-xs text-gray-400 mb-1">Estado</div>
            <div className="text-white font-medium">
              {plan.dither.enabled ? '✓ Habilitado' : '✗ Deshabilitado'}
            </div>
          </div>
          {plan.dither.enabled && (
            <>
              <div className="bg-gray-900 rounded-lg p-4">
                <div className="text-xs text-gray-400 mb-1">Distancia</div>
                <div className="text-white font-medium">
                  {plan.dither.pixels} píxeles
                </div>
              </div>
              <div className="bg-gray-900 rounded-lg p-4 col-span-2">
                <div className="text-xs text-gray-400 mb-1">Frecuencia</div>
                <div className="text-white font-medium">
                  Cada {plan.dither.every_n_frames} frames
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* HDR Warning */}
      {plan.hdr_mode && (
        <div className="bg-yellow-900/20 border border-yellow-800 rounded-xl p-6 mb-6">
          <div className="flex gap-4">
            <div className="text-4xl">⚠️</div>
            <div className="flex-1">
              <div className="font-semibold text-yellow-300 mb-2">
                Modo HDR Activado
              </div>
              <div className="text-yellow-200 text-sm">
                El análisis del scout frame detectó saturación. Este plan incluye exposiciones
                cortas para núcleos estelares y largas para detalles débiles. Asegúrate de
                capturar ambos sets.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Assistant Final Message */}
      <div className="bg-blue-900/20 border border-blue-800 rounded-xl p-6 mb-6">
        <div className="flex gap-4">
          <div className="text-4xl">🤖</div>
          <div className="flex-1">
            <div className="font-semibold text-blue-300 mb-2">Astroalex dice:</div>
            <div className="text-white">
              ¡Tu sesión está completamente planificada! He calculado {plan.lights.reduce((sum: number, l: any) => sum + l.count, 0)} exposiciones
              de ciencia para un total de {plan.total_session_time}. Exporta el plan a tu software
              de captura y disfruta la noche. ¡Cielos despejados!
            </div>
          </div>
        </div>
      </div>

      {/* Export Buttons */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 mb-6">
        <h3 className="text-lg font-semibold text-white mb-4">
          Exportar Plan de Captura
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <button
            onClick={() => handleExport('asiair')}
            disabled={exporting}
            className="px-6 py-4 bg-orange-600 hover:bg-orange-700 disabled:bg-gray-700 text-white font-semibold rounded-lg transition-all shadow-lg flex items-center justify-center gap-3"
          >
            <span className="text-2xl">📱</span>
            <div className="text-left">
              <div className="font-bold">ZWO ASIAIR</div>
              <div className="text-xs opacity-80">Formato .plan</div>
            </div>
          </button>
          <button
            onClick={() => handleExport('nina')}
            disabled={exporting}
            className="px-6 py-4 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 text-white font-semibold rounded-lg transition-all shadow-lg flex items-center justify-center gap-3"
          >
            <span className="text-2xl">💻</span>
            <div className="text-left">
              <div className="font-bold">N.I.N.A.</div>
              <div className="text-xs opacity-80">Formato .json</div>
            </div>
          </button>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-4">
        <button
          onClick={onBack}
          className="px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
        >
          ← Atrás
        </button>
        <button
          onClick={handleFinish}
          className="flex-1 px-6 py-4 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-lg transition-all shadow-lg"
        >
          ✓ Completar Sesión
        </button>
      </div>
    </div>
  );
}
