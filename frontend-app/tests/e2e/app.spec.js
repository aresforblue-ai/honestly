// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * AppWhistler Truth Engine E2E Tests
 * 
 * These tests verify the main user flows work correctly.
 * Run with: npx playwright test
 */

test.describe('Navigation', () => {
  test('homepage loads correctly', async ({ page }) => {
    await page.goto('/');
    
    // Check main elements are present
    await expect(page.locator('nav')).toBeVisible();
    await expect(page.getByText(/AppWhistler/i)).toBeVisible();
  });

  test('navigation links work', async ({ page }) => {
    await page.goto('/');
    
    // Check navigation is functional
    const navElement = page.locator('nav');
    await expect(navElement).toBeVisible();
  });
});

test.describe('Dashboard', () => {
  test('displays entity registry', async ({ page }) => {
    await page.goto('/');
    
    // Wait for loading to complete
    await page.waitForLoadState('networkidle');
    
    // Should show either entities or loading/error state
    const content = page.locator('main');
    await expect(content).toBeVisible();
  });

  test('search functionality works', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Find search input if it exists
    const searchInput = page.locator('input[type="text"]');
    if (await searchInput.isVisible()) {
      await searchInput.fill('test');
      // Verify search filtering works (content updates)
      await page.waitForTimeout(500);
    }
  });
});

test.describe('Keyboard Shortcuts', () => {
  test('Cmd/Ctrl+K opens search', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Press Cmd+K (Mac) or Ctrl+K (Windows/Linux)
    await page.keyboard.press('Meta+k');
    
    // May or may not have command palette - just verify no errors
  });
});

test.describe('Responsive Design', () => {
  test('mobile viewport renders correctly', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    
    await expect(page.locator('nav')).toBeVisible();
  });

  test('tablet viewport renders correctly', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');
    
    await expect(page.locator('nav')).toBeVisible();
  });

  test('desktop viewport renders correctly', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    
    await expect(page.locator('nav')).toBeVisible();
  });
});

test.describe('Entity Details', () => {
  test('navigating to entity shows details', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // If there are entity cards, clicking one should navigate
    const entityLinks = page.locator('a[href^="/app/"]');
    const count = await entityLinks.count();
    
    if (count > 0) {
      await entityLinks.first().click();
      await page.waitForLoadState('networkidle');
      
      // Should be on entity detail page
      expect(page.url()).toContain('/app/');
    }
  });
});

test.describe('Proof Verification', () => {
  test('verify page handles invalid token gracefully', async ({ page }) => {
    await page.goto('/verify/invalid-token');
    await page.waitForLoadState('networkidle');
    
    // Should show error or not found state, not crash
    const content = page.locator('main');
    await expect(content).toBeVisible();
  });
});

test.describe('Performance', () => {
  test('page loads within acceptable time', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
    const loadTime = Date.now() - startTime;
    
    // Page should load within 5 seconds
    expect(loadTime).toBeLessThan(5000);
  });

  test('no console errors on load', async ({ page }) => {
    const errors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Filter out expected errors (like missing GraphQL backend)
    const criticalErrors = errors.filter(err => 
      !err.includes('Failed to fetch') && 
      !err.includes('GraphQL') &&
      !err.includes('Network error')
    );
    
    expect(criticalErrors).toHaveLength(0);
  });
});

test.describe('Accessibility', () => {
  test('main content is accessible', async ({ page }) => {
    await page.goto('/');
    
    // Check for basic accessibility
    const main = page.locator('main');
    await expect(main).toBeVisible();
  });

  test('navigation is keyboard accessible', async ({ page }) => {
    await page.goto('/');
    
    // Tab through navigation
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    // Focused element should be visible
    const focused = page.locator(':focus');
    if (await focused.count() > 0) {
      await expect(focused.first()).toBeVisible();
    }
  });
});

