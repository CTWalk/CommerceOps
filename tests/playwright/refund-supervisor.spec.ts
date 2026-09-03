import { expect, finishFailureDiagnostics, type Page, startFailureDiagnostics, test } from '../helpers/failure-diagnostics';
import { openProductFromStore } from '../helpers/navigation';
import { createSnapshotter } from '../helpers/screenshot';
import { TEST_IDS } from '../shared/testids';

test.beforeEach(async ({ page }, testInfo) => startFailureDiagnostics(page, testInfo));
test.afterEach(async ({ page }, testInfo) => finishFailureDiagnostics(page, testInfo));

async function login(page: Page, email: string, destination: RegExp) {
  await page.goto('/login');
  await page.getByTestId(TEST_IDS.loginEmail).fill(email);
  await page.getByTestId(TEST_IDS.loginPassword).fill('commerce-demo');
  await page.getByTestId(TEST_IDS.loginSubmit).click();
  await expect(page).toHaveURL(destination);
}

async function logout(page: Page) {
  await expect(page.locator('.session-chip')).toBeVisible();
  const staffLogout = page.getByRole('button', { name: 'Logout' });
  if (await staffLogout.count()) {
    await staffLogout.click();
  } else {
    await page.getByRole('link', { name: 'Profile' }).first().click();
    await page.getByTestId('account-logout').click();
  }
  await expect(page).toHaveURL(/\/login/);
}

async function orderState(page: Page, orderId: string) {
  const response = await page.request.get('/api/state');
  expect(response.ok()).toBeTruthy();
  const { state } = await response.json();
  return state.orders.find((order: { id: string }) => order.id === orderId);
}

async function requiredCapture(
  page: Page,
  snap: (label: string) => Promise<void>,
  label: string,
  width: number,
  height: number,
) {
  await page.setViewportSize({ width, height });
  await expect(page.locator('.toast')).toHaveCount(0);
  await expect(page.locator('main.page').first()).toHaveCSS('opacity', '1');
  await expect.poll(async () => page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    viewportWidth: window.innerWidth,
  }))).toMatchObject({ scrollWidth: width, viewportWidth: width });
  await snap(`${label}_${width}x${height}`);
}

