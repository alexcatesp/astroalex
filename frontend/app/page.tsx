'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import { Project } from '@/shared/types';
import ProjectCard from '@/components/ProjectCard';
import CreateProjectModal from '@/components/CreateProjectModal';

export default function Home() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const loadProjects = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.getProjects();
      setProjects(data);
    } catch (err) {
      setError('Error al cargar proyectos. Asegúrate de que el backend esté ejecutándose.');
      console.error('Error loading projects:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  const handleCreateProject = async (name: string, description?: string) => {
    try {
      await apiClient.createProject({ name, description });
      await loadProjects();
    } catch (err: any) {
      alert(`Error al crear proyecto: ${err.message}`);
    }
  };

  const handleDeleteProject = async (id: string) => {
    try {
      await apiClient.deleteProject(id, false);
      await loadProjects();
    } catch (err: any) {
      alert(`Error al eliminar proyecto: ${err.message}`);
    }
  };

  return (
    <div className="min-h-screen p-8">
      <main className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-500 to-purple-600 bg-clip-text text-transparent mb-2">
            Astroalex
          </h1>
          <p className="text-xl text-gray-400">
            Tu pipeline de procesamiento astrofotográfico
          </p>
        </div>

        {/* Projects Section */}
        <div className="mb-6 flex justify-between items-center">
          <h2 className="text-2xl font-semibold text-white">Proyectos</h2>
          <button
            onClick={() => setIsModalOpen(true)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
          >
            + Nuevo Proyecto
          </button>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-12 text-gray-400">
            Cargando proyectos...
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-900/20 border border-red-800 rounded-lg p-4 text-red-400 mb-6">
            {error}
          </div>
        )}

        {/* Projects Grid */}
        {!loading && !error && (
          <>
            {projects.length === 0 ? (
              <div className="text-center py-12 bg-gray-900 rounded-lg border border-gray-800">
                <p className="text-gray-400 mb-4">
                  No hay proyectos todavía
                </p>
                <button
                  onClick={() => setIsModalOpen(true)}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
                >
                  Crear tu primer proyecto
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {projects.map((project) => (
                  <ProjectCard
                    key={project.id}
                    project={project}
                    onDelete={handleDeleteProject}
                  />
                ))}
              </div>
            )}
          </>
        )}

        {/* Create Project Modal */}
        <CreateProjectModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onCreate={handleCreateProject}
        />
      </main>
    </div>
  );
}
