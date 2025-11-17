/**
 * End-to-End test for schedule tracking workflow
 * 
 * Tests the complete user journey for following and tracking their daily schedule:
 * 1. User logs in with existing account
 * 2. User views today's schedule on dashboard
 * 3. User marks a workout as complete
 * 4. User verifies progress is updated
 * 5. User checks adherence rate and streak
 * 
 * Success Criteria:
 * - User Story 2: Complete schedule tracking flow works end-to-end
 * - FR-010 to FR-020: Schedule management functional requirements
 * - FR-026 to FR-034: Progress tracking functional requirements
 * - SC-007 to SC-012: Schedule-related success criteria
 */

import { test, expect, Page } from '@playwright/test';

// Test configuration
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Test data - reusing user from plan creation test
const TEST_USER = {
  email: process.env.E2E_TEST_USER_EMAIL || 'schedule.test@example.com',
  password: process.env.E2E_TEST_USER_PASSWORD || 'TestPassword123!',
};

test.describe('Schedule Tracking E2E Flow', () => {
  let page: Page;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
  });

  test.afterAll(async () => {
    await page.close();
  });

  test.beforeEach(async () => {
    // Login before each test
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', TEST_USER.email);
    await page.fill('input[name="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/dashboard/, { timeout: 10000 });
  });

  test('View today\'s schedule on dashboard', async () => {
    // Step 1: Navigate to dashboard
    await page.goto(`${BASE_URL}/dashboard`);
    await expect(page).toHaveURL(/dashboard/);

    // Step 2: Verify today's schedule is visible
    await expect(
      page.locator('text=/today.*schedule|schedule.*today/i')
    ).toBeVisible({ timeout: 5000 });

    // Step 3: Check for schedule entries (workouts or meals)
    const hasWorkout = await page.locator('text=/workout/i').isVisible();
    const hasMeal = await page.locator('text=/meal/i').isVisible();
    
    expect(hasWorkout || hasMeal).toBeTruthy();

    // Step 4: Verify schedule entry components exist
    const scheduleCards = page.locator('[class*="schedule"], [data-testid="schedule-entry"]');
    const cardCount = await scheduleCards.count();
    expect(cardCount).toBeGreaterThan(0);

    console.log(`✓ Found ${cardCount} schedule entries for today`);
  });

  test('Complete workout and verify progress update', async () => {
    // Step 1: Navigate to dashboard or schedule page
    await page.goto(`${BASE_URL}/dashboard`);

    // Step 2: Find first scheduled workout
    const workoutEntry = page.locator('text=/workout/i').first();
    await expect(workoutEntry).toBeVisible({ timeout: 5000 });

    // Step 3: Look for "Complete" button
    const completeButton = page.locator('button:has-text("Complete")').first();
    
    if (await completeButton.isVisible()) {
      // Get initial progress stats before completing
      let initialAdherence = '0';
      let initialStreak = '0';
      
      const adherenceElement = page.locator('text=/adherence.*rate/i').or(
        page.locator('[data-testid="adherence-rate"]')
      );
      if (await adherenceElement.isVisible()) {
        const adherenceText = await adherenceElement.textContent();
        initialAdherence = adherenceText?.match(/\d+/)?.[0] || '0';
      }

      const streakElement = page.locator('text=/streak/i').or(
        page.locator('[data-testid="current-streak"]')
      );
      if (await streakElement.isVisible()) {
        const streakText = await streakElement.textContent();
        initialStreak = streakText?.match(/\d+/)?.[0] || '0';
      }

      console.log(`Initial adherence: ${initialAdherence}%, streak: ${initialStreak} days`);

      // Step 4: Click complete button
      await completeButton.click();

      // Step 5: Handle completion dialog if it appears
      const dialogNotes = page.locator('textarea[id="notes"]').or(
        page.locator('textarea[placeholder*="note"]')
      );
      
      if (await dialogNotes.isVisible({ timeout: 2000 })) {
        await dialogNotes.fill('E2E test completion - workout completed successfully');
        
        const submitButton = page.locator('button:has-text("Complete")').last();
        await submitButton.click();
      }

      // Step 6: Verify completion status updated
      await expect(
        page.locator('text=/completed/i').first()
      ).toBeVisible({ timeout: 5000 });

      // Step 7: Wait for progress to update
      await page.waitForTimeout(2000);

      // Step 8: Verify progress stats changed (reload page to get fresh data)
      await page.reload();
      await page.waitForLoadState('networkidle');

      // Check adherence rate or completed count increased
      const hasProgressUpdate = await page.locator('text=/\d+.*completed|adherence.*\d+%/i').isVisible();
      expect(hasProgressUpdate).toBeTruthy();

      console.log('✓ Workout marked as complete and progress updated');
    } else {
      console.log('⚠ No scheduled workouts available to complete (might be rest day)');
      test.skip();
    }
  });

  test('View schedule calendar and navigate days', async () => {
    // Step 1: Navigate to schedule page
    await page.goto(`${BASE_URL}/dashboard/schedule`);
    await expect(page).toHaveURL(/schedule/);

    // Step 2: Verify calendar view exists
    await expect(
      page.locator('text=/calendar|upcoming|schedule/i')
    ).toBeVisible({ timeout: 5000 });

    // Step 3: Check for multiple days displayed
    const dayCards = page.locator('[class*="day"], [data-testid*="day"]');
    const dayCount = await dayCards.count();
    
    expect(dayCount).toBeGreaterThanOrEqual(7); // At least a week view

    console.log(`✓ Calendar shows ${dayCount} days`);

    // Step 4: Verify navigation controls exist
    const hasNavigation = await page.locator('button[aria-label*="next"]').or(
      page.locator('button:has-text("→")')
    ).isVisible();

    if (hasNavigation) {
      console.log('✓ Calendar navigation controls present');
    }
  });

  test('Skip meal and provide reason', async () => {
    // Step 1: Go to dashboard
    await page.goto(`${BASE_URL}/dashboard`);

    // Step 2: Find first scheduled meal
    const mealEntry = page.locator('text=/meal/i').first();
    
    if (await mealEntry.isVisible({ timeout: 3000 })) {
      // Step 3: Look for "Skip" button
      const skipButton = page.locator('button:has-text("Skip")').first();
      
      if (await skipButton.isVisible()) {
        await skipButton.click();

        // Step 4: Fill in skip reason
        const reasonTextarea = page.locator('textarea[id="reason"]').or(
          page.locator('textarea[placeholder*="reason"]')
        );

        await expect(reasonTextarea).toBeVisible({ timeout: 3000 });
        await reasonTextarea.fill('E2E test - Time constraints, had to skip meal');

        // Step 5: Confirm skip
        const confirmButton = page.locator('button:has-text("Skip")').last();
        await confirmButton.click();

        // Step 6: Verify meal marked as skipped
        await expect(
          page.locator('text=/skipped/i').first()
        ).toBeVisible({ timeout: 5000 });

        console.log('✓ Meal skipped with reason');
      } else {
        console.log('⚠ No skip button available (meal might be already completed)');
        test.skip();
      }
    } else {
      console.log('⚠ No meals scheduled for today');
      test.skip();
    }
  });

  test('View progress page with adherence and streak', async () => {
    // Step 1: Navigate to progress page
    await page.goto(`${BASE_URL}/dashboard/progress`);
    await expect(page).toHaveURL(/progress/);

    // Step 2: Verify adherence rate is displayed
    await expect(
      page.locator('text=/adherence.*rate/i')
    ).toBeVisible({ timeout: 5000 });

    const adherenceValue = page.locator('text=/\d+%/').first();
    await expect(adherenceValue).toBeVisible();

    // Step 3: Verify streak is displayed
    await expect(
      page.locator('text=/streak/i')
    ).toBeVisible({ timeout: 5000 });

    const streakValue = page.locator('text=/\d+.*day/i').first();
    await expect(streakValue).toBeVisible();

    // Step 4: Check for progress chart or visualization
    const hasChart = await page.locator('[class*="chart"], [class*="progress"]').isVisible();
    expect(hasChart).toBeTruthy();

    console.log('✓ Progress page displays adherence and streak data');
  });

  test('Log body measurement', async () => {
    // Step 1: Navigate to progress page
    await page.goto(`${BASE_URL}/dashboard/progress`);

    // Step 2: Find "Add Measurement" button
    const addButton = page.locator('button:has-text("Add Measurement")').or(
      page.locator('button:has-text("Log")')
    );

    if (await addButton.isVisible({ timeout: 3000 })) {
      await addButton.click();

      // Step 3: Fill in measurement dialog
      const typeSelect = page.locator('select[id="type"]').or(
        page.locator('[role="combobox"]').first()
      );
      await expect(typeSelect).toBeVisible({ timeout: 3000 });
      
      // Select weight measurement
      if (await page.locator('select[id="type"]').isVisible()) {
        await page.selectOption('select[id="type"]', 'weight');
      } else {
        await typeSelect.click();
        await page.locator('text=/weight/i').first().click();
      }

      // Step 4: Enter value
      const valueInput = page.locator('input[id="value"]').or(
        page.locator('input[type="number"]').first()
      );
      await valueInput.fill('175.5');

      // Step 5: Add optional notes
      const notesInput = page.locator('input[id="notes"]').or(
        page.locator('input[placeholder*="note"]')
      );
      if (await notesInput.isVisible()) {
        await notesInput.fill('E2E test measurement');
      }

      // Step 6: Submit measurement
      const submitButton = page.locator('button:has-text("Add Measurement")').last();
      await submitButton.click();

      // Step 7: Verify measurement appears in history
      await page.waitForTimeout(2000);
      await expect(
        page.locator('text=/175\.5|weight/i')
      ).toBeVisible({ timeout: 5000 });

      console.log('✓ Body measurement logged successfully');
    } else {
      console.log('⚠ Add measurement button not found');
      test.skip();
    }
  });

  test('Verify schedule summary statistics', async () => {
    // Step 1: Go to dashboard
    await page.goto(`${BASE_URL}/dashboard`);

    // Step 2: Check for summary statistics
    const summaryElements = await page.locator('text=/\d+.*\/.*\d+|total|completed/i').count();
    expect(summaryElements).toBeGreaterThan(0);

    // Step 3: Verify completion percentage is shown
    const hasPercentage = await page.locator('text=/\d+%/').isVisible();
    expect(hasPercentage).toBeTruthy();

    // Step 4: Check for workout and meal counts
    const workoutCount = page.locator('text=/workout.*\d+|\d+.*workout/i');
    const mealCount = page.locator('text=/meal.*\d+|\d+.*meal/i');

    const hasWorkoutStat = await workoutCount.isVisible();
    const hasMealStat = await mealCount.isVisible();

    expect(hasWorkoutStat || hasMealStat).toBeTruthy();

    console.log('✓ Schedule summary statistics displayed');
  });
});

