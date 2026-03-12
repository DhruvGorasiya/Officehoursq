import { test, expect } from '@playwright/test';

test.describe('Submit Question Flow', () => {
  test('should allow student to submit a question to an active session', async ({ page }) => {
    const uniqueEmail = `test_student_${Date.now()}@example.com`;
    
    // Register fresh student
    await page.goto('/register');
    await page.getByLabel(/Full Name/i).fill('E2E Student');
    await page.getByLabel(/University Email/i).fill(uniqueEmail);
    await page.getByLabel(/Password/i).fill('SecurePass123!');
    await page.getByLabel(/I am a.../i).selectOption('student');
    await page.getByRole('button', { name: /Register/i }).click();
    await expect(page).toHaveURL(/\/dashboard/);

    // Join CS5432
    await page.getByRole('button', { name: 'Join Course', exact: true }).click();
    await page.getByLabel(/Invite Code/i).fill(process.env.SEED_INVITE_CODE as string);
    await page.getByRole('button', { name: 'Join', exact: true }).click();
    await expect(page.locator('text=CS5432')).toBeVisible();

    // Navigate to active session
    await page.locator('text=CS5432').first().click();
    await page.locator('text=Week 2 – Debugging with AI Assistance').first().click();
    
    // Fill question form
    await page.getByPlaceholder(/Brief summary/i).fill('Test E2E Question');
    await page.getByPlaceholder(/Detailed description/i).fill('I am testing the E2E queue submission');
    await page.getByPlaceholder(/Steps you/i).fill('Running playwright tests');
    
    await page.getByLabel(/Category/i).selectOption('debugging');
    await page.getByLabel(/Priority/i).selectOption('high');

    // Submit Question
    await page.getByRole('button', { name: /Submit Question/i }).click();

    // Assert queue status screen appears
    await expect(page.locator('text=Queue Status')).toBeVisible({ timeout: 15000 });
  });
});
