/**
 * Weather Island mount logic.
 *
 * This module is dynamically imported by main.ts when a
 * [data-island="weather"] element is found in the DOM.
 *
 * The WeatherIsland component handles its own data fetching
 * via geolocation and the /api/weather endpoint, so no server-side
 * props are needed.
 */
import { createRoot } from 'react-dom/client'
import { WeatherIsland } from './WeatherIsland'

/**
 * Mount the WeatherIsland component into the given element.
 *
 * @param element - DOM element to render into
 * @param _props - Unused, weather data is fetched client-side
 */
export function mount(element: HTMLElement, _props: unknown): void {
  // Clear loading placeholder
  element.innerHTML = ''

  // Create React root and render
  const root = createRoot(element)
  root.render(<WeatherIsland />)
}
