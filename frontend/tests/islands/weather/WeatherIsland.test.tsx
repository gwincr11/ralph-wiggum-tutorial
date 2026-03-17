/**
 * WeatherIsland component tests.
 *
 * Tests the weather island's core functionality:
 * - Rendering loading state
 * - Displaying weather data after successful fetch
 * - Hiding widget when geolocation denied
 * - Hiding widget when API returns error
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { WeatherIsland } from '@/islands/weather/WeatherIsland'

// Mock weather data
const mockWeatherData = {
  current: {
    name: 'Today',
    temperature: 72,
    unit: 'F',
    shortForecast: 'Sunny',
    icon: 'https://api.weather.gov/icons/day/few',
    isDaytime: true,
  },
  periods: [
    {
      name: 'Tonight',
      temperature: 55,
      unit: 'F',
      shortForecast: 'Clear',
      icon: 'https://api.weather.gov/icons/night/few',
      isDaytime: false,
    },
    {
      name: 'Tuesday',
      temperature: 75,
      unit: 'F',
      shortForecast: 'Partly Cloudy',
      icon: 'https://api.weather.gov/icons/day/sct',
      isDaytime: true,
    },
  ],
}

describe('WeatherIsland', () => {
  // Store original implementations
  const originalGeolocation = navigator.geolocation
  const originalFetch = global.fetch

  beforeEach(() => {
    vi.resetAllMocks()
  })

  afterEach(() => {
    // Restore original implementations
    Object.defineProperty(navigator, 'geolocation', {
      value: originalGeolocation,
      writable: true,
    })
    global.fetch = originalFetch
  })

  it('renders loading state initially', () => {
    // Mock geolocation that never resolves
    Object.defineProperty(navigator, 'geolocation', {
      value: {
        getCurrentPosition: vi.fn(),
      },
      writable: true,
    })

    render(<WeatherIsland />)

    // Should show loading skeleton
    const skeleton = document.querySelector('.animate-pulse')
    expect(skeleton).toBeInTheDocument()
  })

  it('renders weather data after successful fetch', async () => {
    // Mock successful geolocation
    Object.defineProperty(navigator, 'geolocation', {
      value: {
        getCurrentPosition: vi.fn((success) => {
          success({
            coords: { latitude: 37.7749, longitude: -122.4194 },
          })
        }),
      },
      writable: true,
    })

    // Mock successful fetch
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockWeatherData),
    })

    render(<WeatherIsland />)

    // Wait for weather data to load
    await waitFor(() => {
      expect(screen.getByText('72°F')).toBeInTheDocument()
    })

    expect(screen.getByText('Today')).toBeInTheDocument()
    expect(screen.getByText('Sunny')).toBeInTheDocument()
  })

  it('renders nothing when geolocation denied', async () => {
    // Mock denied geolocation
    Object.defineProperty(navigator, 'geolocation', {
      value: {
        getCurrentPosition: vi.fn((_success, error) => {
          error({ code: 1, message: 'User denied' })
        }),
      },
      writable: true,
    })

    const { container } = render(<WeatherIsland />)

    // Wait for denied state to be processed
    await waitFor(() => {
      // Component should render nothing (null)
      expect(container.firstChild).toBeNull()
    })
  })

  it('renders nothing when API returns error', async () => {
    // Mock successful geolocation
    Object.defineProperty(navigator, 'geolocation', {
      value: {
        getCurrentPosition: vi.fn((success) => {
          success({
            coords: { latitude: 37.7749, longitude: -122.4194 },
          })
        }),
      },
      writable: true,
    })

    // Mock failed fetch
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 502,
    })

    const { container } = render(<WeatherIsland />)

    // Wait for error state to be processed
    await waitFor(() => {
      expect(container.firstChild).toBeNull()
    })
  })

  it('displays current temperature and forecast', async () => {
    // Mock successful geolocation
    Object.defineProperty(navigator, 'geolocation', {
      value: {
        getCurrentPosition: vi.fn((success) => {
          success({
            coords: { latitude: 37.7749, longitude: -122.4194 },
          })
        }),
      },
      writable: true,
    })

    // Mock successful fetch
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockWeatherData),
    })

    render(<WeatherIsland />)

    await waitFor(() => {
      expect(screen.getByText('72°F')).toBeInTheDocument()
      expect(screen.getByText('Sunny')).toBeInTheDocument()
    })
  })

  it('displays forecast periods', async () => {
    // Mock successful geolocation
    Object.defineProperty(navigator, 'geolocation', {
      value: {
        getCurrentPosition: vi.fn((success) => {
          success({
            coords: { latitude: 37.7749, longitude: -122.4194 },
          })
        }),
      },
      writable: true,
    })

    // Mock successful fetch
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockWeatherData),
    })

    render(<WeatherIsland />)

    await waitFor(() => {
      expect(screen.getByText('Tonight')).toBeInTheDocument()
      expect(screen.getByText('Tuesday')).toBeInTheDocument()
      expect(screen.getByText('55°')).toBeInTheDocument()
      expect(screen.getByText('75°')).toBeInTheDocument()
    })
  })

  it('renders nothing when geolocation not available', async () => {
    // Mock missing geolocation API
    Object.defineProperty(navigator, 'geolocation', {
      value: undefined,
      writable: true,
    })

    const { container } = render(<WeatherIsland />)

    await waitFor(() => {
      expect(container.firstChild).toBeNull()
    })
  })
})
