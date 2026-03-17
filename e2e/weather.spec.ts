import { test, expect } from '@playwright/test';

/**
 * Weather Widget E2E tests.
 *
 * Tests the weather widget functionality including:
 * - Display when geolocation is granted
 * - Hidden when geolocation is denied
 * - Handles API errors gracefully
 * - Displays temperature and forecast data
 *
 * Note: Uses mocked geolocation and API responses to avoid
 * real NWS API calls and ensure deterministic tests.
 */

// Mock weather API response
const mockWeatherResponse = {
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
    {
      name: 'Tuesday Night',
      temperature: 58,
      unit: 'F',
      shortForecast: 'Mostly Clear',
      icon: 'https://api.weather.gov/icons/night/few',
      isDaytime: false,
    },
    {
      name: 'Wednesday',
      temperature: 78,
      unit: 'F',
      shortForecast: 'Mostly Sunny',
      icon: 'https://api.weather.gov/icons/day/sct',
      isDaytime: true,
    },
    {
      name: 'Wednesday Night',
      temperature: 60,
      unit: 'F',
      shortForecast: 'Partly Cloudy',
      icon: 'https://api.weather.gov/icons/night/sct',
      isDaytime: false,
    },
  ],
};

test.describe('Weather Widget', () => {
  test('displays weather when geolocation granted and API succeeds', async ({ context, page }) => {
    // Grant geolocation permission and set mock location
    await context.grantPermissions(['geolocation']);
    await context.setGeolocation({ latitude: 37.7749, longitude: -122.4194 });

    // Mock the weather API to avoid real NWS calls
    await page.route('/api/weather*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockWeatherResponse),
      });
    });

    await page.goto('/');

    // Wait for the weather widget to load
    const weatherWidget = page.locator('[data-island="weather"]');
    await expect(weatherWidget).toBeVisible();

    // Check current conditions are displayed
    await expect(page.getByText('72°F')).toBeVisible();
    await expect(page.getByText('Sunny')).toBeVisible();
    await expect(page.getByText('Today')).toBeVisible();
  });

  test('displays forecast periods', async ({ context, page }) => {
    await context.grantPermissions(['geolocation']);
    await context.setGeolocation({ latitude: 37.7749, longitude: -122.4194 });

    await page.route('/api/weather*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockWeatherResponse),
      });
    });

    await page.goto('/');

    // Check forecast periods are displayed
    await expect(page.getByText('Tonight')).toBeVisible();
    await expect(page.getByText('Tuesday', { exact: true })).toBeVisible();
    await expect(page.getByText('55°')).toBeVisible();
    await expect(page.getByText('75°')).toBeVisible();
  });

  test('widget hidden when geolocation denied', async ({ context, page }) => {
    // Clear geolocation permission (simulates denial)
    await context.clearPermissions();

    await page.goto('/');

    // Small wait to allow component to process denied state
    await page.waitForTimeout(500);

    // The weather island mount point should still exist but be empty
    const weatherWidget = page.locator('[data-island="weather"]');

    // Check that the widget is either hidden or empty
    // The component renders null when denied, so the container may have no visible content
    const isEmptyOrHidden = await weatherWidget.evaluate((el) => {
      return el.innerHTML.trim() === '' || el.children.length === 0;
    });
    expect(isEmptyOrHidden).toBe(true);
  });

  test('widget hidden when API returns error', async ({ context, page }) => {
    await context.grantPermissions(['geolocation']);
    await context.setGeolocation({ latitude: 37.7749, longitude: -122.4194 });

    // Mock API to return error
    await page.route('/api/weather*', async (route) => {
      await route.fulfill({
        status: 502,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Weather service unavailable' }),
      });
    });

    await page.goto('/');

    // Wait for error state to be processed
    await page.waitForTimeout(500);

    // The weather island should be empty or not show weather data
    const weatherWidget = page.locator('[data-island="weather"]');
    const isEmptyOrHidden = await weatherWidget.evaluate((el) => {
      return el.innerHTML.trim() === '' || el.children.length === 0;
    });
    expect(isEmptyOrHidden).toBe(true);
  });

  test('displays weather icon based on forecast', async ({ context, page }) => {
    await context.grantPermissions(['geolocation']);
    await context.setGeolocation({ latitude: 37.7749, longitude: -122.4194 });

    await page.route('/api/weather*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockWeatherResponse),
      });
    });

    await page.goto('/');

    // Check that weather icons are rendered (they should have aria-labels)
    const sunnyIcon = page.getByRole('img', { name: 'Sunny', exact: true });
    await expect(sunnyIcon).toBeVisible();
  });
});

test.describe('Weather API', () => {
  test('GET /api/weather returns 400 for missing params', async ({ request }) => {
    const response = await request.get('/api/weather');
    expect(response.status()).toBe(400);

    const body = await response.json();
    expect(body.error).toBeDefined();
  });

  test('GET /api/weather returns 400 for invalid coords', async ({ request }) => {
    const response = await request.get('/api/weather?lat=abc&lng=def');
    expect(response.status()).toBe(400);
  });

  test('GET /api/weather returns 400 for out-of-range coords', async ({ request }) => {
    const response = await request.get('/api/weather?lat=999&lng=-122.4');
    expect(response.status()).toBe(400);

    const body = await response.json();
    expect(body.error).toContain('Latitude');
  });
});
