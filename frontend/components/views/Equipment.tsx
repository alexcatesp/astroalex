'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';

interface EquipmentProps {
  onNavigate: (view: string) => void;
}

export default function Equipment({ onNavigate }: EquipmentProps) {
  const [profiles, setProfiles] = useState<any[]>([]);
  const [activeProfile, setActiveProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingProfile, setEditingProfile] = useState<any>(null);

  useEffect(() => {
    loadProfiles();
  }, []);

  const loadProfiles = async () => {
    try {
      const [profilesList, active] = await Promise.all([
        apiClient.getEquipmentProfiles(),
        apiClient.getActiveEquipmentProfile().catch(() => null),
      ]);
      setProfiles(profilesList);
      setActiveProfile(active);
    } catch (error) {
      console.error('Error loading profiles:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleActivate = async (id: string) => {
    try {
      await apiClient.activateEquipmentProfile(id);
      await loadProfiles();
    } catch (error) {
      console.error('Error activating profile:', error);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('¿Eliminar este perfil de equipo?')) return;
    try {
      await apiClient.deleteEquipmentProfile(id);
      await loadProfiles();
    } catch (error) {
      console.error('Error deleting profile:', error);
    }
  };

  const handleEdit = (profile: any) => {
    setEditingProfile(profile);
    setShowForm(true);
  };

  const handleCreate = () => {
    setEditingProfile(null);
    setShowForm(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-400">Cargando equipos...</div>
      </div>
    );
  }

  if (showForm) {
    return (
      <EquipmentForm
        profile={editingProfile}
        onClose={() => {
          setShowForm(false);
          setEditingProfile(null);
        }}
        onSave={async () => {
          await loadProfiles();
          setShowForm(false);
          setEditingProfile(null);
        }}
      />
    );
  }

  return (
    <div className="max-w-6xl mx-auto py-8 px-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">
            Perfiles de Equipo
          </h1>
          <p className="text-gray-400">
            Gestiona tus cámaras, telescopios y filtros
          </p>
        </div>
        <button
          onClick={handleCreate}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-all shadow-lg"
        >
          + Nuevo Perfil
        </button>
      </div>

      {/* Profiles List */}
      {profiles.length === 0 ? (
        <div className="bg-gray-800 rounded-xl p-12 text-center border border-gray-700">
          <div className="text-5xl mb-4">📷</div>
          <h3 className="text-xl font-semibold text-white mb-2">
            No hay perfiles de equipo
          </h3>
          <p className="text-gray-400 mb-6">
            Crea tu primer perfil para comenzar
          </p>
          <button
            onClick={handleCreate}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-all"
          >
            Crear Primer Perfil
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {profiles.map((profile) => (
            <div
              key={profile.id}
              className={`bg-gray-800 rounded-xl p-6 border-2 transition-all ${
                profile.is_active
                  ? 'border-blue-600 shadow-lg shadow-blue-900/50'
                  : 'border-gray-700 hover:border-gray-600'
              }`}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-xl font-bold text-white">
                      {profile.name}
                    </h3>
                    {profile.is_active && (
                      <span className="px-3 py-1 bg-blue-600 text-white text-xs font-medium rounded-full">
                        ACTIVO
                      </span>
                    )}
                  </div>
                  {profile.description && (
                    <p className="text-gray-400 text-sm">{profile.description}</p>
                  )}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleEdit(profile)}
                    className="px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
                  >
                    ✏️ Editar
                  </button>
                  {!profile.is_active && (
                    <button
                      onClick={() => handleActivate(profile.id)}
                      className="px-3 py-2 bg-blue-900 hover:bg-blue-800 text-blue-200 rounded-lg transition-colors"
                    >
                      Activar
                    </button>
                  )}
                  <button
                    onClick={() => handleDelete(profile.id)}
                    className="px-3 py-2 bg-red-900 hover:bg-red-800 text-red-200 rounded-lg transition-colors"
                  >
                    🗑️
                  </button>
                </div>
              </div>

              {/* Equipment Details */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Camera */}
                <div className="bg-gray-900 rounded-lg p-4">
                  <div className="text-xs text-gray-500 mb-2">📷 CÁMARA</div>
                  <div className="font-semibold text-white">{profile.camera.model}</div>
                  <div className="text-sm text-gray-400">{profile.camera.manufacturer}</div>
                  <div className="text-xs text-gray-500 mt-2">
                    {profile.camera.sensor_width} × {profile.camera.sensor_height} px
                    <br />
                    {profile.camera.pixel_size} µm pixel
                    {profile.camera.color && ' • Color'}
                    {profile.camera.cooling && ' • Refrigerada'}
                  </div>
                </div>

                {/* Telescope */}
                <div className="bg-gray-900 rounded-lg p-4">
                  <div className="text-xs text-gray-500 mb-2">🔭 TELESCOPIO</div>
                  <div className="font-semibold text-white">{profile.telescope.name}</div>
                  <div className="text-sm text-gray-400">{profile.telescope.manufacturer}</div>
                  <div className="text-xs text-gray-500 mt-2">
                    FL: {profile.telescope.focal_length}mm
                    <br />
                    Apertura: {profile.telescope.aperture}mm
                    <br />
                    f/{profile.telescope.focal_ratio.toFixed(1)}
                  </div>
                </div>

                {/* Computed Values */}
                <div className="bg-gray-900 rounded-lg p-4">
                  <div className="text-xs text-gray-500 mb-2">📊 CALCULADO</div>
                  <div className="space-y-1">
                    <div className="text-sm">
                      <span className="text-gray-400">FOV:</span>{' '}
                      <span className="text-white font-mono">
                        {(profile.telescope.focal_length && profile.camera.sensor_width ?
                          (2 * (180 / Math.PI) * Math.atan((profile.camera.sensor_width * profile.camera.pixel_size / 1000) / (2 * profile.telescope.focal_length))).toFixed(2)
                          : '---')}°
                      </span>
                    </div>
                    <div className="text-sm">
                      <span className="text-gray-400">Pixel Scale:</span>{' '}
                      <span className="text-white font-mono">
                        {(206.265 * profile.camera.pixel_size / profile.telescope.focal_length).toFixed(2)}""/px
                      </span>
                    </div>
                    {profile.filters && profile.filters.length > 0 && (
                      <div className="text-xs text-gray-500 mt-2">
                        {profile.filters.length} filtro{profile.filters.length > 1 ? 's' : ''}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Equipment Form Component (simplified version)
function EquipmentForm({ profile, onClose, onSave }: any) {
  const [formData, setFormData] = useState({
    name: profile?.name || '',
    description: profile?.description || '',
    camera: {
      model: profile?.camera?.model || '',
      manufacturer: profile?.camera?.manufacturer || '',
      sensor_width: profile?.camera?.sensor_width || 4144,
      sensor_height: profile?.camera?.sensor_height || 2822,
      pixel_size: profile?.camera?.pixel_size || 4.63,
      color: profile?.camera?.color ?? true,
      cooling: profile?.camera?.cooling ?? true,
      bit_depth: profile?.camera?.bit_depth || 16,
    },
    telescope: {
      name: profile?.telescope?.name || '',
      manufacturer: profile?.telescope?.manufacturer || '',
      focal_length: profile?.telescope?.focal_length || 600,
      aperture: profile?.telescope?.aperture || 80,
      telescope_type: profile?.telescope?.telescope_type || 'refractor',
    },
    filters: profile?.filters || [],
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (profile) {
        await apiClient.updateEquipmentProfile(profile.id, formData);
      } else {
        await apiClient.createEquipmentProfile(formData);
      }
      onSave();
    } catch (error) {
      console.error('Error saving profile:', error);
      alert('Error al guardar el perfil');
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white mb-2">
          {profile ? 'Editar Perfil' : 'Nuevo Perfil de Equipo'}
        </h1>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Info */}
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-4">Información Básica</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Nombre del Perfil *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-blue-600"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Descripción
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-blue-600"
                rows={2}
              />
            </div>
          </div>
        </div>

        {/* Camera */}
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-4">📷 Cámara</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Modelo *</label>
              <input
                type="text"
                value={formData.camera.model}
                onChange={(e) => setFormData({ ...formData, camera: { ...formData.camera, model: e.target.value } })}
                className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-blue-600"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Fabricante *</label>
              <input
                type="text"
                value={formData.camera.manufacturer}
                onChange={(e) => setFormData({ ...formData, camera: { ...formData.camera, manufacturer: e.target.value } })}
                className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-blue-600"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Sensor Width (px)</label>
              <input
                type="number"
                value={formData.camera.sensor_width}
                onChange={(e) => setFormData({ ...formData, camera: { ...formData.camera, sensor_width: parseInt(e.target.value) } })}
                className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-blue-600"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Pixel Size (µm)</label>
              <input
                type="number"
                step="0.01"
                value={formData.camera.pixel_size}
                onChange={(e) => setFormData({ ...formData, camera: { ...formData.camera, pixel_size: parseFloat(e.target.value) } })}
                className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-blue-600"
              />
            </div>
          </div>
        </div>

        {/* Telescope */}
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-4">🔭 Telescopio</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Nombre *</label>
              <input
                type="text"
                value={formData.telescope.name}
                onChange={(e) => setFormData({ ...formData, telescope: { ...formData.telescope, name: e.target.value } })}
                className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-blue-600"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Fabricante</label>
              <input
                type="text"
                value={formData.telescope.manufacturer}
                onChange={(e) => setFormData({ ...formData, telescope: { ...formData.telescope, manufacturer: e.target.value } })}
                className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-blue-600"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Focal Length (mm) *</label>
              <input
                type="number"
                value={formData.telescope.focal_length}
                onChange={(e) => setFormData({ ...formData, telescope: { ...formData.telescope, focal_length: parseInt(e.target.value) } })}
                className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-blue-600"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Apertura (mm) *</label>
              <input
                type="number"
                value={formData.telescope.aperture}
                onChange={(e) => setFormData({ ...formData, telescope: { ...formData.telescope, aperture: parseInt(e.target.value) } })}
                className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-blue-600"
                required
              />
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-4">
          <button
            type="button"
            onClick={onClose}
            className="px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
          >
            Cancelar
          </button>
          <button
            type="submit"
            className="flex-1 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-all shadow-lg"
          >
            {profile ? 'Guardar Cambios' : 'Crear Perfil'}
          </button>
        </div>
      </form>
    </div>
  );
}
