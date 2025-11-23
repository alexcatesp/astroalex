'use client';

export default function Step3TargetSelection({ session, onComplete, onBack }: any) {
  return (
    <div className="max-w-4xl mx-auto py-8 px-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">
          Step 3: Selección de Objetivo
        </h1>
        <p className="text-gray-400">
          Encuentra el objetivo perfecto para las condiciones actuales
        </p>
      </div>

      <div className="bg-gradient-to-br from-green-900/30 to-emerald-900/30 rounded-xl p-12 border border-green-800/50 text-center">
        <div className="text-6xl mb-6">🎯</div>
        <h3 className="text-2xl font-bold text-white mb-4">
          Próximamente
        </h3>
        <p className="text-gray-300 mb-8">
          Sugerencias inteligentes basadas en FOV, tiempo disponible, fase lunar y ubicación
        </p>
      </div>

      <div className="flex gap-4 mt-8">
        <button
          onClick={onBack}
          className="px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
        >
          ← Atrás
        </button>
        <button
          onClick={() => onComplete({})}
          className="flex-1 px-6 py-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-all shadow-lg"
        >
          Continuar al Paso 4 (Skip) →
        </button>
      </div>
    </div>
  );
}
