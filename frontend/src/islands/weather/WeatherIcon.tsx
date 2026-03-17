/**
 * WeatherIcon component - Maps weather forecasts to visual emoji icons.
 * 
 * Converts NWS shortForecast strings to appropriate weather emojis.
 * Uses pattern matching to handle various forecast descriptions.
 */

interface WeatherIconProps {
  forecast: string
  className?: string
}

/**
 * Map of forecast keywords to emoji icons.
 * Order matters - first match wins, so more specific patterns come first.
 */
const FORECAST_ICONS: Array<{ pattern: RegExp; icon: string }> = [
  // Severe weather first
  { pattern: /thunderstorm|thunder/i, icon: '⛈️' },
  { pattern: /tornado|funnel/i, icon: '🌪️' },
  { pattern: /hurricane|tropical/i, icon: '🌀' },
  
  // Precipitation
  { pattern: /snow|blizzard|flurr/i, icon: '❄️' },
  { pattern: /sleet|freezing rain|ice/i, icon: '🌨️' },
  { pattern: /rain|shower|drizzle/i, icon: '🌧️' },
  { pattern: /hail/i, icon: '🌨️' },
  
  // Fog and haze
  { pattern: /fog|mist|haze|smoke/i, icon: '🌫️' },
  
  // Cloudy conditions
  { pattern: /overcast|cloudy/i, icon: '☁️' },
  { pattern: /mostly cloudy/i, icon: '🌥️' },
  { pattern: /partly cloudy|partly sunny/i, icon: '⛅' },
  
  // Clear/sunny conditions
  { pattern: /sunny|clear/i, icon: '☀️' },
  { pattern: /mostly sunny|mostly clear/i, icon: '🌤️' },
  
  // Wind
  { pattern: /windy|breezy/i, icon: '💨' },
  
  // Hot/cold
  { pattern: /hot/i, icon: '🔥' },
  { pattern: /cold|frigid/i, icon: '🥶' },
]

// Default icon when no pattern matches
const DEFAULT_ICON = '🌡️'

/**
 * Get emoji icon for a weather forecast.
 */
function getWeatherIcon(forecast: string): string {
  for (const { pattern, icon } of FORECAST_ICONS) {
    if (pattern.test(forecast)) {
      return icon
    }
  }
  return DEFAULT_ICON
}

/**
 * WeatherIcon component renders an emoji icon based on forecast text.
 */
export function WeatherIcon({ forecast, className = '' }: WeatherIconProps) {
  const icon = getWeatherIcon(forecast)
  
  return (
    <span 
      className={`text-2xl ${className}`} 
      role="img" 
      aria-label={forecast}
    >
      {icon}
    </span>
  )
}
