'use client';

import { Project } from '@/shared/types';
import Link from 'next/link';

interface ProjectCardProps {
  project: Project;
  onDelete?: (id: string) => void;
}

export default function ProjectCard({ project, onDelete }: ProjectCardProps) {
  const handleDelete = (e: React.MouseEvent) => {
    e.preventDefault();
    if (confirm(`¿Eliminar el proyecto "${project.name}"?`)) {
      onDelete?.(project.id);
    }
  };

  return (
    <Link href={`/projects/${project.id}`}>
      <div className="block p-6 bg-gray-900 rounded-lg border border-gray-800 hover:border-blue-500 transition-colors cursor-pointer">
        <div className="flex justify-between items-start mb-2">
          <h3 className="text-xl font-semibold text-white">{project.name}</h3>
          {onDelete && (
            <button
              onClick={handleDelete}
              className="text-red-400 hover:text-red-300 text-sm"
              title="Eliminar proyecto"
            >
              🗑️
            </button>
          )}
        </div>

        {project.description && (
          <p className="text-gray-400 text-sm mb-3">{project.description}</p>
        )}

        <div className="text-xs text-gray-500 space-y-1">
          <div>
            Creado: {new Date(project.created_at).toLocaleDateString('es-ES')}
          </div>
          <div className="truncate" title={project.path}>
            📁 {project.path}
          </div>
        </div>
      </div>
    </Link>
  );
}
