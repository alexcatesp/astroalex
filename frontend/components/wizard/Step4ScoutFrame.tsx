'use client';

import { useState } from 'react';

interface Step4Props {
  session: any;
  onComplete: (data: any) => void;
  onBack: () => void;
}

export default function Step4ScoutFrame({ session, onComplete, onBack }: Step4Props) {
  const [scoutFile, setScoutFile] = useState<File | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<any>(null);
  const [skipStep, setSkipStep] = useState(false);

  const handleUpload = async () => {
    if (!scoutFile) {
      alert('Por favor selecciona un frame de prueba');
      return;
    }

    try {
      setAnalyzing(true);

      const formData = new FormData();
      formData.append('scout_frame', scoutFile);

      const response = await fetch(
        `http://localhost:8000/sessions/${session.id}/step4/analyze`,
        {
          method: 'POST',
          body: formData,
        }
      );

      if (!response.ok) throw new Error('Error en análisis');

      const data = await response.json();
      setAnalysis(data.scout_analysis);
    } catch (error) {
      console.error('Error:', error);
      alert('Error al analizar el frame. Puedes saltarte este paso por ahora.');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleContinue = () => {
    if (analysis || skipStep) {
      onComplete(analysis || {});
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">
          Step 4: Smart Scout Frame
        </h1>
        <p className="text-gray-400">
          Analiza un frame de prueba para optimizar tu plan de captura
        </p>
      </div>

      {!analysis ? (
        <>
          {/* Info Card */}
          <div className="bg-blue-900/20 border border-blue-800 rounded-xl p-6 mb-6">
            <div className="flex gap-3">
              <div className="text-3xl">💡</div>
              <div>
                <div className="font-semibold text-blue-300 mb-2">¿Qué es un Scout Frame?</div>
                <ul className="text-sm text-blue-200 space-y-1">
                  <li>• <strong>Apunta al objeto</strong> y toma una exposición de prueba (30-60s)</li>
                  <li>• <strong>Con tu filtro principal</strong> (Ha, L-Pro, o Luminance)</li>
                  <li>• <strong>Sin procesamiento</strong>: archivo FITS raw</li>
                </ul>
                <div className="mt-3 text-xs text-blue-300">
                  Astroalex medirá: Fondo de cielo, saturación, y calculará exposición óptima
                </div>
              </div>
            </div>
          </div>

          {/* Upload Section */}
          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <span>🔍</span> Scout Frame
            </h3>
            <input
              type="file"
              accept=".fit,.fits,.fts"
              onChange={(e) => setScoutFile(e.target.files?.[0] || null)}
              className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700 cursor-pointer"
            />
            {scoutFile && (
              <div className="mt-2 text-sm text-gray-400">
                {scoutFile.name} ({(scoutFile.size / 1024 / 1024).toFixed(2)} MB)
              </div>
            )}

            <button
              onClick={handleUpload}
              disabled={!scoutFile || analyzing}
              className="w-full mt-4 px-6 py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white font-semibold rounded-lg transition-all shadow-lg disabled:cursor-not-allowed"
            >
              {analyzing ? 'Analizando frame...' : '🔍 Analizar Scout Frame'}
            </button>
          </div>

          {/* Skip Option */}
          <div className="mt-6 text-center">
            <button
              onClick={() => setSkipStep(true)}
              className="text-gray-400 hover:text-white text-sm underline"
            >
              Saltarse este paso (usar valores por defecto)
            </button>
          </div>
        </>
      ) : (
        <div className="space-y-6">
          {/* Success Message */}
          <div className="bg-green-900/20 border border-green-800 rounded-xl p-6">
            <div className="flex gap-3">
              <div className="text-3xl">✅</div>
              <div>
                <div className="font-semibold text-green-300 mb-2">
                  ¡Análisis Completado!
                </div>
                <div className="text-sm text-green-200">
                  Frame analizado exitosamente. Exposiciones óptimas calculadas.
                </div>
              </div>
            </div>
          </div>

          {/* Analysis Results */}
          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4">
              Resultados del Análisis
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gray-900 rounded-lg p-4">
                <div className="text-xs text-gray-400 mb-1">Fondo de Cielo</div>
                <div className="text-2xl font-bold text-white">
                  {analysis.sky_background?.toFixed(1) || 'N/A'}
                </div>
                <div className="text-xs text-gray-500">e-/s</div>
              </div>
              <div className="bg-gray-900 rounded-lg p-4">
                <div className="text-xs text-gray-400 mb-1">Saturación Detectada</div>
                <div className="text-2xl font-bold text-white">
                  {analysis.saturation_detected
                    ? `${(analysis.saturation_percentage * 100).toFixed(1)}%`
                    : '0%'}
                </div>
                <div className="text-xs text-gray-500">
                  {analysis.saturation_detected ? '⚠️ HDR recomendado' : '✓ Sin saturación'}
                </div>
              </div>
              <div className="bg-gray-900 rounded-lg p-4">
                <div className="text-xs text-gray-400 mb-1">SNR Estimado</div>
                <div className="text-2xl font-bold text-white">
                  {analysis.snr_estimate?.toFixed(1) || 'N/A'}
                </div>
                <div className="text-xs text-gray-500">ratio</div>
              </div>
            </div>
          </div>

          {/* Optimal Exposures */}
          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4">
              Exposiciones Óptimas Calculadas
            </h3>
            <div className="space-y-2">
              {analysis.optimal_exposure &&
                Object.entries(analysis.optimal_exposure).map(([filter, seconds]: [string, any]) => (
                  <div key={filter} className="flex items-center justify-between p-3 bg-gray-900 rounded-lg">
                    <div className="flex items-center gap-3">
                      <span className="px-3 py-1 bg-blue-600 text-white rounded font-medium">
                        {filter}
                      </span>
                      <span className="text-gray-400">Filtro {filter}</span>
                    </div>
                    <div className="text-white font-bold text-lg">
                      {seconds}s
                    </div>
                  </div>
                ))}
            </div>
          </div>

          {/* HDR Warning */}
          {analysis.hdr_required && (
            <div className="bg-yellow-900/20 border border-yellow-800 rounded-xl p-6">
              <div className="flex gap-4">
                <div className="text-4xl">⚠️</div>
                <div className="flex-1">
                  <div className="font-semibold text-yellow-300 mb-2">
                    Estrategia HDR Recomendada
                  </div>
                  <div className="text-yellow-200 text-sm">
                    Se detectó saturación en el {(analysis.saturation_percentage * 100).toFixed(1)}% de los píxeles.
                    Te recomendamos usar dos exposiciones: una corta para preservar núcleos estelares
                    y una larga para capturar detalles débiles.
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Assistant Message */}
          <div className="bg-blue-900/20 border border-blue-800 rounded-xl p-6">
            <div className="flex gap-4">
              <div className="text-4xl">🤖</div>
              <div className="flex-1">
                <div className="font-semibold text-blue-300 mb-2">Astroalex dice:</div>
                <div className="text-white">
                  {analysis.sky_background < 30
                    ? 'Cielo oscuro excelente! Puedes usar exposiciones largas sin problemas.'
                    : analysis.sky_background < 60
                    ? 'Contaminación lumínica moderada. Considera usar un filtro anti-polución si tienes.'
                    : 'Alta contaminación lumínica. Usa filtros narrowband (Ha, OIII, SII) para mejores resultados.'}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-4 mt-8">
        <button
          onClick={onBack}
          className="px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
        >
          ← Atrás
        </button>
        <button
          onClick={handleContinue}
          disabled={!analysis && !skipStep}
          className="flex-1 px-6 py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white font-semibold rounded-lg transition-all shadow-lg disabled:cursor-not-allowed"
        >
          {skipStep ? 'Continuar sin Scout Frame →' : 'Continuar al Paso 5 →'}
        </button>
      </div>
    </div>
  );
}
