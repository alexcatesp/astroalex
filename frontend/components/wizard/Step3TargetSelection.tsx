'use client';

import { useState, useEffect } from 'react';

interface Step3Props {
  session: any;
  onComplete: (data: any) => void;
  onBack: () => void;
}

// Mock database - en producción vendría del backend
const CELESTIAL_OBJECTS = [
  {
    id: 'm31',
    name: 'M31 - Galaxia de Andrómeda',
    type: 'Galaxy',
    ra: 10.685,
    dec: 41.269,
    size: 178, // arcminutes
    magnitude: 3.4,
    surfaceBrightness: 13.5,
    bestFilters: ['L', 'R', 'G', 'B'],
    season: 'autumn',
    difficulty: 'easy',
  },
  {
    id: 'm42',
    name: 'M42 - Nebulosa de Orión',
    type: 'Nebula',
    ra: 83.822,
    dec: -5.391,
    size: 65,
    magnitude: 4.0,
    surfaceBrightness: 17.0,
    bestFilters: ['Ha', 'OIII', 'SII', 'L'],
    season: 'winter',
    difficulty: 'easy',
  },
  {
    id: 'm51',
    name: 'M51 - Galaxia Remolino',
    type: 'Galaxy',
    ra: 202.470,
    dec: 47.195,
    size: 11,
    magnitude: 8.4,
    surfaceBrightness: 13.0,
    bestFilters: ['L', 'R', 'G', 'B', 'Ha'],
    season: 'spring',
    difficulty: 'medium',
  },
  {
    id: 'm27',
    name: 'M27 - Nebulosa Dumbbell',
    type: 'Planetary Nebula',
    ra: 299.901,
    dec: 22.721,
    size: 8,
    magnitude: 7.5,
    surfaceBrightness: 15.6,
    bestFilters: ['OIII', 'Ha', 'L'],
    season: 'summer',
    difficulty: 'medium',
  },
  {
    id: 'ngc7000',
    name: 'NGC 7000 - Nebulosa Norteamérica',
    type: 'Nebula',
    ra: 312.250,
    dec: 44.333,
    size: 120,
    magnitude: 4.0,
    surfaceBrightness: 22.0,
    bestFilters: ['Ha', 'OIII', 'SII'],
    season: 'summer',
    difficulty: 'easy',
  },
  {
    id: 'ic1396',
    name: 'IC 1396 - Nebulosa Trompa de Elefante',
    type: 'Nebula',
    ra: 324.042,
    dec: 57.500,
    size: 170,
    magnitude: 3.5,
    surfaceBrightness: 21.1,
    bestFilters: ['Ha', 'OIII', 'SII'],
    season: 'summer',
    difficulty: 'medium',
  },
];

