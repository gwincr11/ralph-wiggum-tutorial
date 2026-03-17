/**
 * Weather island mount function.
 * 
 * Called by the island registry when a [data-island="weather"] element
 * is found in the DOM. No props needed since weather data comes from
 * browser geolocation + API call.
 */
import { createRoot } from 'react-dom/client'
import { WeatherIsland } from './WeatherIsland'

export function mount(element: HTMLElement, _props: unknown): void {
  // Clear loading placeholder
  element.innerHTML = ''
  
  // Mount the React component
  const root = createRoot(element)
  root.render(<WeatherIsland />)
}
