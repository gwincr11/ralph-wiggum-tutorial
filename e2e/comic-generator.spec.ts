/**
 * Comic Generator E2E Tests
 *
 * Tests the comic generator feature with mocked API responses.
 * Uses Playwright's route() to intercept API calls and return
 * canned responses, avoiding real Hugging Face API calls.
 */
import { test, expect } from '@playwright/test'

// Sample base64 placeholder image (1x1 red pixel PNG)
const PLACEHOLDER_IMAGE =
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=='

// Mock successful comic response
const mockComicResponse = {
  prompt: 'A cat using a computer',
  panels: [
    {
      panel_number: 1,
      description: 'A cat sits at a desk with a computer',
      dialogue: 'Time to check my emails!',
      image_base64: PLACEHOLDER_IMAGE,
    },
    {
      panel_number: 2,
      description: 'Cat stares intensely at the screen',
      dialogue: 'Wait... what is this?',
      image_base64: PLACEHOLDER_IMAGE,
    },
    {
      panel_number: 3,
      description: 'Cat knocks the computer off the desk',
      dialogue: 'Nevermind!',
      image_base64: PLACEHOLDER_IMAGE,
    },
  ],
  created_at: '2024-01-01T00:00:00Z',
}

test.describe('Comic Generator Page', () => {
  test('should navigate to /comic and show the form', async ({ page }) => {
    await page.goto('/comic')

    // Verify page title
    await expect(page).toHaveTitle(/Comic Generator/)

    // Verify form elements are present
    await expect(page.getByLabel(/funny situation/i)).toBeVisible()
    await expect(page.getByRole('button', { name: /generate comic/i })).toBeVisible()
  })

  test('should have navigation links', async ({ page }) => {
    await page.goto('/comic')

    // Verify navigation links
    await expect(page.getByRole('link', { name: 'Hello' })).toBeVisible()
    await expect(page.getByRole('link', { name: 'Comic Generator' })).toBeVisible()
  })

  test('should navigate from home to comic page', async ({ page }) => {
    await page.goto('/')
    await page.getByRole('link', { name: 'Comic Generator' }).click()
    await expect(page).toHaveURL('/comic')
    await expect(page.getByLabel(/funny situation/i)).toBeVisible()
  })
})

test.describe('Comic Generation Flow', () => {
  test('should show loading state when generating', async ({ page }) => {
    // Mock API with delayed response
    await page.route('/api/comic/generate', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 100))
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockComicResponse),
      })
    })

    await page.goto('/comic')

    // Enter prompt
    await page.getByLabel(/funny situation/i).fill('A cat using a computer')

    // Click generate
    await page.getByRole('button', { name: /generate comic/i }).click()

    // Verify loading state
    await expect(page.getByText(/generating/i)).toBeVisible()

    // Wait for completion
    await expect(page.getByTestId('panel-1')).toBeVisible({ timeout: 10000 })
  })

  test('should display 3 panels with images and captions on success', async ({ page }) => {
    // Mock successful API response
    await page.route('/api/comic/generate', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockComicResponse),
      })
    })

    await page.goto('/comic')

    // Enter prompt and generate
    await page.getByLabel(/funny situation/i).fill('A cat using a computer')
    await page.getByRole('button', { name: /generate comic/i }).click()

    // Wait for panels to appear
    await expect(page.getByTestId('panel-1')).toBeVisible({ timeout: 10000 })
    await expect(page.getByTestId('panel-2')).toBeVisible()
    await expect(page.getByTestId('panel-3')).toBeVisible()

    // Verify dialogue text appears
    await expect(page.getByText('Time to check my emails!')).toBeVisible()
    await expect(page.getByText('Wait... what is this?')).toBeVisible()
    await expect(page.getByText('Nevermind!')).toBeVisible()

    // Verify images are rendered (as img elements with src)
    const images = page.locator('[data-testid^="panel-"] img')
    await expect(images).toHaveCount(3)
  })

  test('should show error message on API failure (503)', async ({ page }) => {
    // Mock API error
    await page.route('/api/comic/generate', async (route) => {
      await route.fulfill({
        status: 503,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Service Error',
          message: 'Comic generation service is temporarily unavailable.',
        }),
      })
    })

    await page.goto('/comic')

    // Enter prompt and generate
    await page.getByLabel(/funny situation/i).fill('Test prompt')
    await page.getByRole('button', { name: /generate comic/i }).click()

    // Verify error message appears
    await expect(page.getByText(/error/i)).toBeVisible({ timeout: 10000 })
    await expect(page.getByText(/temporarily unavailable/i)).toBeVisible()
  })

  test('should show rate limit error on 429', async ({ page }) => {
    // Mock rate limit error
    await page.route('/api/comic/generate', async (route) => {
      await route.fulfill({
        status: 429,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Rate Limit Exceeded',
          message: 'Too many requests. Please try again later.',
        }),
      })
    })

    await page.goto('/comic')

    // Enter prompt and generate
    await page.getByLabel(/funny situation/i).fill('Test prompt')
    await page.getByRole('button', { name: /generate comic/i }).click()

    // Verify rate limit error message
    await expect(page.getByText(/rate limit/i)).toBeVisible({ timeout: 10000 })
  })

  test('should disable button during generation', async ({ page }) => {
    // Mock API with longer delay to ensure we can observe the disabled state
    await page.route('/api/comic/generate', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 2000))
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockComicResponse),
      })
    })

    await page.goto('/comic')

    // Enter prompt
    await page.getByLabel(/funny situation/i).fill('Test prompt')

    // Get button and click
    const button = page.getByRole('button', { name: /generate comic/i })
    await button.click()

    // Verify loading state - button shows "Generating..." text
    await expect(page.getByText('Generating...')).toBeVisible({ timeout: 1000 })

    // Wait for completion
    await expect(page.getByTestId('panel-1')).toBeVisible({ timeout: 10000 })

    // Button should be re-enabled with original text
    await expect(page.getByRole('button', { name: /generate comic/i })).toBeEnabled()
  })

  test('should show character count for prompt', async ({ page }) => {
    await page.goto('/comic')

    // Character count should be visible
    await expect(page.getByText('0/500')).toBeVisible()

    // Type some text
    await page.getByLabel(/funny situation/i).fill('Hello')

    // Character count should update
    await expect(page.getByText('5/500')).toBeVisible()
  })

  test('should disable generate button when prompt is empty', async ({ page }) => {
    await page.goto('/comic')

    // Button should be disabled with empty prompt
    const button = page.getByRole('button', { name: /generate comic/i })
    await expect(button).toBeDisabled()

    // Enter text
    await page.getByLabel(/funny situation/i).fill('Test')
    await expect(button).toBeEnabled()

    // Clear text
    await page.getByLabel(/funny situation/i).clear()
    await expect(button).toBeDisabled()
  })
})

test.describe('Comic Page Accessibility', () => {
  test('should have accessible form labels', async ({ page }) => {
    await page.goto('/comic')

    // Textarea should have a label
    const textarea = page.getByLabel(/funny situation/i)
    await expect(textarea).toBeVisible()
    await expect(textarea).toHaveAttribute('id')
  })

  test('should have proper heading structure', async ({ page }) => {
    await page.goto('/comic')

    // Should have h1 heading
    await expect(page.getByRole('heading', { level: 1, name: /comic generator/i })).toBeVisible()
  })
})