export default function Step3TargetSelection({ session, onComplete, onBack }: Step3Props) {
  const [selectedTarget, setSelectedTarget] = useState<any>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredTargets, setFilteredTargets] = useState<any[]>([]);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [userFilters, setUserFilters] = useState<string[]>([]);
  const [filterByEquipment, setFilterByEquipment] = useState(true);

  useEffect(() => {
    // Cargar filtros del equipo activo
    loadUserFilters();
  }, []);

  useEffect(() => {
    // Generar recomendaciones inteligentes basadas en condiciones
    if (userFilters.length > 0 || !filterByEquipment) {
      generateRecommendations();
      applyFilters();
    }
  }, [userFilters, filterByEquipment]);

  useEffect(() => {
    // Filtrar objetivos por búsqueda
    applyFilters();
  }, [searchQuery]);

  const loadUserFilters = async () => {
    try {
      const response = await fetch('http://localhost:8000/equipment/profiles/active');
      if (response.ok) {
        const profile = await response.json();
        // Extraer nombres de filtros del equipo
        const filters = profile.filters?.map((f: any) => f.name || f) || [];
        setUserFilters(filters);
      }
    } catch (error) {
      console.error('Error loading equipment filters:', error);
      // Si no hay equipo configurado, mostrar todos los objetivos
      setFilterByEquipment(false);
      setUserFilters([]);
    }
  };

  const applyFilters = () => {
    let targets = CELESTIAL_OBJECTS;

    // Filtrar por filtros de equipamiento
    if (filterByEquipment && userFilters.length > 0) {
      targets = targets.filter((obj) => {
        // Un objetivo es compatible si al menos uno de sus filtros recomendados está disponible
        return obj.bestFilters.some((filter) => userFilters.includes(filter));
      });
    }

    // Filtrar por búsqueda
    if (searchQuery) {
      targets = targets.filter((obj) =>
        obj.name.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    setFilteredTargets(targets);
  };

  const generateRecommendations = () => {
    // Lógica de recomendación basada en:
    // - Moon phase del session
    // - Seeing conditions
    // - Equipment filters (filtrado por equipamiento)

    const moonIllumination = session.ephemeris?.moon_illumination || 50;
    const seeing = session.conditions?.seeing || 2.5;

    let candidateObjects = CELESTIAL_OBJECTS;

    // FILTRADO CRÍTICO: Solo objetivos compatibles con filtros del usuario
    if (filterByEquipment && userFilters.length > 0) {
      candidateObjects = candidateObjects.filter((obj) =>
        obj.bestFilters.some((filter) => userFilters.includes(filter))
      );
    }

    let recommended = candidateObjects.map((obj) => {
      let score = 100;

      // Penalizar objetos débiles si hay luna
      if (moonIllumination > 50) {
        if (obj.surfaceBrightness > 18) score -= 30;
        if (obj.type === 'Nebula') score -= 20;
      } else {
        // Favorecer nebulosas en luna nueva
        if (obj.type === 'Nebula') score += 20;
      }

      // Penalizar objetos pequeños si el seeing es malo
      if (seeing > 3 && obj.size < 20) {
        score -= 25;
      }

      // Favorecer objetos grandes y brillantes para principiantes
      if (obj.difficulty === 'easy') score += 15;
      if (obj.size > 60) score += 10;

      // Bonus si el usuario tiene TODOS los filtros recomendados
      const hasAllFilters = obj.bestFilters.every((filter) =>
        userFilters.includes(filter)
      );
      if (hasAllFilters) score += 25;

      return { ...obj, score };
    });

    // Ordenar por score y tomar top 3
    recommended.sort((a, b) => b.score - a.score);
    setRecommendations(recommended.slice(0, 3));
  };

  const handleSelectTarget = (target: any) => {
    setSelectedTarget(target);
  };

  const handleContinue = async () => {
    if (!selectedTarget) return;

    try {
      // Enviar selección al backend
      const response = await fetch(
        `http://localhost:8000/sessions/${session.id}/step3/select`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            target_name: selectedTarget.name,
            target_id: selectedTarget.id,
            ra: selectedTarget.ra,
            dec: selectedTarget.dec,
          }),
        }
      );

      if (!response.ok) throw new Error('Error selecting target');

      onComplete(selectedTarget);
    } catch (error) {
      console.error('Error:', error);
      // Continuar de todos modos con el target seleccionado
      onComplete(selectedTarget);
    }
  };

  return (
    <div className="max-w-6xl mx-auto py-8 px-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">
          Step 3: Selección de Objetivo
        </h1>
        <p className="text-gray-400">
          Elige el objetivo perfecto para las condiciones de esta noche
        </p>
      </div>

      {/* Equipment Filters Info */}
      {userFilters.length > 0 && (
        <div className="mb-6 bg-blue-900/20 border border-blue-800 rounded-xl p-4">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-blue-300 mb-2 flex items-center gap-2">
                <span>🔭</span> Filtros de tu Equipo
              </h3>
              <div className="flex flex-wrap gap-2">
                {userFilters.map((filter) => (
                  <span
                    key={filter}
                    className="px-3 py-1 bg-blue-700 rounded-full text-xs text-white font-medium"
                  >
                    {filter}
                  </span>
                ))}
              </div>
            </div>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={filterByEquipment}
                onChange={(e) => setFilterByEquipment(e.target.checked)}
                className="w-4 h-4"
              />
              <span className="text-xs text-gray-300">Filtrar por equipo</span>
            </label>
          </div>
          {filterByEquipment && (
            <p className="text-xs text-blue-200 mt-2">
              ℹ️ Mostrando solo objetivos compatibles con tus filtros
            </p>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Panel - Recommendations */}
        <div className="lg:col-span-1">
          <div className="bg-gradient-to-br from-green-900/30 to-emerald-900/30 rounded-xl p-6 border border-green-800/50 sticky top-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <span>🤖</span> Recomendaciones
            </h3>
            <p className="text-sm text-gray-300 mb-4">
              Basado en luna {session.ephemeris?.moon_illumination || 0}%, seeing{' '}
              {session.conditions?.seeing || 'N/A'}"
            </p>

            <div className="space-y-3">
              {recommendations.map((target, index) => (
                <button
                  key={target.id}
                  onClick={() => handleSelectTarget(target)}
                  className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                    selectedTarget?.id === target.id
                      ? 'bg-green-600 border-green-400'
                      : 'bg-gray-800 border-gray-700 hover:border-green-600'
                  }`}
                >
                  <div className="flex items-start gap-2">
                    <div className="text-xl font-bold text-green-400">
                      #{index + 1}
                    </div>
                    <div className="flex-1">
                      <div className="font-medium text-white text-sm">
                        {target.name}
                      </div>
                      <div className="text-xs text-gray-400 mt-1">
                        {target.type} • {target.size}' • Mag {target.magnitude}
                      </div>
                      <div className="mt-2 flex flex-wrap gap-1">
                        {target.bestFilters.slice(0, 3).map((filter: string) => (
                          <span
                            key={filter}
                            className="px-2 py-0.5 bg-gray-700 rounded text-xs text-gray-300"
                          >
                            {filter}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>

            {selectedTarget && (
              <button
                onClick={handleContinue}
                className="w-full mt-6 px-4 py-3 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-lg transition-all shadow-lg"
              >
                Usar {selectedTarget.name.split('-')[0]} →
              </button>
            )}
          </div>
        </div>

        {/* Right Panel - All Targets */}
        <div className="lg:col-span-2">
          {/* Search */}
          <div className="mb-6">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Buscar objetivo (M31, NGC 7000, Orion...)"
              className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-blue-600"
            />
          </div>

          {/* Target Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredTargets.map((target) => (
              <button
                key={target.id}
                onClick={() => handleSelectTarget(target)}
                className={`text-left p-6 rounded-xl border-2 transition-all ${
                  selectedTarget?.id === target.id
                    ? 'bg-blue-900/40 border-blue-600 shadow-lg shadow-blue-900/50'
                    : 'bg-gray-800 border-gray-700 hover:border-gray-600'
                }`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h4 className="font-bold text-white text-lg">
                      {target.name.split('-')[0]}
                    </h4>
                    <p className="text-sm text-gray-400">
                      {target.name.split('-')[1]?.trim() || target.type}
                    </p>
                  </div>
                  {selectedTarget?.id === target.id && (
                    <div className="text-2xl">✓</div>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-2 text-sm mb-3">
                  <div>
                    <span className="text-gray-400">Tipo:</span>{' '}
                    <span className="text-white">{target.type}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Tamaño:</span>{' '}
                    <span className="text-white">{target.size}'</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Mag:</span>{' '}
                    <span className="text-white">{target.magnitude}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">SB:</span>{' '}
                    <span className="text-white">{target.surfaceBrightness}</span>
                  </div>
                </div>

                <div>
                  <div className="text-xs text-gray-400 mb-1">Filtros recomendados:</div>
                  <div className="flex flex-wrap gap-1">
                    {target.bestFilters.map((filter: string) => (
                      <span
                        key={filter}
                        className="px-2 py-1 bg-gray-700 rounded text-xs text-gray-300"
                      >
                        {filter}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="mt-3">
                  <span
                    className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                      target.difficulty === 'easy'
                        ? 'bg-green-900 text-green-300'
                        : target.difficulty === 'medium'
                        ? 'bg-yellow-900 text-yellow-300'
                        : 'bg-red-900 text-red-300'
                    }`}
                  >
                    {target.difficulty === 'easy'
                      ? '🟢 Fácil'
                      : target.difficulty === 'medium'
                      ? '🟡 Intermedio'
                      : '🔴 Difícil'}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

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
          disabled={!selectedTarget}
          className="flex-1 px-6 py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white font-semibold rounded-lg transition-all shadow-lg disabled:cursor-not-allowed"
        >
          {selectedTarget
            ? `Continuar con ${selectedTarget.name.split('-')[0]} →`
            : 'Selecciona un objetivo'}
        </button>
      </div>
    </div>
  );
}
