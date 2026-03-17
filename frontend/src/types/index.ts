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

/**
 * A single weather forecast period from NWS API.
 */
export interface WeatherPeriod {
  name: string
  temperature: number
  unit: string
  shortForecast: string
  icon: string
  isDaytime: boolean
}

/**
 * Complete weather data with current conditions and forecast.
 */
export interface WeatherData {
  current: WeatherPeriod
  periods: WeatherPeriod[]
}
