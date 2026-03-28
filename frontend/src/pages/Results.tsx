export default function Results() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <nav className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                Results
              </h1>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 px-4">
        <div className="card">
          <p className="text-gray-500 dark:text-gray-400 text-center">
            No results yet. Start an assessment to see your triage report.
          </p>
        </div>
      </main>
    </div>
  )
}
