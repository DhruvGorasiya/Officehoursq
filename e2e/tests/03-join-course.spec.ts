import { test, expect } from '@playwright/test';

test.describe('Join Course Flow', () => {
  test('should allow student to join a course with an invite code', async ({ page }) => {
    // Navigate and login as student
    await page.goto('/login');
    await page.getByLabel(/^Email$/i).fill(process.env.STUDENT_EMAIL as string);
    await page.getByLabel(/Password/i).fill(process.env.STUDENT_PASSWORD as string);
    await page.getByRole('button', { name: /Sign In/i }).click();

    // Verify dashboard redirect
    await expect(page).toHaveURL(/\/dashboard/);

    // Click 'Join Course' button
    await page.getByRole('button', { name: /Join Course/i }).click();

    // Fill the invite code modal
    await page.getByLabel(/Invite Code/i).fill(process.env.SEED_INVITE_CODE as string);
    await page.getByRole('button', { name: 'Join', exact: true }).click();

    // Assert the CS5432 course appears in the dashboard
    const courseCard = page.locator('text=CS5432');
    await expect(courseCard).toBeVisible({ timeout: 10000 });
  });
});
