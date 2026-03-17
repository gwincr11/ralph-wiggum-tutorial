/**
 * Shared TypeScript types for the application.
 *
 * These types are used across islands, components, and API interactions.
 */

/**
 * Hello record from the API.
 */
export interface Hello {
  id: number
  message: string
  created_at: string
}

/**
 * Request payload for creating a new Hello.
 */
export interface HelloCreate {
  message: string
}

/**
 * Comic panel from the API.
 */
export interface ComicPanel {
  panel_number: number
  description: string
  dialogue: string
  image_base64?: string
}

/**
 * Request payload for generating a comic.
 */
export interface ComicGenerateRequest {
  prompt: string
}

/**
 * Response from comic generation API.
 */
export interface ComicResponse {
  prompt: string
  panels: ComicPanel[]
  created_at: string
}

/**
 * Generic API error response.
 */
export interface ApiError {
  error: string
  message: string
  details?: Record<string, unknown>[]
}

/**
 * Props passed to islands via data-props attribute.
 * Each island receives its initial data from the server.
 */
export type IslandProps<T = unknown> = {
  initialData?: T
}
