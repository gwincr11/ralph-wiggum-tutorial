/**
 * WeatherIsland - Weather forecast display component
 *
 * This island:
 * 1. Uses browser geolocation to get user's location
 * 2. Fetches weather data from backend proxy (/api/weather)
 * 3. Displays current conditions and 5-day forecast
 * 4. Renders nothing if location denied or API fails (per spec)
 *
 * The backend proxy handles the NWS API call because browsers
 * block the custom User-Agent header required by weather.gov.
 */
import { useState, useEffect } from 'react'
import type { WeatherData } from '@/types'
import { WeatherIcon } from './WeatherIcon'

type WeatherState =
  | { status: 'loading' }
  | { status: 'success'; data: WeatherData }
  | { status: 'error' }
  | { status: 'denied' }

export function WeatherIsland() {
  const [state, setState] = useState<WeatherState>({ status: 'loading' })

  useEffect(() => {
    let cancelled = false

    async function fetchWeather() {
      // Check if geolocation is available
      if (!navigator.geolocation) {
        setState({ status: 'denied' })
        return
      }

      try {
        // Get user's location
        const position = await new Promise<GeolocationPosition>((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, {
            timeout: 10000,
            maximumAge: 300000, // 5 minute cache
          })
        })

        if (cancelled) return

        const { latitude, longitude } = position.coords

        // Fetch weather from backend proxy
        const response = await fetch(
          `/api/weather?lat=${latitude}&lng=${longitude}`
        )

        if (cancelled) return

        if (!response.ok) {
          setState({ status: 'error' })
          return
        }

        const data: WeatherData = await response.json()
        setState({ status: 'success', data })

      } catch (error) {
        if (cancelled) return

        // GeolocationPositionError means user denied or location unavailable
        if (error instanceof GeolocationPositionError) {
          setState({ status: 'denied' })
        } else {
          setState({ status: 'error' })
        }
      }
    }

    fetchWeather()

    return () => {
      cancelled = true
    }
  }, [])

  // Per spec: render nothing if denied or error
  if (state.status === 'denied' || state.status === 'error') {
    return null
  }

  // Loading state with skeleton
  if (state.status === 'loading') {
    return (
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/3 mb-3"></div>
          <div className="flex items-center gap-4 mb-4">
            <div className="h-12 w-12 bg-gray-200 rounded-full"></div>
            <div className="h-10 bg-gray-200 rounded w-24"></div>
          </div>
          <div className="h-4 bg-gray-200 rounded w-2/3 mb-4"></div>
          <div className="flex gap-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex-1 h-20 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  // Success state - render weather data
  const { current, periods } = state.data

  // Get first 5 daytime periods for the forecast strip
  const forecastPeriods = periods
    .filter(p => p.isDaytime)
    .slice(0, 5)

  return (
    <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg shadow-lg p-6 mb-6 text-white">
      {/* Current conditions */}
      <div className="mb-6">
        <h2 className="text-sm font-medium opacity-80 mb-2">Current Weather</h2>
        <div className="flex items-center gap-4">
          <WeatherIcon
            forecast={current.shortForecast}
            className="text-5xl drop-shadow-md"
          />
          <div>
            <div className="text-5xl font-bold">
              {current.temperature}°{current.unit}
            </div>
            <div className="text-lg opacity-90">{current.shortForecast}</div>
          </div>
        </div>
      </div>

      {/* 5-day forecast strip */}
      {forecastPeriods.length > 0 && (
        <div>
          <h3 className="text-sm font-medium opacity-80 mb-3">5-Day Forecast</h3>
          <div className="grid grid-cols-5 gap-2">
            {forecastPeriods.map((period, idx) => (
              <div
                key={idx}
                className="bg-white/10 rounded-lg p-3 text-center backdrop-blur-sm"
              >
                <div className="text-xs font-medium opacity-80 mb-1 truncate">
                  {period.name}
                </div>
                <WeatherIcon
                  forecast={period.shortForecast}
                  className="text-xl"
                />
                <div className="text-lg font-bold mt-1">
                  {period.temperature}°
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
