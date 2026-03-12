import { test, expect } from '@playwright/test';

test.describe('Claim and Resolve Question Flow', () => {
  test('should allow TA to claim and resolve a question', async ({ page }) => {
    test.setTimeout(60000); // Overall test timeout
    const studentEmail = `student_for_ta_${Date.now()}@example.com`;
    
    // 1. Student submits a question
    await page.goto('/register');
    await page.getByLabel(/Full Name/i).fill('E2E Queue Student');
    await page.getByLabel(/University Email/i).fill(studentEmail);
    await page.getByLabel(/Password/i).fill('SecurePass123!');
    await page.getByLabel(/I am a.../i).selectOption('student');
    await page.getByRole('button', { name: /Register/i }).click();
    await expect(page).toHaveURL(/\/dashboard/);
    
    await page.getByRole('button', { name: 'Join Course', exact: true }).click();
    await page.getByLabel(/Invite Code/i).fill(process.env.SEED_INVITE_CODE as string);
    await page.getByRole('button', { name: 'Join', exact: true }).click();

    await page.locator('text=CS5432').first().click();
    await page.locator('text=Week 2 – Debugging with AI Assistance').first().click();
    
    const questionTitle = `Question for TA ${Date.now()}`;
    await page.getByPlaceholder(/Brief summary/i).fill(questionTitle);
    await page.getByPlaceholder(/Detailed description/i).fill('TA please help me');
    await page.getByPlaceholder(/Steps you/i).fill('Testing E2E');
    await page.getByRole('button', { name: /Submit Question/i }).click();
    await expect(page.locator('text=Queue Status')).toBeVisible({ timeout: 15000 });

    // 2. Logout student, Login TA
    await page.goto('/login');
    await page.getByLabel(/Email/i).fill(process.env.TA_EMAIL as string);
    await page.getByLabel(/Password/i).fill(process.env.TA_PASSWORD as string);
    await page.getByRole('button', { name: /Sign In/i }).click();
    await expect(page).toHaveURL(/\/dashboard/);

    // 3. TA resolves
    await page.locator('text=CS5432').first().click();
    await page.locator('text=Week 2 – Debugging with AI Assistance').first().click();
    await page.waitForLoadState('networkidle');

    // Find our question card (resilient locator)
    // We look for a div with data-testid="question-card" containing the title
    const questionCard = page.locator('[data-testid="question-card"]', { hasText: questionTitle }).first();
    
    // Debug: output content if not visible
    if (!await questionCard.isVisible()) {
      console.log('--- DEBUG: Question card not visible. Current Page Content ---');
      const content = await page.content();
      console.log(content);
      console.log('--- END DEBUG ---');
    }

    await expect(questionCard).toBeVisible({ timeout: 20000 });

    // Click Claim and wait for refresh
    const claimPromise = page.waitForResponse(resp => resp.url().includes('/claim') && resp.status() === 200);
    // Use .first() on the button itself within the card just in case
    await questionCard.getByRole('button', { name: /Claim/i }).first().click();
    await claimPromise;
    await page.waitForLoadState('networkidle');
    
    // Assert the card shows In Progress status
    // The card should now have 'In Progress' text
    const inProgressCard = page.locator('[data-testid="question-card"]', { hasText: questionTitle }).filter({ hasText: 'In Progress' }).first();
    await expect(inProgressCard).toBeVisible({ timeout: 20000 });

    // Click Resolve and wait for refresh
    const resolvePromise = page.waitForResponse(resp => resp.url().includes('/resolve') && resp.status() === 200);
    await inProgressCard.getByRole('button', { name: /Resolve/i }).first().click();
    await resolvePromise;
    await page.waitForLoadState('networkidle');

    // Assert the specific question card is gone
    await expect(page.locator('[data-testid="question-card"]', { hasText: questionTitle })).not.toBeVisible({ timeout: 20000 });
  });
});
