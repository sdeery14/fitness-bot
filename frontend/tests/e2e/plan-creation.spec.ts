/**
 * End-to-End test for fitness plan creation workflow
 * 
 * Tests the complete user journey from signup to plan generation:
 * 1. User signs up with a new account
 * 2. User logs in
 * 3. User starts a conversation with the AI agent
 * 4. User provides fitness goals and requirements
 * 5. AI generates a personalized fitness plan
 * 6. User views the generated plan
 * 
 * Success Criteria:
 * - User Story 1: Complete plan creation flow works end-to-end
 * - FR-052 to FR-071: All functional requirements are exercised
 * - SC-001 to SC-030: Success criteria are validated
 */

import { test, expect, Page } from '@playwright/test';

// Test configuration
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Test data
const TEST_USER = {
  email: `test.user.${Date.now()}@example.com`,
  password: 'TestPassword123!',
  full_name: 'Test User',
  date_of_birth: '1990-01-15',
  current_fitness_level: 'intermediate'
};

const PLAN_CREATION_MESSAGES = [
  'I want to lose 15 pounds in 3 months',
  'I have access to a gym with all equipment',
  'I prefer morning workouts',
  'I am vegetarian'
];

test.describe('Fitness Plan Creation E2E Flow', () => {
  let page: Page;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
  });

  test.afterAll(async () => {
    await page.close();
  });

  test('Complete signup → login → conversation → plan generation flow', async () => {
    // Step 1: Navigate to signup page
    await page.goto(`${BASE_URL}/signup`);
    await expect(page).toHaveTitle(/Sign Up|AI Fitness Planner/i);

    // Step 2: Fill out signup form
    await page.fill('input[name="email"]', TEST_USER.email);
    await page.fill('input[name="password"]', TEST_USER.password);
    await page.fill('input[name="confirmPassword"]', TEST_USER.password);
    await page.fill('input[name="full_name"]', TEST_USER.full_name);
    await page.fill('input[name="date_of_birth"]', TEST_USER.date_of_birth);
    await page.selectOption('select[name="current_fitness_level"]', TEST_USER.current_fitness_level);

    // Step 3: Submit signup form
    await page.click('button[type="submit"]');

    // Wait for redirect to login page or dashboard
    await page.waitForURL(/login|dashboard/, { timeout: 5000 });

    // Step 4: Login (if redirected to login page)
    const currentUrl = page.url();
    if (currentUrl.includes('/login')) {
      await page.fill('input[name="email"]', TEST_USER.email);
      await page.fill('input[name="password"]', TEST_USER.password);
      await page.click('button[type="submit"]');
      await page.waitForURL(/dashboard/, { timeout: 5000 });
    }

    // Verify we're logged in (check for user menu or logout button)
    await expect(page.locator('text=/logout|sign out/i')).toBeVisible({ timeout: 5000 });

    // Step 5: Navigate to chat/conversation page
    await page.goto(`${BASE_URL}/dashboard/chat`);
    await expect(page).toHaveURL(/chat/);

    // Step 6: Start conversation with initial message
    const messageInput = page.locator('textarea[placeholder*="message"]').or(
      page.locator('input[placeholder*="message"]')
    );
    await messageInput.fill(PLAN_CREATION_MESSAGES[0]);
    await messageInput.press('Enter');

    // Wait for AI response
    await expect(page.locator('text=/AI|Assistant/i')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.message').or(page.locator('[data-sender="assistant"]'))).toBeVisible();

    // Step 7: Continue conversation with follow-up messages
    for (let i = 1; i < PLAN_CREATION_MESSAGES.length; i++) {
      await page.waitForTimeout(2000); // Wait for previous response to complete
      await messageInput.fill(PLAN_CREATION_MESSAGES[i]);
      await messageInput.press('Enter');
      
      // Wait for AI response
      await page.waitForTimeout(3000);
    }

    // Step 8: Wait for plan generation to complete
    // Look for indicators like "plan created", "view plan", or navigation to plan page
    await expect(
      page.locator('text=/plan created|plan generated|view.*plan/i')
    ).toBeVisible({ timeout: 30000 });

    // Step 9: Navigate to or verify plan view
    const planLink = page.locator('a[href*="plan"]').or(page.locator('button:has-text("View Plan")'));
    if (await planLink.isVisible()) {
      await planLink.click();
      await page.waitForTimeout(2000);
    }

    // Step 10: Verify plan details are displayed
    await expect(page.locator('text=/fitness plan|workout|meal/i')).toBeVisible({ timeout: 5000 });

    // Verify key plan elements
    const pageContent = await page.content();
    
    // Should show goal information
    expect(pageContent.toLowerCase()).toMatch(/goal|objective|target/);
    
    // Should show duration
    expect(pageContent).toMatch(/week|month|day/);

    // Should show workout information
    expect(pageContent.toLowerCase()).toMatch(/workout|exercise/);

    // Should show meal/nutrition information
    expect(pageContent.toLowerCase()).toMatch(/meal|nutrition|calorie/);

    console.log('✓ E2E Test Passed: Complete plan creation flow successful');
  });

  test('Verify plan persists after logout and login', async () => {
    // Step 1: Logout
    await page.goto(`${BASE_URL}/dashboard`);
    const logoutButton = page.locator('button:has-text("Logout")').or(
      page.locator('a:has-text("Logout")')
    );
    await logoutButton.click();
    await page.waitForURL(/login|signup/, { timeout: 5000 });

    // Step 2: Login again
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', TEST_USER.email);
    await page.fill('input[name="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/dashboard/, { timeout: 5000 });

    // Step 3: Navigate to plans page
    await page.goto(`${BASE_URL}/dashboard/plans`).catch(() => {
      // If /plans doesn't exist, try /plan or /dashboard
      return page.goto(`${BASE_URL}/dashboard`);
    });

    // Step 4: Verify plan is still there
    await expect(page.locator('text=/fitness plan|active plan/i')).toBeVisible({ timeout: 5000 });
    
    console.log('✓ E2E Test Passed: Plan persists after logout/login');
  });

  test('Verify AI streaming responses work', async () => {
    // Navigate to chat
    await page.goto(`${BASE_URL}/dashboard/chat`);

    // Send a message
    const messageInput = page.locator('textarea[placeholder*="message"]').or(
      page.locator('input[placeholder*="message"]')
    );
    await messageInput.fill('Tell me about my workout plan');
    await messageInput.press('Enter');

    // Verify streaming indicator appears (loading animation, typing indicator, etc.)
    await expect(
      page.locator('[data-loading="true"]').or(
        page.locator('.typing-indicator')
      ).or(
        page.locator('text=/•••|typing|thinking/i')
      )
    ).toBeVisible({ timeout: 2000 });

    // Wait for response to complete
    await page.waitForTimeout(5000);

    // Verify response appeared
    await expect(page.locator('.message').last()).toBeVisible();
    
    console.log('✓ E2E Test Passed: AI streaming responses work');
  });

  test('Verify form validation on signup', async () => {
    await page.goto(`${BASE_URL}/signup`);

    // Try to submit empty form
    await page.click('button[type="submit"]');

    // Should show validation errors
    await expect(page.locator('text=/required|invalid/i')).toBeVisible({ timeout: 2000 });

    // Try with weak password
    await page.fill('input[name="email"]', 'newuser@example.com');
    await page.fill('input[name="password"]', '123'); // Weak password
    await page.click('button[type="submit"]');

    // Should show password validation error
    await expect(page.locator('text=/password|weak|strong/i')).toBeVisible({ timeout: 2000 });

    console.log('✓ E2E Test Passed: Form validation works');
  });
});

