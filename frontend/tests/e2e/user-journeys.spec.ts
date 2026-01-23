/**
 * Sample E2E test using Playwright
 * Tests critical user journeys
 */

import { test, expect } from '@playwright/test'

// Test data
const TEST_USER = {
  email: 'test@teduco.ai',
  password: 'TestPassword123!',
  firstName: 'Test',
  lastName: 'User',
}

test.describe('Authentication Flow', () => {
  test('should allow user to sign up', async ({ page }) => {
    await page.goto('/signup')

    // Fill signup form
    await page.getByLabel(/email/i).fill(TEST_USER.email)
    await page.getByLabel(/password/i).fill(TEST_USER.password)
    await page.getByLabel(/confirm password/i).fill(TEST_USER.password)

    // Submit form
    await page.getByRole('button', { name: /sign up/i }).click()

    // Should redirect to onboarding or dashboard
    await expect(page).toHaveURL(/\/(onboarding|dashboard)/)
  })

  test('should allow user to log in', async ({ page }) => {
    await page.goto('/login')

    await page.getByLabel(/email/i).fill(TEST_USER.email)
    await page.getByLabel(/password/i).fill(TEST_USER.password)
    await page.getByRole('button', { name: /log in/i }).click()

    await expect(page).toHaveURL(/\/dashboard/)
    await expect(page.getByText(/welcome/i)).toBeVisible()
  })

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/login')

    await page.getByLabel(/email/i).fill('wrong@email.com')
    await page.getByLabel(/password/i).fill('wrongpassword')
    await page.getByRole('button', { name: /log in/i }).click()

    await expect(page.getByText(/invalid credentials/i)).toBeVisible()
  })
})

test.describe('Chat Interface', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login')
    await page.getByLabel(/email/i).fill(TEST_USER.email)
    await page.getByLabel(/password/i).fill(TEST_USER.password)
    await page.getByRole('button', { name: /log in/i }).click()
    await page.waitForURL(/\/dashboard/)
  })

  test('should send a message and receive response', async ({ page }) => {
    await page.goto('/chat')

    // Type a question
    const chatInput = page.getByPlaceholder(/ask a question/i)
    await chatInput.fill('What are the best universities for Computer Science?')

    // Send message
    await page.getByRole('button', { name: /send/i }).click()

    // User message should appear
    await expect(
      page.getByText('What are the best universities for Computer Science?')
    ).toBeVisible()

    // Wait for assistant response (with timeout)
    await expect(page.getByText(/MIT|Stanford|Carnegie Mellon/i)).toBeVisible({
      timeout: 10000,
    })

    // Check for sources
    await expect(page.getByText(/sources/i)).toBeVisible()
  })

  test('should create new chat', async ({ page }) => {
    await page.goto('/chat')

    await page.getByRole('button', { name: /new chat/i }).click()

    // Should show empty chat state
    await expect(page.getByText(/start a conversation/i)).toBeVisible()
  })

  test('should switch between chats', async ({ page }) => {
    await page.goto('/chat')

    // Create first chat
    await page.getByPlaceholder(/ask a question/i).fill('Question 1')
    await page.getByRole('button', { name: /send/i }).click()

    // Create new chat
    await page.getByRole('button', { name: /new chat/i }).click()
    await page.getByPlaceholder(/ask a question/i).fill('Question 2')
    await page.getByRole('button', { name: /send/i }).click()

    // Switch back to first chat
    const firstChat = page.getByText(/Question 1/i).first()
    await firstChat.click()

    await expect(page.getByText('Question 1')).toBeVisible()
  })
})

test.describe('Document Upload', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/email/i).fill(TEST_USER.email)
    await page.getByLabel(/password/i).fill(TEST_USER.password)
    await page.getByRole('button', { name: /log in/i }).click()
    await page.waitForURL(/\/dashboard/)
  })

  test('should upload a document', async ({ page }) => {
    await page.goto('/documents')

    // Click upload button
    const uploadButton = page.getByRole('button', { name: /upload/i })
    await uploadButton.click()

    // Upload file
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles('./tests/fixtures/sample_transcript.pdf')

    // Select document type
    await page.getByLabel(/document type/i).selectOption('transcript')

    // Submit
    await page.getByRole('button', { name: /upload/i }).click()

    // Wait for success message
    await expect(page.getByText(/uploaded successfully/i)).toBeVisible()

    // Document should appear in list
    await expect(page.getByText(/sample_transcript.pdf/i)).toBeVisible()
  })

  test('should delete a document', async ({ page }) => {
    await page.goto('/documents')

    // Find a document and click delete
    const deleteButton = page
      .getByRole('button', { name: /delete/i })
      .first()
    await deleteButton.click()

    // Confirm deletion
    await page.getByRole('button', { name: /confirm/i }).click()

    // Success message
    await expect(page.getByText(/deleted successfully/i)).toBeVisible()
  })
})

test.describe('University Search', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/email/i).fill(TEST_USER.email)
    await page.getByLabel(/password/i).fill(TEST_USER.password)
    await page.getByRole('button', { name: /log in/i }).click()
    await page.waitForURL(/\/dashboard/)
  })

  test('should search for universities', async ({ page }) => {
    await page.goto('/universities')

    // Search
    const searchInput = page.getByPlaceholder(/search universities/i)
    await searchInput.fill('computer science')

    // Results should appear
    await expect(page.getByText(/MIT|Stanford/i)).toBeVisible()
  })

  test('should filter by country', async ({ page }) => {
    await page.goto('/universities')

    // Select country filter
    await page.getByLabel(/country/i).selectOption('USA')

    // Apply filter
    await page.getByRole('button', { name: /apply filters/i }).click()

    // Results should only show USA universities
    const results = page.getByTestId('university-card')
    await expect(results.first()).toContainText(/USA/)
  })

  test('should view university details', async ({ page }) => {
    await page.goto('/universities')

    // Click on a university
    await page.getByText(/MIT/i).first().click()

    // Should navigate to details page
    await expect(page).toHaveURL(/\/universities\/uni-/)
    await expect(page.getByRole('heading', { name: /MIT/i })).toBeVisible()
    await expect(page.getByText(/tuition/i)).toBeVisible()
  })
})

test.describe('Multi-language Support', () => {
  test('should switch language to Turkish', async ({ page }) => {
    await page.goto('/')

    // Find language switcher
    const languageSwitcher = page.getByRole('button', { name: /language/i })
    await languageSwitcher.click()

    // Select Turkish
    await page.getByText(/türkçe/i).click()

    // Check for Turkish text
    await expect(page.getByText(/giriş yap|oturum aç/i)).toBeVisible()
  })
})

test.describe('Accessibility', () => {
  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('/login')

    // Tab through form
    await page.keyboard.press('Tab') // Email field
    await page.keyboard.type(TEST_USER.email)

    await page.keyboard.press('Tab') // Password field
    await page.keyboard.type(TEST_USER.password)

    await page.keyboard.press('Tab') // Submit button
    await page.keyboard.press('Enter')

    // Should submit form
    await expect(page).toHaveURL(/\/dashboard/)
  })

  test('should have proper ARIA labels', async ({ page }) => {
    await page.goto('/chat')

    // Check for ARIA labels
    const chatInput = page.getByRole('textbox', { name: /message/i })
    await expect(chatInput).toHaveAttribute('aria-label')

    const sendButton = page.getByRole('button', { name: /send/i })
    await expect(sendButton).toHaveAttribute('aria-label')
  })
})
