export default function Home() {
  return (
    <div className="min-h-screen flex items-center justify-center p-8">
      <main className="max-w-4xl w-full">
        <div className="text-center space-y-6">
          <h1 className="text-6xl font-bold bg-gradient-to-r from-blue-500 to-purple-600 bg-clip-text text-transparent">
            Astroalex
          </h1>
          <p className="text-xl text-gray-400">
            Tu pipeline de procesamiento astrofotográfico, automatizado e inteligente
          </p>
          <div className="mt-8 p-6 bg-gray-900 rounded-lg border border-gray-800">
            <h2 className="text-2xl font-semibold mb-4">Estado del Proyecto</h2>
            <p className="text-gray-400">
              Configuración inicial completada. Frontend Next.js 15 listo.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
