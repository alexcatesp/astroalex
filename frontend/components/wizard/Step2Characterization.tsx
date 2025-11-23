'use client';

import { useState } from 'react';

interface Step2Props {
  session: any;
  onComplete: (data: any) => void;
  onBack: () => void;
}

export default function Step2Characterization({ session, onComplete, onBack }: Step2Props) {
  const [biasFiles, setBiasFiles] = useState<FileList | null>(null);
  const [flatFiles, setFlatFiles] = useState<FileList | null>(null);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [skipStep, setSkipStep] = useState(false);

  const handleUpload = async () => {
    if (!biasFiles || !flatFiles) {
      alert('Por favor selecciona al menos 2 Bias y 2 Flats');
      return;
    }

    try {
      setUploading(true);

      // Crear FormData para upload
      const formData = new FormData();
      Array.from(biasFiles).forEach((file) => formData.append('bias', file));
      Array.from(flatFiles).forEach((file) => formData.append('flats', file));

      const response = await fetch(
        `http://localhost:8000/sessions/${session.id}/step2/characterize`,
        {
          method: 'POST',
          body: formData,
        }
      );

      if (!response.ok) throw new Error('Error en caracterización');

      const data = await response.json();
      setResults(data.sensor_profile);
    } catch (error) {
      console.error('Error:', error);
      alert('Error al caracterizar la cámara. Puedes saltarte este paso por ahora.');
    } finally {
      setUploading(false);
    }
  };

  const handleContinue = () => {
    if (results || skipStep) {
      onComplete(results || {});
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">
          Step 2: Caracterización de Cámara
        </h1>
        <p className="text-gray-400">
          Calibra tu cámara para obtener parámetros precisos de ruido y ganancia
        </p>
      </div>

      {!results ? (
        <>
          {/* Info Card */}
          <div className="bg-blue-900/20 border border-blue-800 rounded-xl p-6 mb-6">
            <div className="flex gap-3">
              <div className="text-3xl">💡</div>
              <div>
                <div className="font-semibold text-blue-300 mb-2">¿Qué necesitas?</div>
                <ul className="text-sm text-blue-200 space-y-1">
                  <li>• <strong>2 Bias frames</strong>: Capturas con el obturador cerrado, 0s exposición</li>
                  <li>• <strong>2 Flat frames</strong>: Capturas de superficie uniforme iluminada</li>
                  <li>• Archivos FITS sin procesar</li>
                </ul>
                <div className="mt-3 text-xs text-blue-300">
                  Astroalex calculará: Read Noise, Gain y Full Well Capacity
                </div>
              </div>
            </div>
          </div>

          {/* Upload Section */}
          <div className="space-y-6">
            {/* Bias Upload */}
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <span>🌑</span> Bias Frames
              </h3>
              <input
                type="file"
                accept=".fit,.fits,.fts"
                multiple
                onChange={(e) => setBiasFiles(e.target.files)}
                className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700 cursor-pointer"
              />
              {biasFiles && (
                <div className="mt-2 text-sm text-gray-400">
                  {biasFiles.length} archivo(s) seleccionado(s)
                </div>
              )}
            </div>

            {/* Flats Upload */}
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <span>☁️</span> Flat Frames
              </h3>
              <input
                type="file"
                accept=".fit,.fits,.fts"
                multiple
                onChange={(e) => setFlatFiles(e.target.files)}
                className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700 cursor-pointer"
              />
              {flatFiles && (
                <div className="mt-2 text-sm text-gray-400">
                  {flatFiles.length} archivo(s) seleccionado(s)
                </div>
              )}
            </div>

            {/* Upload Button */}
            <button
              onClick={handleUpload}
              disabled={!biasFiles || !flatFiles || uploading}
              className="w-full px-6 py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white font-semibold rounded-lg transition-all shadow-lg disabled:cursor-not-allowed"
            >
              {uploading ? 'Procesando archivos...' : '📊 Analizar y Caracterizar'}
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
                  ¡Caracterización Completada!
                </div>
                <div className="text-sm text-green-200">
                  Tu cámara ha sido calibrada exitosamente. Los parámetros se han guardado en tu perfil de equipo.
                </div>
              </div>
            </div>
          </div>

          {/* Results */}
          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4">
              Parámetros Calculados
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gray-900 rounded-lg p-4">
                <div className="text-xs text-gray-400 mb-1">Read Noise</div>
                <div className="text-2xl font-bold text-white">
                  {results.read_noise?.toFixed(2) || 'N/A'}
                </div>
                <div className="text-xs text-gray-500">electrons</div>
              </div>
              <div className="bg-gray-900 rounded-lg p-4">
                <div className="text-xs text-gray-400 mb-1">Gain</div>
                <div className="text-2xl font-bold text-white">
                  {results.gain?.toFixed(2) || 'N/A'}
                </div>
                <div className="text-xs text-gray-500">e-/ADU</div>
              </div>
              <div className="bg-gray-900 rounded-lg p-4">
                <div className="text-xs text-gray-400 mb-1">Full Well</div>
                <div className="text-2xl font-bold text-white">
                  {results.full_well_capacity
                    ? `${(results.full_well_capacity / 1000).toFixed(1)}k`
                    : 'N/A'}
                </div>
                <div className="text-xs text-gray-500">electrons</div>
              </div>
            </div>
          </div>

          {/* Assistant Message */}
          <div className="bg-blue-900/20 border border-blue-800 rounded-xl p-6">
            <div className="flex gap-4">
              <div className="text-4xl">🤖</div>
              <div className="flex-1">
                <div className="font-semibold text-blue-300 mb-2">Astroalex dice:</div>
                <div className="text-white">
                  {results.read_noise < 2
                    ? `Excelente ruido de lectura (${results.read_noise.toFixed(2)}e-). Tu cámara está optimizada para exposiciones largas.`
                    : results.read_noise < 4
                    ? `Buen ruido de lectura (${results.read_noise.toFixed(2)}e-). Rendimiento sólido para astrofotografía.`
                    : `Ruido de lectura moderado (${results.read_noise.toFixed(2)}e-). Considera usar binning 2x2 para mejorar SNR.`}
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
          disabled={!results && !skipStep}
          className="flex-1 px-6 py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white font-semibold rounded-lg transition-all shadow-lg disabled:cursor-not-allowed"
        >
          {skipStep ? 'Continuar sin Caracterizar →' : 'Continuar al Paso 3 →'}
        </button>
      </div>
    </div>
  );
}
