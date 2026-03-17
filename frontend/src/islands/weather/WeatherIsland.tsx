/**
 * WeatherIsland - Displays local weather using browser geolocation.
 * 
 * This island requests the user's location, fetches weather data from
 * the backend proxy, and displays current conditions plus a 5-day forecast.
 * If location access is denied or the API fails, the widget is hidden.
 */
import { useState, useEffect } from 'react'
import { WeatherData } from '../../types'
import { WeatherIcon } from './WeatherIcon'

type LoadingState = 'idle' | 'loading' | 'success' | 'error' | 'denied'

export function WeatherIsland() {
  const [weather, setWeather] = useState<WeatherData | null>(null)
  const [state, setState] = useState<LoadingState>('idle')

  useEffect(() => {
    // Start loading weather data
    fetchWeatherWithLocation()
  }, [])

  async function fetchWeatherWithLocation() {
    setState('loading')

    // Check if geolocation is available
    if (!navigator.geolocation) {
      setState('denied')
      return
    }

    // Request user's location
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords
        try {
          const response = await fetch(`/api/weather?lat=${latitude}&lng=${longitude}`)
          if (!response.ok) {
            throw new Error('Weather API error')
          }
          const data: WeatherData = await response.json()
          setWeather(data)
          setState('success')
        } catch (err) {
          console.error('Failed to fetch weather:', err)
          setState('error')
        }
      },
      (error) => {
        console.error('Geolocation error:', error)
        setState('denied')
      },
      {
        enableHighAccuracy: false,
        timeout: 10000,
        maximumAge: 300000 // 5 minutes cache
      }
    )
  }

  // Hide widget entirely for denied/error states (per spec)
  if (state === 'denied' || state === 'error') {
    return null
  }

  // Loading state with skeleton
  if (state === 'loading' || state === 'idle') {
    return (
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="animate-pulse">
          <div className="flex items-center gap-4 mb-4">
            <div className="h-12 w-12 bg-gray-200 rounded-full"></div>
            <div className="flex-1">
              <div className="h-4 bg-gray-200 rounded w-1/3 mb-2"></div>
              <div className="h-8 bg-gray-200 rounded w-1/4"></div>
            </div>
          </div>
          <div className="flex gap-2 overflow-x-auto">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex-shrink-0 w-20 h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  // Success state with weather data
  if (!weather) return null

  const { current, periods } = weather

  return (
    <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg shadow-lg p-6 mb-6 text-white">
      {/* Current conditions */}
      <div className="flex items-center gap-4 mb-6">
        <WeatherIcon forecast={current.shortForecast} className="text-5xl" />
        <div>
          <p className="text-sm opacity-90">{current.name}</p>
          <p className="text-4xl font-bold">
            {current.temperature}°{current.unit}
          </p>
          <p className="text-sm opacity-90">{current.shortForecast}</p>
        </div>
      </div>

      {/* Forecast strip */}
      <div className="border-t border-white/20 pt-4">
        <h3 className="text-sm font-medium mb-3 opacity-90">Forecast</h3>
        <div className="flex gap-3 overflow-x-auto pb-2">
          {periods.map((period, index) => (
            <div 
              key={index} 
              className="flex-shrink-0 bg-white/10 rounded-lg p-3 text-center min-w-[80px] hover:bg-white/20 transition-colors"
            >
              <p className="text-xs opacity-90 mb-1 truncate">{period.name}</p>
              <WeatherIcon forecast={period.shortForecast} className="text-xl" />
              <p className="text-lg font-semibold mt-1">
                {period.temperature}°
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
