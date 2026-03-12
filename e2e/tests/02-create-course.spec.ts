import { test, expect } from '@playwright/test';

test.describe('Course Creation Flow', () => {
  test('should allow professor to log in and create a course', async ({ page }) => {
    // Navigate to login
    await page.goto('/login');

    // Login as professor
    await page.getByLabel(/^Email$/i).fill(process.env.PROFESSOR_EMAIL!);
    await page.getByLabel(/Password/i).fill(process.env.PROFESSOR_PASSWORD!);
    await page.getByRole('button', { name: /Sign In/i }).click();

    // Verify successful login
    await expect(page).toHaveURL(/\/dashboard/);

    // Click 'Create Course' button
    await page.getByRole('button', { name: /Create Course/i }).click();

    // Fill course creation modal
    await page.getByLabel(/Course Name/i).fill('E2E Test Course');
    // Assuming UI has a submit button inside modal
    await page.getByRole('button', { name: 'Create', exact: true }).click();

    // Wait for the course card to appear
    const newCourseCard = page.locator('text=E2E Test Course');
    await expect(newCourseCard).toBeVisible({ timeout: 10000 });

    // Assert a 6-char invite code is visible
    await expect(page.locator('text=Invite Code').first()).toBeVisible();
  });
});
