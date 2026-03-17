/**
 * Comic Island mount logic.
 *
 * This module is dynamically imported by main.ts when a
 * [data-island="comic-generator"] element is found in the DOM.
 */
import { createRoot } from 'react-dom/client'
import { ComicGenerator } from './ComicGenerator'

/**
 * Mount the ComicGenerator component into the given element.
 *
 * @param element - DOM element to render into
 * @param _props - Initial props (unused for this island)
 */
export function mount(element: HTMLElement, _props: unknown): void {
  // Clear loading placeholder
  element.innerHTML = ''

  // Create React root and render
  const root = createRoot(element)
  root.render(<ComicGenerator />)
}
