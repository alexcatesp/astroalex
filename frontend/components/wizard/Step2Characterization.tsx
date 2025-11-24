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

    // Validar cantidad de archivos
    if (biasFiles.length < 2) {
      alert('Se requieren al menos 2 Bias frames');
      return;
    }
    if (flatFiles.length < 2) {
      alert('Se requieren al menos 2 Flat frames');
      return;
    }

    try {
      setUploading(true);

      // Crear FormData con solo los archivos FITS
      const formData = new FormData();
      formData.append('bias1', biasFiles[0]);
      formData.append('bias2', biasFiles[1]);
      formData.append('flat1', flatFiles[0]);
      formData.append('flat2', flatFiles[1]);

      // Construir URL con query parameters
      const cameraModel = session.equipment_profile?.camera?.model || 'Unknown Camera';
      const gainSetting = session.equipment_profile?.camera?.gain;

      const params = new URLSearchParams({
        camera_model: cameraModel,
      });

      if (gainSetting !== undefined && gainSetting !== null) {
        params.append('gain_setting', gainSetting.toString());
      }

      console.log('Request details:');
      console.log('- Files: bias1, bias2, flat1, flat2');
      console.log('- Query params:', params.toString());

      const response = await fetch(
        `http://localhost:8000/sessions/${session.id}/step2/characterize?${params.toString()}`,
        {
          method: 'POST',
          body: formData,
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('Error response:', errorData);

        let errorMessage = 'Error en caracterización';
        if (errorData.detail) {
          if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
          } else if (Array.isArray(errorData.detail)) {
            errorMessage = errorData.detail.map((e: any) => e.msg || JSON.stringify(e)).join(', ');
          } else {
            errorMessage = JSON.stringify(errorData.detail);
          }
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      console.log('Characterization result:', data);

      // El backend devuelve la sesión completa actualizada
      setResults(data.camera_profile);

      // Notificar al componente padre con la sesión actualizada
      onComplete(data);
    } catch (error) {
      console.error('Full error:', error);
      const errorMessage = error instanceof Error ? error.message : JSON.stringify(error);
      alert(`Error al caracterizar la cámara: ${errorMessage}. Puedes saltarte este paso por ahora.`);
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
          {/* Info Cards */}
          <div className="space-y-4 mb-6">
            <div className="bg-blue-900/20 border border-blue-800 rounded-xl p-6">
              <div className="flex gap-3">
                <div className="text-3xl">💡</div>
                <div className="flex-1">
                  <div className="font-semibold text-blue-300 mb-2">¿Qué necesitas?</div>
                  <ul className="text-sm text-blue-200 space-y-1">
                    <li>• <strong>2 Bias frames</strong>: Capturas con el obturador cerrado, 0s exposición</li>
                    <li>• <strong>2 Flat frames</strong>: Capturas de superficie uniforme iluminada (40-60% del máximo)</li>
                    <li>• Archivos FITS sin procesar (extensiones: .fit, .fits, .fts)</li>
                  </ul>
                  <div className="mt-3 text-xs text-blue-300">
                    Astroalex calculará automáticamente: <strong>Read Noise</strong>, <strong>Gain</strong> y <strong>Full Well Capacity</strong>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-purple-900/20 border border-purple-800 rounded-xl p-6">
              <div className="flex gap-3">
                <div className="text-3xl">🔬</div>
                <div className="flex-1">
                  <div className="font-semibold text-purple-300 mb-2">¿Por qué es importante?</div>
                  <div className="text-sm text-purple-200 space-y-2">
                    <p>
                      <strong>Read Noise</strong>: Ruido electrónico del sensor. Valores bajos (&lt;2e-) son excelentes para
                      exposiciones largas. Valores altos (&gt;4e-) benefician de binning 2x2.
                    </p>
                    <p>
                      <strong>Gain</strong>: Conversión de electrones a unidades digitales (ADU). Típico: 0.5-3.0 e-/ADU.
                    </p>
                    <p>
                      <strong>Full Well</strong>: Capacidad máxima antes de saturación. Define el rango dinámico de tu sensor.
                    </p>
                  </div>
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
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
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
                  {results.gain?.toFixed(3) || 'N/A'}
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

            {/* Camera Model Info */}
            {results.camera_model && (
              <div className="text-sm text-gray-400 mt-3 pt-3 border-t border-gray-700">
                <span className="font-medium">Cámara:</span> {results.camera_model}
                {results.gain_setting && <span className="ml-4"><span className="font-medium">Gain:</span> {results.gain_setting}</span>}
                {results.temperature && <span className="ml-4"><span className="font-medium">Temp:</span> {results.temperature}°C</span>}
              </div>
            )}

            {/* Warnings if any */}
            {results.notes && (
              <div className="mt-3 p-3 bg-yellow-900/20 border border-yellow-800 rounded-lg">
                <div className="text-sm text-yellow-300">
                  <span className="font-semibold">⚠️ Advertencias:</span>
                  <div className="mt-1 text-yellow-200">{results.notes}</div>
                </div>
              </div>
            )}
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
