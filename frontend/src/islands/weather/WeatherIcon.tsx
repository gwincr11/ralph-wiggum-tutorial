/**
 * WeatherIcon - Maps weather forecast strings to visual icons
 *
 * Uses emoji icons for simplicity and universal support.
 * Maps common NWS shortForecast strings to appropriate weather symbols.
 */

interface WeatherIconProps {
  forecast: string
  className?: string
}

/**
 * Map of forecast keywords to emoji icons.
 * Order matters - first match wins.
 */
const forecastIcons: [RegExp, string][] = [
  [/thunder|storm/i, '⛈️'],
  [/rain|shower|drizzle/i, '🌧️'],
  [/snow|flurr/i, '❄️'],
  [/sleet|ice|freez/i, '🌨️'],
  [/fog|mist|haz/i, '🌫️'],
  [/cloud|overcast/i, '☁️'],
  [/partly.*cloud|partly.*sunny/i, '⛅'],
  [/mostly.*cloud/i, '🌥️'],
  [/mostly.*sunny|mostly.*clear/i, '🌤️'],
  [/sunny|clear/i, '☀️'],
  [/wind/i, '💨'],
  [/hot/i, '🔥'],
  [/cold/i, '🥶'],
]

/**
 * Get the appropriate weather icon for a forecast string.
 */
function getWeatherIcon(forecast: string): string {
  for (const [pattern, icon] of forecastIcons) {
    if (pattern.test(forecast)) {
      return icon
    }
  }
  return '🌡️' // Default fallback
}

export function WeatherIcon({ forecast, className = '' }: WeatherIconProps) {
  const icon = getWeatherIcon(forecast)

  return (
    <span className={`text-2xl ${className}`} role="img" aria-label={forecast}>
      {icon}
    </span>
  )
}
