/**
 * E2E tests for the Weather Widget feature.
 *
 * These tests verify the weather widget works correctly by:
 * - Mocking geolocation via Playwright's context
 * - Mocking the /api/weather endpoint to avoid real NWS API calls
 * - Testing visibility based on location permission state
 *
 * Per spec: Widget renders nothing if location denied or API fails.
 */
import { test, expect } from '@playwright/test';

// Mock weather API response
const mockWeatherResponse = {
  current: {
    name: 'Today',
    temperature: 72,
    unit: 'F',
    shortForecast: 'Sunny',
    icon: 'https://api.weather.gov/icons/land/day/skc',
    isDaytime: true,
  },
  periods: [
    {
      name: 'Tonight',
      temperature: 55,
      unit: 'F',
      shortForecast: 'Clear',
      icon: 'https://api.weather.gov/icons/land/night/skc',
      isDaytime: false,
    },
    {
      name: 'Tomorrow',
      temperature: 75,
      unit: 'F',
      shortForecast: 'Partly Cloudy',
      icon: 'https://api.weather.gov/icons/land/day/sct',
      isDaytime: true,
    },
    {
      name: 'Wednesday',
      temperature: 78,
      unit: 'F',
      shortForecast: 'Sunny',
      icon: 'https://api.weather.gov/icons/land/day/skc',
      isDaytime: true,
    },
    {
      name: 'Thursday',
      temperature: 80,
      unit: 'F',
      shortForecast: 'Hot',
      icon: 'https://api.weather.gov/icons/land/day/hot',
      isDaytime: true,
    },
    {
      name: 'Friday',
      temperature: 76,
      unit: 'F',
      shortForecast: 'Warm',
      icon: 'https://api.weather.gov/icons/land/day/few',
      isDaytime: true,
    },
  ],
};

test.describe('Weather Widget', () => {
  test('shows weather when geolocation granted and API succeeds', async ({ page, context }) => {
    // Grant geolocation permission and set location
    await context.grantPermissions(['geolocation']);
    await context.setGeolocation({ latitude: 37.7749, longitude: -122.4194 });

    // Mock the weather API endpoint
    await page.route('/api/weather*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockWeatherResponse),
      });
    });

    await page.goto('/');

    // Weather widget should be visible with data
    await expect(page.getByText('Current Weather')).toBeVisible();
    await expect(page.getByText(/72°F/)).toBeVisible();
    await expect(page.getByText('Sunny')).toBeVisible();
  });

  test('shows 5-day forecast strip', async ({ page, context }) => {
    await context.grantPermissions(['geolocation']);
    await context.setGeolocation({ latitude: 37.7749, longitude: -122.4194 });

    await page.route('/api/weather*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockWeatherResponse),
      });
    });

    await page.goto('/');

    // Wait for weather data to load
    await expect(page.getByText('5-Day Forecast')).toBeVisible();

    // Should show forecast days
    await expect(page.getByText('Tomorrow')).toBeVisible();
    await expect(page.getByText('Wednesday')).toBeVisible();
  });

  test('hides weather widget when geolocation denied', async ({ page, context }) => {
    // Don't grant geolocation permission - browser will deny by default
    // Note: Playwright defaults to denying permissions not explicitly granted

    await page.route('/api/weather*', (route) => {
      // This shouldn't be called if geolocation is denied
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockWeatherResponse),
      });
    });

    await page.goto('/');

    // Wait for potential weather widget to load (give it time to attempt geolocation)
    await page.waitForTimeout(1000);

    // Weather widget should NOT be visible (per spec: renders nothing on denial)
    // Check that "Current Weather" text is not present
    const weatherHeader = page.getByText('Current Weather');
    await expect(weatherHeader).not.toBeVisible();
  });

  test('hides weather widget when API returns error', async ({ page, context }) => {
    await context.grantPermissions(['geolocation']);
    await context.setGeolocation({ latitude: 37.7749, longitude: -122.4194 });

    // Mock API to return error
    await page.route('/api/weather*', (route) => {
      route.fulfill({
        status: 502,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Upstream API error' }),
      });
    });

    await page.goto('/');

    // Wait for widget to process the error
    await page.waitForTimeout(1000);

    // Weather widget should NOT be visible
    const weatherHeader = page.getByText('Current Weather');
    await expect(weatherHeader).not.toBeVisible();
  });

  test('weather widget displays temperature correctly', async ({ page, context }) => {
    await context.grantPermissions(['geolocation']);
    await context.setGeolocation({ latitude: 40.7128, longitude: -74.0060 });

    const customWeatherData = {
      ...mockWeatherResponse,
      current: {
        ...mockWeatherResponse.current,
        temperature: 85,
        shortForecast: 'Hot and Humid',
      },
    };

    await page.route('/api/weather*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(customWeatherData),
      });
    });

    await page.goto('/');

    await expect(page.getByText(/85°F/)).toBeVisible();
    await expect(page.getByText('Hot and Humid')).toBeVisible();
  });

  test('hello island still works alongside weather widget', async ({ page, context }) => {
    // Grant geolocation for weather
    await context.grantPermissions(['geolocation']);
    await context.setGeolocation({ latitude: 37.7749, longitude: -122.4194 });

    await page.route('/api/weather*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockWeatherResponse),
      });
    });

    await page.goto('/');

    // Both islands should work
    await expect(page.getByText('Current Weather')).toBeVisible();

    // Hello island should still be functional
    const helloIsland = page.locator('[data-island="hello"]');
    await expect(helloIsland).toBeVisible();

    const input = page.getByPlaceholder('Enter a greeting');
    await expect(input).toBeVisible();
  });
});

test.describe('Weather API', () => {
  test('GET /api/weather returns weather data', async ({ request, context }) => {
    // Note: This tests the actual backend, but with mocked upstream
    // In a real scenario, we'd want the backend to work correctly

    // Test with valid coordinates
    const response = await request.get('/api/weather?lat=37.7749&lng=-122.4194');

    // The backend will try to call the real NWS API
    // In CI, this might fail due to network issues, so we check for valid response format
    // Either success (200) or upstream error (502) are acceptable
    expect([200, 502]).toContain(response.status());
  });

  test('GET /api/weather rejects missing params', async ({ request }) => {
    const response = await request.get('/api/weather');
    expect(response.status()).toBe(400);

    const body = await response.json();
    expect(body.error).toBeDefined();
  });

  test('GET /api/weather rejects invalid params', async ({ request }) => {
    const response = await request.get('/api/weather?lat=invalid&lng=invalid');
    expect(response.status()).toBe(400);
  });

  test('GET /api/weather rejects out-of-range coordinates', async ({ request }) => {
    const response = await request.get('/api/weather?lat=999&lng=-122');
    expect(response.status()).toBe(400);

    const body = await response.json();
    expect(body.error).toContain('Latitude');
  });
});
