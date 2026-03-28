export default function Chat() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <nav className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                Symptom Assessment
              </h1>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto py-6 px-4">
        <div className="card h-[600px] flex flex-col">
          <div className="flex-1 overflow-y-auto mb-4 p-4 border rounded-lg bg-gray-50 dark:bg-gray-700">
            <p className="text-gray-500 dark:text-gray-400 text-center mt-8">
              Start chatting with our AI assistant about your symptoms...
            </p>
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Describe your symptoms..."
              className="input-field flex-1"
            />
            <button className="btn-primary">
              Send
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}
