'use client';

import { useState } from 'react';
import { apiClient } from '@/lib/api';

interface StorageSetupProps {
  onComplete: () => void;
  onBack?: () => void;
}

export default function StorageSetup({ onComplete, onBack }: StorageSetupProps) {
  const [formData, setFormData] = useState({
    raw_data_path: 'E:\\Astrofoto\\Raw',
    processed_data_path: 'D:\\Astrofoto\\Processed',
    projects_path: 'D:\\Astrofoto\\Projects',
    cache_path: 'D:\\Astrofoto\\Cache',
  });
  const [validation, setValidation] = useState<any>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleValidate = async () => {
    try {
      // En un caso real, llamaríamos a un endpoint de validación
      setValidation({
        raw_data_path: { valid: true, exists: false },
        processed_data_path: { valid: true, exists: false },
        projects_path: { valid: true, exists: false },
        cache_path: { valid: true, exists: false },
      });
    } catch (err) {
      console.error('Error validating paths:', err);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);

      await apiClient.setStorageConfig(formData);

      // Actualizar user state
      await apiClient.updateUserState({ storage_configured: true });

      onComplete();
    } catch (err: any) {
      setError(err.message || 'Error al guardar la configuración');
      console.error('Error saving storage config:', err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">
          Configuración de Almacenamiento
        </h1>
        <p className="text-gray-400">
          Define dónde se guardarán tus archivos FITS y proyectos
        </p>
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-800 rounded-lg p-4 text-red-400 mb-6">
          {error}
        </div>
      )}

      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 mb-6">
        <div className="space-y-6">
          {/* Raw Data Path */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Ruta de Datos Raw (FITS) *
            </label>
            <p className="text-xs text-gray-500 mb-2">
              Normalmente en disco externo. Aquí se guardarán los FITS sin procesar.
            </p>
            <input
              type="text"
              value={formData.raw_data_path}
              onChange={(e) => setFormData({ ...formData, raw_data_path: e.target.value })}
              className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white font-mono focus:outline-none focus:border-blue-600"
              placeholder="E:\Astrofoto\Raw"
            />
            {validation?.raw_data_path && (
              <div className={`text-xs mt-1 ${validation.raw_data_path.valid ? 'text-green-400' : 'text-red-400'}`}>
                {validation.raw_data_path.valid
                  ? validation.raw_data_path.exists
                    ? '✓ Directorio válido y existe'
                    : '✓ Directorio válido (se creará automáticamente)'
                  : '✗ Ruta inválida'}
              </div>
            )}
          </div>

          {/* Processed Data Path */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Ruta de Datos Procesados *
            </label>
            <p className="text-xs text-gray-500 mb-2">
              Masters, calibrados, registrados y apilados.
            </p>
            <input
              type="text"
              value={formData.processed_data_path}
              onChange={(e) => setFormData({ ...formData, processed_data_path: e.target.value })}
              className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white font-mono focus:outline-none focus:border-blue-600"
              placeholder="D:\Astrofoto\Processed"
            />
          </div>

          {/* Projects Path */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Ruta de Proyectos *
            </label>
            <p className="text-xs text-gray-500 mb-2">
              Metadatos, configuraciones y resultados finales.
            </p>
            <input
              type="text"
              value={formData.projects_path}
              onChange={(e) => setFormData({ ...formData, projects_path: e.target.value })}
              className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white font-mono focus:outline-none focus:border-blue-600"
              placeholder="D:\Astrofoto\Projects"
            />
          </div>

          {/* Cache Path */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Ruta de Caché
            </label>
            <p className="text-xs text-gray-500 mb-2">
              Archivos temporales y caché del sistema.
            </p>
            <input
              type="text"
              value={formData.cache_path}
              onChange={(e) => setFormData({ ...formData, cache_path: e.target.value })}
              className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white font-mono focus:outline-none focus:border-blue-600"
              placeholder="D:\Astrofoto\Cache"
            />
          </div>
        </div>

        {/* Validate Button */}
        <button
          onClick={handleValidate}
          className="mt-6 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
        >
          Validar Rutas
        </button>
      </div>

      {/* Info Card */}
      <div className="bg-blue-900/20 border border-blue-800 rounded-lg p-4 mb-6">
        <div className="flex gap-3">
          <div className="text-2xl">💡</div>
          <div className="text-sm text-blue-300">
            <p className="font-medium mb-2">Recomendaciones:</p>
            <ul className="list-disc list-inside space-y-1 text-xs">
              <li>Guarda los FITS raw en un disco externo rápido (SSD preferible)</li>
              <li>Procesados y proyectos pueden ir en disco interno</li>
              <li>Los directorios se crearán automáticamente si no existen</li>
              <li>Puedes cambiar estas rutas más tarde en Configuración</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-4">
        {onBack && (
          <button
            onClick={onBack}
            className="px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
          >
            ← Atrás
          </button>
        )}
        <button
          onClick={handleSave}
          disabled={saving}
          className="flex-1 px-6 py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white font-semibold rounded-lg transition-all shadow-lg disabled:cursor-not-allowed"
        >
          {saving ? 'Guardando...' : 'Guardar y Continuar →'}
        </button>
      </div>
    </div>
  );
}
