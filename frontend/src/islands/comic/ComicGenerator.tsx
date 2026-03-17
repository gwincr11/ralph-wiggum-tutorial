/**
 * ComicGenerator - Interactive comic strip generator component
 *
 * Demonstrates the islands pattern by:
 * - Providing a form to enter a story prompt
 * - Calling the API to generate a 3-panel comic
 * - Displaying generated panels with images and dialogue
 * - Managing loading, error, and success states
 *
 * This island handles its own data fetching and state management,
 * making it self-contained and portable.
 */
import React, { useState } from 'react'
import type { ComicPanel, ComicResponse, ComicGenerateRequest } from '@/types'

export function ComicGenerator() {
  const [prompt, setPrompt] = useState('')
  const [panels, setPanels] = useState<ComicPanel[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!prompt.trim() || loading) return

    setLoading(true)
    setError(null)
    setPanels([])

    try {
      const payload: ComicGenerateRequest = { prompt: prompt.trim() }
      const response = await fetch('/api/comic/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        const errorData = await response.json()
        if (response.status === 429) {
          throw new Error('Rate limit exceeded. Please try again later.')
        } else if (response.status === 503) {
          throw new Error('Comic generation service is temporarily unavailable.')
        }
        throw new Error(errorData.message || errorData.error || 'Failed to generate comic')
      }

      const comic: ComicResponse = await response.json()
      setPanels(comic.panels)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Comic generation form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="prompt" className="block text-sm font-medium text-gray-700 mb-2">
            Enter a funny situation or story idea
          </label>
          <textarea
            id="prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="A cat trying to use a computer..."
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            disabled={loading}
            maxLength={500}
            rows={3}
          />
          <div className="text-sm text-gray-500 mt-1">
            {prompt.length}/500 characters
          </div>
        </div>
        <button
          type="submit"
          disabled={loading || !prompt.trim()}
          className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Generating...
            </>
          ) : (
            'Generate Comic'
          )}
        </button>
      </form>

      {/* Error message */}
      {error && (
        <div className="p-4 bg-red-100 text-red-700 rounded-lg border border-red-200">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Loading skeleton */}
      {loading && (
        <div className="space-y-4">
          <p className="text-gray-600 text-center">Creating your comic... This may take a minute.</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[1, 2, 3].map((n) => (
              <div key={n} className="animate-pulse">
                <div className="bg-gray-200 rounded-lg h-48 mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Comic panels */}
      {panels.length > 0 && !loading && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-800">Your Comic</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {panels.map((panel) => (
              <div
                key={panel.panel_number}
                data-testid={`panel-${panel.panel_number}`}
                className="bg-white border-2 border-gray-800 rounded-lg overflow-hidden shadow-lg"
              >
                {/* Panel image */}
                <div className="aspect-square bg-gray-100 flex items-center justify-center">
                  {panel.image_base64 ? (
                    <img
                      src={`data:image/png;base64,${panel.image_base64}`}
                      alt={panel.description}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="text-center p-4 text-gray-500">
                      <p className="text-sm italic">{panel.description}</p>
                    </div>
                  )}
                </div>
                {/* Panel dialogue */}
                <div className="p-3 bg-white border-t-2 border-gray-800">
                  <p className="text-center font-comic text-gray-800">
                    {panel.dialogue}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
