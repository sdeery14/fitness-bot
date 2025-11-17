import { test, expect } from '@playwright/test';

test.describe('Disruption Handling E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to application
    await page.goto('http://localhost:3000');
    
    // Login as test user (assuming authentication is required)
    // This will need to be adjusted based on your actual authentication flow
    await page.goto('http://localhost:3000/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    // Wait for dashboard to load
    await page.waitForURL('**/dashboard');
  });

  test('user can report disruption and see confirmation', async ({ page }) => {
    // 1. Navigate to dashboard
    await expect(page).toHaveURL(/dashboard/);
    
    // 2. Click "Report Disruption" button
    await page.click('button:has-text("Report Disruption")');
    
    // 3. Verify dialog appears
    await expect(page.locator('dialog, [role="dialog"]')).toBeVisible();
    await expect(page.locator('text=Report Schedule Disruption')).toBeVisible();
    
    // 4. Fill out disruption form
    // Select disruption type
    await page.click('button:has-text("Illness")');
    
    // Select severity
    await page.click('button:has-text("Moderate")');
    
    // Set start date (today)
    const today = new Date().toISOString().split('T')[0];
    await page.fill('input[name="start_date"]', today);
    
    // Set end date (7 days from now)
    const endDate = new Date();
    endDate.setDate(endDate.getDate() + 7);
    const endDateStr = endDate.toISOString().split('T')[0];
    await page.fill('input[name="end_date"]', endDateStr);
    
    // Fill description
    await page.fill('textarea[name="description"]', 
      'Got the flu. Unable to work out for about a week. Need to adjust my schedule.');
    
    // 5. Submit the form
    await page.click('button:has-text("Submit")');
    
    // 6. Wait for success toast/notification
    await expect(page.locator('text=successfully')).toBeVisible({ timeout: 10000 });
    
    // 7. Verify dialog closes
    await expect(page.locator('dialog, [role="dialog"]')).not.toBeVisible();
  });

  test('disruption form validates required fields', async ({ page }) => {
    // Open dialog
    await page.click('button:has-text("Report Disruption")');
    await expect(page.locator('dialog, [role="dialog"]')).toBeVisible();
    
    // Try to submit without filling fields
    await page.click('button:has-text("Submit")');
    
    // Should see validation errors
    await expect(page.locator('text=required')).toBeVisible();
  });

  test('disruption form validates description length', async ({ page }) => {
    // Open dialog
    await page.click('button:has-text("Report Disruption")');
    
    // Fill minimum required fields
    await page.click('button:has-text("Illness")');
    await page.click('button:has-text("Minor")');
    
    const today = new Date().toISOString().split('T')[0];
    await page.fill('input[name="start_date"]', today);
    
    // Try with too short description (< 10 chars)
    await page.fill('textarea[name="description"]', 'Too short');
    await page.click('button:has-text("Submit")');
    
    // Should see validation error about minimum length
    await expect(page.locator('text=at least 10 characters')).toBeVisible();
  });

  test('user can cancel disruption report', async ({ page }) => {
    // Open dialog
    await page.click('button:has-text("Report Disruption")');
    await expect(page.locator('dialog, [role="dialog"]')).toBeVisible();
    
    // Fill some data
    await page.click('button:has-text("Travel")');
    await page.fill('textarea[name="description"]', 'Going on vacation for a week');
    
    // Click cancel
    await page.click('button:has-text("Cancel")');
    
    // Dialog should close without submitting
    await expect(page.locator('dialog, [role="dialog"]')).not.toBeVisible();
  });

  test('severe disruption shows appropriate messaging', async ({ page }) => {
    // Open dialog
    await page.click('button:has-text("Report Disruption")');
    
    // Select injury + severe
    await page.click('button:has-text("Injury")');
    await page.click('button:has-text("Severe")');
    
    // Should see severity description
    await expect(page.locator('text=Major impact')).toBeVisible();
    
    const today = new Date().toISOString().split('T')[0];
    await page.fill('input[name="start_date"]', today);
    
    const endDate = new Date();
    endDate.setDate(endDate.getDate() + 14);
    await page.fill('input[name="end_date"]', endDate.toISOString().split('T')[0]);
    
    await page.fill('textarea[name="description"]', 
      'Serious back injury. Cannot exercise for at least 2 weeks. Doctor recommended complete rest.');
    
    // Submit
    await page.click('button:has-text("Submit")');
    
    // Should get success confirmation
    await expect(page.locator('text=successfully')).toBeVisible({ timeout: 10000 });
  });

  test('ongoing disruption can be reported without end date', async ({ page }) => {
    // Open dialog
    await page.click('button:has-text("Report Disruption")');
    
    // Select personal emergency
    await page.click('button:has-text("Personal Emergency")');
    await page.click('button:has-text("Severe")');
    
    // Set only start date (no end date for ongoing situation)
    const today = new Date().toISOString().split('T')[0];
    await page.fill('input[name="start_date"]', today);
    
    await page.fill('textarea[name="description"]', 
      'Family emergency. Not sure when I can resume my fitness routine.');
    
    // Submit
    await page.click('button:has-text("Submit")');
    
    // Should handle ongoing disruption
    await expect(page.locator('text=successfully')).toBeVisible({ timeout: 10000 });
  });
});