test.describe('Error Handling E2E', () => {
  test('Handle invalid login gracefully', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Try invalid credentials
    await page.fill('input[name="email"]', 'nonexistent@example.com');
    await page.fill('input[name="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');

    // Should show error message
    await expect(page.locator('text=/invalid|incorrect|error/i')).toBeVisible({ timeout: 3000 });

    // Should not redirect
    expect(page.url()).toContain('/login');

    console.log('✓ E2E Test Passed: Invalid login handled gracefully');
  });

  test('Handle API errors gracefully', async ({ page }) => {
    // Login first
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', TEST_USER.email);
    await page.fill('input[name="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/dashboard/, { timeout: 5000 });

    // Intercept API calls and simulate error
    await page.route(`${API_URL}/ai/conversations/*`, (route) => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'error',
          error: {
            code: 'INTERNAL_ERROR',
            message: 'Simulated server error'
          }
        })
      });
    });

    // Try to send a message
    await page.goto(`${BASE_URL}/dashboard/chat`);
    const messageInput = page.locator('textarea[placeholder*="message"]').or(
      page.locator('input[placeholder*="message"]')
    );
    await messageInput.fill('Test message');
    await messageInput.press('Enter');

    // Should show error notification
    await expect(page.locator('text=/error|failed|try again/i')).toBeVisible({ timeout: 5000 });

    console.log('✓ E2E Test Passed: API errors handled gracefully');
  });
});
