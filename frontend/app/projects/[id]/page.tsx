'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { Project, FileMetadata } from '@/shared/types';
import Link from 'next/link';

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;

  const [project, setProject] = useState<Project | null>(null);
  const [ingestFiles, setIngestFiles] = useState<FileMetadata[]>([]);
  const [ingestStats, setIngestStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [organizing, setOrganizing] = useState(false);
  const [sessionName, setSessionName] = useState('');

  useEffect(() => {
    loadProjectData();
  }, [projectId]);

  const loadProjectData = async () => {
    try {
      setLoading(true);
      const [projectData, files, stats] = await Promise.all([
        apiClient.getProject(projectId),
        apiClient.scanIngestDirectory(projectId),
        apiClient.getIngestStats(projectId),
      ]);

      setProject(projectData);
      setIngestFiles(files);
      setIngestStats(stats);
    } catch (err) {
      console.error('Error loading project data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleOrganizeFiles = async () => {
    if (organizing) return;

    if (ingestFiles.length === 0) {
      alert('No hay archivos para organizar');
      return;
    }

    try {
      setOrganizing(true);
      const results = await apiClient.organizeFiles(projectId, sessionName || undefined);

      alert(
        `Organización completada:\n` +
        `✓ ${results.success} archivos organizados\n` +
        `✗ ${results.failed} errores`
      );

      // Reload data
      await loadProjectData();
      setSessionName('');
    } catch (err: any) {
      alert(`Error al organizar archivos: ${err.message}`);
    } finally {
      setOrganizing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen p-8 flex items-center justify-center">
        <div className="text-gray-400">Cargando proyecto...</div>
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
          <Link href="/" className="text-blue-400 hover:text-blue-300 mt-4 inline-block">
            ← Volver a proyectos
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link href="/" className="text-blue-400 hover:text-blue-300 mb-4 inline-block">
            ← Volver a proyectos
          </Link>
          <h1 className="text-4xl font-bold text-white mb-2">{project.name}</h1>
          {project.description && (
            <p className="text-gray-400">{project.description}</p>
          )}
          <p className="text-sm text-gray-500 mt-2">📁 {project.path}</p>
        </div>

        {/* Ingestion Section */}
        <div className="bg-gray-900 rounded-lg border border-gray-800 p-6 mb-6">
          <h2 className="text-2xl font-semibold text-white mb-4">
            Ingesta de Archivos
          </h2>

          <p className="text-gray-400 mb-4">
            Coloca archivos FITS en la carpeta <code className="bg-gray-800 px-2 py-1 rounded">00_ingest/</code> y haz clic en organizar.
          </p>

          {/* Statistics */}
          {ingestStats && ingestStats.total_files > 0 && (
            <div className="bg-gray-800 rounded-lg p-4 mb-4">
              <h3 className="text-lg font-semibold text-white mb-3">
                Archivos Detectados: {ingestStats.total_files}
              </h3>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {/* By Type */}
                {Object.keys(ingestStats.by_type).length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-400 mb-2">Por Tipo</h4>
                    {Object.entries(ingestStats.by_type).map(([type, count]) => (
                      <div key={type} className="text-sm text-gray-300">
                        {type}: {count as number}
                      </div>
                    ))}
                  </div>
                )}

                {/* By Filter */}
                {Object.keys(ingestStats.by_filter).length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-400 mb-2">Por Filtro</h4>
                    {Object.entries(ingestStats.by_filter).map(([filter, count]) => (
                      <div key={filter} className="text-sm text-gray-300">
                        {filter}: {count as number}
                      </div>
                    ))}
                  </div>
                )}

                {/* By Object */}
                {Object.keys(ingestStats.by_object).length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-400 mb-2">Por Objeto</h4>
                    {Object.entries(ingestStats.by_object).map(([obj, count]) => (
                      <div key={obj} className="text-sm text-gray-300 truncate" title={obj}>
                        {obj}: {count as number}
                      </div>
                    ))}
                  </div>
                )}

                {/* By Date */}
                {Object.keys(ingestStats.by_date).length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-400 mb-2">Por Fecha</h4>
                    {Object.entries(ingestStats.by_date).map(([date, count]) => (
                      <div key={date} className="text-sm text-gray-300">
                        {date}: {count as number}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Organization Controls */}
          <div className="flex gap-3 items-end">
            <div className="flex-1">
              <label htmlFor="session" className="block text-sm font-medium text-gray-300 mb-2">
                Nombre de Sesión de Calibración (opcional)
              </label>
              <input
                type="text"
                id="session"
                value={sessionName}
                onChange={(e) => setSessionName(e.target.value)}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Ej: 2025-01-22_Newton200_ASI533"
              />
            </div>
            <button
              onClick={handleOrganizeFiles}
              disabled={organizing || ingestFiles.length === 0}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-md transition-colors font-medium"
            >
              {organizing ? 'Organizando...' : 'Organizar Archivos'}
            </button>
          </div>

          {ingestFiles.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No hay archivos en la carpeta de ingesta
            </div>
          )}
        </div>

        {/* File List */}
        {ingestFiles.length > 0 && (
          <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
            <h3 className="text-xl font-semibold text-white mb-4">
              Archivos Detectados ({ingestFiles.length})
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-left border-b border-gray-800">
                  <tr className="text-gray-400">
                    <th className="pb-2 pr-4">Archivo</th>
                    <th className="pb-2 pr-4">Tipo</th>
                    <th className="pb-2 pr-4">Objeto</th>
                    <th className="pb-2 pr-4">Filtro</th>
                    <th className="pb-2 pr-4">Exp</th>
                    <th className="pb-2">Gain</th>
                  </tr>
                </thead>
                <tbody className="text-gray-300">
                  {ingestFiles.slice(0, 50).map((file, idx) => (
                    <tr key={idx} className="border-b border-gray-800/50">
                      <td className="py-2 pr-4 font-mono text-xs truncate max-w-xs" title={file.filename}>
                        {file.filename}
                      </td>
                      <td className="py-2 pr-4">
                        <span className={`px-2 py-1 rounded text-xs ${
                          file.image_type === 'Light' ? 'bg-green-900/30 text-green-400' :
                          file.image_type === 'Dark' ? 'bg-blue-900/30 text-blue-400' :
                          file.image_type === 'Flat' ? 'bg-yellow-900/30 text-yellow-400' :
                          file.image_type === 'Bias' ? 'bg-purple-900/30 text-purple-400' :
                          'bg-gray-800 text-gray-400'
                        }`}>
                          {file.image_type || 'N/A'}
                        </span>
                      </td>
                      <td className="py-2 pr-4 truncate max-w-xs" title={file.object_name || ''}>
                        {file.object_name || '-'}
                      </td>
                      <td className="py-2 pr-4">{file.filter || '-'}</td>
                      <td className="py-2 pr-4">{file.exposure_time ? `${file.exposure_time}s` : '-'}</td>
                      <td className="py-2">{file.gain || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {ingestFiles.length > 50 && (
                <div className="text-center text-gray-500 text-sm mt-4">
                  Mostrando 50 de {ingestFiles.length} archivos
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
