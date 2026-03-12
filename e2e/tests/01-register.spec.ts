import { test, expect } from '@playwright/test';

test.describe('Registration Flow', () => {
  test('should register a new student and redirect to dashboard', async ({ page }) => {
    await page.goto('/register');

    const uniqueEmail = `test.student.${Date.now()}@example.com`;

    // Fill the registration form
    await page.getByLabel(/Full Name/i).fill('Test Student E2E');
    await page.getByLabel(/University Email/i).fill(uniqueEmail);
    await page.getByLabel(/Password/i).fill('SecurePass123!');
    
    // Select role
    await page.getByLabel(/I am a.../i).selectOption('student');

    // Submit
    await page.getByRole('button', { name: /Register/i }).click();

    // Verify redirect
    await expect(page).toHaveURL(/\/dashboard/);
    
    // Assert dashboard UI
    await expect(page.getByRole('heading', { name: /Your Courses/i })).toBeVisible({ timeout: 10000 });
  });
});