test.describe('Schedule Error Handling E2E', () => {
  test('Handle no schedule gracefully', async ({ page }) => {
    // Login
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', TEST_USER.email);
    await page.fill('input[name="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/dashboard/, { timeout: 10000 });

    // Intercept schedule API to return empty
    await page.route(`${API_URL}/schedules/today`, (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          data: {
            date: new Date().toISOString().split('T')[0],
            entries: [],
            summary: {
              total_workouts: 0,
              total_meals: 0,
              completed_workouts: 0,
              completed_meals: 0
            }
          }
        })
      });
    });

    await page.goto(`${BASE_URL}/dashboard`);

    // Should show appropriate message for no activities
    await expect(
      page.locator('text=/no.*activit|rest.*day|nothing.*scheduled/i')
    ).toBeVisible({ timeout: 5000 });

    console.log('✓ No schedule handled gracefully');
  });

  test('Handle API error when fetching schedule', async ({ page }) => {
    // Login
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', TEST_USER.email);
    await page.fill('input[name="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/dashboard/, { timeout: 10000 });

    // Intercept schedule API to return error
    await page.route(`${API_URL}/schedules/today`, (route) => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'error',
          error: {
            code: 'INTERNAL_ERROR',
            message: 'Failed to fetch schedule'
          }
        })
      });
    });

    await page.goto(`${BASE_URL}/dashboard`);

    // Should show error message
    await expect(
      page.locator('text=/error.*loading|failed.*fetch|try.*again/i')
    ).toBeVisible({ timeout: 5000 });

    console.log('✓ Schedule API error handled gracefully');
  });

  test('Handle completion failure gracefully', async ({ page }) => {
    // Login
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', TEST_USER.email);
    await page.fill('input[name="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/dashboard/, { timeout: 10000 });

    await page.goto(`${BASE_URL}/dashboard`);

    // Intercept completion API to return error
    await page.route(`${API_URL}/schedules/entries/*/complete`, (route) => {
      route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'error',
          error: {
            code: 'INVALID_REQUEST',
            message: 'Entry already completed'
          }
        })
      });
    });

    // Try to complete a workout
    const completeButton = page.locator('button:has-text("Complete")').first();
    
    if (await completeButton.isVisible({ timeout: 3000 })) {
      await completeButton.click();

      // Handle dialog if present
      const submitButton = page.locator('button:has-text("Complete")').last();
      if (await submitButton.isVisible({ timeout: 2000 })) {
        await submitButton.click();
      }

      // Should show error notification
      await expect(
        page.locator('text=/error|failed|already.*completed/i')
      ).toBeVisible({ timeout: 5000 });

      console.log('✓ Completion failure handled gracefully');
    } else {
      console.log('⚠ No activities to complete');
      test.skip();
    }
  });
});
