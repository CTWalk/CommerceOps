/**
 * Human-like navigation helpers for the CommerceOps E2E suite.
 *
 * These replace direct URL jumps with the real clicks a human tester would
 * perform, so the regression suite exercises the app's routing/linking and
 * canonical parent ownership exactly as a user does.
 */

import { Page, expect } from '@playwright/test';

/** Opens a product detail page from Shop through its exact card. */
export async function openProductFromStore(page: Page, productName: string): Promise<void> {
  // Since the Home/Shop split, the customer lands on Home, which carries preview
  // media rather than the authoritative catalog grid. Ensure Shop owns the view
  // before looking for a product card.
  if (!/\/store/.test(page.url())) {
    await returnToShop(page);
  }
  const card = page.locator('article.product-card').filter({
    has: page.getByRole('heading', { level: 2, name: productName, exact: true })
  });
  await expect(card).toHaveCount(1);
  await card.getByRole('link', { name: `View ${productName}`, exact: true }).click();
}

/** Opens store selection from the Home fulfillment preview. */
export async function openStoresFromHome(page: Page): Promise<void> {
  await page.getByTestId('home-change-store').click();
  await expect(page).toHaveURL(/\/stores/);
}

/** Opens scan from the Shop heading using the actual customer CTA. */
export async function openScanFromShop(page: Page): Promise<void> {
  const scanLink = page.getByRole('link', { name: 'Scan item', exact: true });
  await scanLink.scrollIntoViewIfNeeded();
  await scanLink.click();
  await expect(page).toHaveURL(/\/scan/);
}

/** Opens the account utility from customer chrome. */
export async function openProfileFromCustomer(page: Page): Promise<void> {
  await page.getByRole('link', { name: 'Profile', exact: true }).first().click();
  await expect(page).toHaveURL(/\/profile/);
}

/** Opens customer Help from the Account landing page. */
export async function openHelpFromProfile(page: Page): Promise<void> {
  await page.getByRole('link', { name: /Help center/ }).click();
  await expect(page).toHaveURL(/\/help/);
}

/** Returns to the customer Home root through global navigation. */
export async function returnToCustomerHome(page: Page): Promise<void> {
  const mobileHome = page.getByTestId('mobile-tab-home');
  if (await mobileHome.isVisible().catch(() => false)) {
    await mobileHome.click();
  } else {
    await page.getByRole('link', { name: 'Home', exact: true }).first().click();
  }
  await expect(page).toHaveURL(/\/home/);
}

/** Returns to the Shop/catalog root through global navigation. */
export async function returnToShop(page: Page): Promise<void> {
  const mobileShop = page.getByTestId('mobile-tab-shop');
  if (await mobileShop.isVisible().catch(() => false)) {
    await mobileShop.click();
  } else {
    await page.getByRole('link', { name: 'Shop', exact: true }).first().click();
  }
  await expect(page).toHaveURL(/\/store/);
}