test.describe('Supervisor-approved refund workflow', () => {
  test.beforeEach(async ({ request }) => {
    await request.post('/api/reset');
  });

  test('RF-01: one refund case moves through customer, review, approval, completion, and customer receipt', async ({ page }) => {
    const snap = createSnapshotter(page, 'RF-01', 'Customer_case_approval_refund_handoff');
    let orderId = '';
    await page.setViewportSize({ width: 360, height: 800 });

    await test.step('1. Customer buys a product and payment is confirmed', async () => {
      await login(page, 'customer@example.com', /\/home/);
      await openProductFromStore(page, 'Packable Rain Shell');
      await page.getByTestId('product-variant-M').click();
      await page.getByTestId(TEST_IDS.productAddToCart).click();
      await expect(page).toHaveURL(/\/cart/);
      await page.getByTestId(TEST_IDS.cartCheckout).click();
      await expect(page).toHaveURL(/\/checkout/);
      await page.getByTestId(TEST_IDS.checkoutAddressName).fill('Refund Flow Customer');
      await page.getByTestId(TEST_IDS.checkoutAddressLine).fill('8 Traceable Way');
      await page.getByTestId(TEST_IDS.checkoutCity).fill('Taipei');
      await page.getByTestId(TEST_IDS.checkoutRequestQuote).click();
      await expect(page.locator('.checkout-ready-line')).toContainText(/^Delivery ·/);
      const payment = page.frameLocator('[data-testid="checkout-payment-frame"]');
      await payment.locator('[name="cardName"]').fill('Refund Flow Customer');
      await payment.locator('[name="cardNumber"]').fill('4242424242424242');
      await payment.locator('[name="cardExpiry"]').fill('12/30');
      await payment.locator('[name="cardCvc"]').fill('123');
      await payment.locator('button[type="submit"]').click();
      await expect(page.getByTestId(TEST_IDS.checkoutPaymentStatus)).toContainText('Payment ready');
      await page.getByTestId(TEST_IDS.checkoutPlaceOrder).click();
      await expect(page).toHaveURL(/\/orders/);
      const state = await page.request.get('/api/state').then((response) => response.json());
      orderId = state.state.orders[0].id;
      expect(state.state.orders[0]).toMatchObject({ id: orderId, paymentStatus: 'paid', refundStatus: 'none' });
    });

    await test.step('2. Customer opens the same order and sees refund is available', async () => {
      await page.getByTestId(`order-row-${orderId}`).click();
      await expect(page.locator('h1')).toHaveText(orderId);
      await expect(page.getByTestId(TEST_IDS.orderRequestRefund)).toBeEnabled();
    });

    await test.step('3. Customer requests a refund and sees customer-facing lifecycle language', async () => {
      await page.getByTestId(TEST_IDS.orderReturnReason).fill('The size did not fit.');
      await page.getByTestId(TEST_IDS.orderRequestRefund).click();
      await expect(page.locator('.toast', { hasText: 'Refund request saved.' })).toBeVisible();
      const lifecycle = page.getByTestId('order-refund-lifecycle');
      await expect(lifecycle).toContainText('Refund requested');
      await expect(lifecycle).toContainText("We're reviewing your request. No action is needed right now.");
      await expect(lifecycle).toContainText('The size did not fit.');
      expect(await orderState(page, orderId)).toMatchObject({ refundStatus: 'requested' });
      await page.evaluate(() => window.scrollTo(0, 0));
      await requiredCapture(page, snap, 'Customer_refund_requested', 360, 800);
    });

    await test.step('4. Case handler sees a glanceable queue and one dominant action', async () => {
      await logout(page);
      await login(page, 'support@example.com', /\/support/);

      await page.evaluate(() => window.scrollTo(0, 0));
      await requiredCapture(page, snap, 'Case_handler_queue', 360, 800);
      await requiredCapture(page, snap, 'Case_handler_queue', 412, 915);

      await page.setViewportSize({ width: 360, height: 800 });
      await page.getByTestId(TEST_IDS.supportRefundTodo.replace('{orderId}', orderId)).click();
      await expect(page.locator('[aria-label="Case status"]')).toContainText('Needs review');
      await expect(page.locator('[aria-label="Case status"]')).toContainText('The size did not fit.');
      await expect(page.getByTestId(TEST_IDS.supportEscalateRefund)).toHaveText(/Send for approval/);
      await expect(page.getByTestId(TEST_IDS.supportRefund)).toHaveCount(0);

      // Secondary context is a separate screen, not first-screen reading load.
      await expect(page.locator('[aria-label="Order context"]')).toHaveCount(0);
      await expect(page.getByTestId(TEST_IDS.supportNoteInput)).toHaveCount(0);
      await expect(page.locator('#support-order-details-disclosure')).toBeVisible();
      await expect(page.locator('#support-notes-disclosure')).toBeVisible();

      const actionSurface = page.getByTestId('support-primary-work-action');
      await expect(actionSurface.locator('button.primary')).toHaveCount(1);
      await expect(actionSurface.getByTestId(TEST_IDS.supportEscalateRefund)).toBeVisible();
      await actionSurface.scrollIntoViewIfNeeded();
      await requiredCapture(page, snap, 'Case_handler_send_for_approval', 360, 800);
      await actionSurface.scrollIntoViewIfNeeded();
      await requiredCapture(page, snap, 'Case_handler_send_for_approval', 412, 915);
      await page.setViewportSize({ width: 360, height: 800 });
    });

    await test.step('5. Case handler sends the refund for approval', async () => {
      await page.getByTestId(TEST_IDS.supportEscalateRefund).scrollIntoViewIfNeeded();
      await page.getByTestId(TEST_IDS.supportEscalateRefund).click();
      await expect(page.locator('.toast', { hasText: 'Sent for approval.' })).toBeVisible();
      expect(await orderState(page, orderId)).toMatchObject({ refundStatus: 'escalated' });
      await expect(page.locator('[aria-label="Case status"]')).toContainText('Approval required');
      await expect(page.getByTestId(TEST_IDS.supportEscalateRefund)).toHaveCount(0);
      await expect(page.getByTestId(TEST_IDS.supportRefund)).toHaveCount(0);

      await page.locator('#support-case-back').click();
      await page.locator('#support-work-waiting').click();
      await expect(page.getByTestId(`support-order-${orderId}`)).toBeVisible();
      await expect(page.getByTestId(TEST_IDS.supportRefundTodo.replace('{orderId}', orderId))).toHaveCount(0);
    });

    await test.step('6. Approver reviews the same case and approves it', async () => {
      await logout(page);
      await login(page, 'supervisor@example.com', /\/supervisor/);
      await page.getByTestId(`support-order-${orderId}`).click();
      await expect(page.locator('[aria-label="Case status"]')).toContainText('Approval required');
      await expect(page.getByTestId(TEST_IDS.supervisorApproveRefund)).toHaveText(/Approve refund/);
      const actionSurface = page.getByTestId('support-primary-work-action');
      await expect(actionSurface.locator('button.primary')).toHaveCount(1);
      await expect(actionSurface.getByTestId(TEST_IDS.supervisorApproveRefund)).toBeVisible();
      await actionSurface.scrollIntoViewIfNeeded();
      await requiredCapture(page, snap, 'Approver_approval_required', 360, 800);
      await actionSurface.scrollIntoViewIfNeeded();
      await requiredCapture(page, snap, 'Approver_approval_required', 412, 915);
      await page.setViewportSize({ width: 360, height: 800 });
      await page.getByTestId(TEST_IDS.supervisorApproveRefund).scrollIntoViewIfNeeded();
      await page.getByTestId(TEST_IDS.supervisorApproveRefund).click();
      await expect(page.locator('.toast', { hasText: 'Refund approved and handed off for completion.' })).toBeVisible();
      expect(await orderState(page, orderId)).toMatchObject({ refundStatus: 'pending_cs_confirmation' });
    });

    await test.step('7. Case handler completes the approved refund', async () => {
      await logout(page);
      await login(page, 'support@example.com', /\/support/);
      await page.getByTestId(TEST_IDS.supportRefundTodo.replace('{orderId}', orderId)).click();
      await expect(page.locator('[aria-label="Case status"]')).toContainText('Ready to complete');
      await expect(page.getByTestId(TEST_IDS.supportRefund)).toHaveText(/Complete refund/);
      const actionSurface = page.getByTestId('support-primary-work-action');
      await expect(actionSurface.locator('button.primary')).toHaveCount(1);
      await expect(actionSurface.getByTestId(TEST_IDS.supportRefund)).toBeVisible();
      await actionSurface.scrollIntoViewIfNeeded();
      await requiredCapture(page, snap, 'Case_handler_complete_refund', 360, 800);
      await page.getByTestId(TEST_IDS.supportRefund).click();
      await expect(page.locator('.toast', { hasText: 'Refund completed.' })).toBeVisible();
      expect(await orderState(page, orderId)).toMatchObject({ refundStatus: 'refunded', status: 'refunded' });

      await page.locator('#support-case-back').click();
      await page.locator('#support-work-done').click();
      await expect(page.getByTestId(`support-order-${orderId}`)).toBeVisible();
      await expect(page.locator('[aria-label="Done"]')).toContainText(orderId);
    });

    await test.step('8. Customer sees the completed refund without internal handoff language', async () => {
      await logout(page);
      await login(page, 'customer@example.com', /\/home/);
      await page.getByRole('link', { name: 'Orders' }).click();
      await expect(page.locator('.order-row').filter({ hasText: orderId }).locator('.order-exception-status')).toHaveText('Refund complete');
      await page.getByTestId(`order-row-${orderId}`).click();
      const lifecycle = page.getByTestId('order-refund-lifecycle');
      await expect(lifecycle).toContainText('Refund complete');
      await expect(lifecycle).toContainText('Your refund has been completed.');
      await expect(lifecycle).not.toContainText('Customer Service');
      await expect(lifecycle).not.toContainText('supervisor');
      await page.evaluate(() => window.scrollTo(0, 0));
      await requiredCapture(page, snap, 'Customer_refund_complete', 360, 800);

      const events = (await page.request.get('/api/events').then((response) => response.json())).events;
      const handoffs = events
        .filter((event: { eventType: string; entityId: string }) => event.entityId === orderId && [
          'order_placed',
          'refund_requested',
          'refund_escalated',
          'refund_supervisor_approved',
          'refund_cs_confirmed',
          'refund_succeeded',
        ].includes(event.eventType))
        .map((event: { eventType: string; role: string; details: { from?: string; to?: string } }) => ({
          eventType: event.eventType,
          role: event.role,
          from: event.details.from,
          to: event.details.to,
        }));
      expect(handoffs).toEqual([
        { eventType: 'order_placed', role: 'customer', from: undefined, to: undefined },
        { eventType: 'refund_requested', role: 'customer', from: 'none', to: 'requested' },
        { eventType: 'refund_escalated', role: 'support', from: 'requested', to: 'escalated' },
        { eventType: 'refund_supervisor_approved', role: 'supervisor', from: 'escalated', to: 'pending_cs_confirmation' },
        { eventType: 'refund_cs_confirmed', role: 'support', from: 'pending_cs_confirmation', to: 'refunded' },
        { eventType: 'refund_succeeded', role: 'support', from: 'pending_cs_confirmation', to: 'refunded' },
      ]);
    });
  });
});
