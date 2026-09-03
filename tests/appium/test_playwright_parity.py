import time

from selenium.common.exceptions import StaleElementReferenceException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from mobile.conftest import first_webview, wait_url
from mobile.test_hybrid import (
    api_request,
    by_testid,
    login_customer,
    login_role,
    logout,
    open_shop,
    submit_payment_frame,
    wait_backend,
)
from shared import trace
from shared.testids import TEST_IDS


def wait_toast(driver, text, timeout=15):
    xpath = (
        "//*[contains(concat(' ', normalize-space(@class), ' '), ' toast ') "
        f"and contains(normalize-space(.), {text!r})]"
    )

    def visible_toast(current):
        for element in current.find_elements(By.XPATH, xpath):
            if element.is_displayed():
                return element
        return False

    return WebDriverWait(driver, timeout).until(visible_toast)


def wait_for_toasts_to_clear(driver, timeout=5):
    return WebDriverWait(
        driver,
        timeout,
        ignored_exceptions=(StaleElementReferenceException,),
    ).until(
        lambda current: not any(
            toast.is_displayed()
            for toast in current.find_elements(By.CSS_SELECTOR, ".toast")
        )
    )


def click_testid_centered(driver, testid, timeout=15):
    positioned = False

    def click_when_ready(current):
        try:
            current.hide_keyboard()
        except WebDriverException:
            pass
        element = current.find_element(By.CSS_SELECTOR, f'[data-testid="{testid}"]')
        nonlocal positioned
        if not positioned:
            current.execute_script(
                "arguments[0].scrollIntoView({ block: 'center', inline: 'nearest' });",
                element,
            )
            positioned = True
        placement = current.execute_script(
            """
            const rect = arguments[0].getBoundingClientRect();
            const header = document.querySelector('.topbar')?.getBoundingClientRect().bottom || 0;
            const bottoms = [window.innerHeight];
            const tabbar = document.querySelector('.customer-mobile-tabbar');
            if (tabbar && !tabbar.contains(arguments[0])) {
              bottoms.push(tabbar.getBoundingClientRect().top);
            }
            for (const selector of ['.cart-checkout-bar', '.checkout-submit-bar']) {
              const fixedAction = document.querySelector(selector);
              if (fixedAction && !fixedAction.contains(arguments[0])) {
                bottoms.push(fixedAction.getBoundingClientRect().top);
              }
            }
            const bottom = Math.min(...bottoms);
            const centerX = rect.left + rect.width / 2;
            const centerY = rect.top + rect.height / 2;
            const hit = document.elementFromPoint(centerX, centerY);
            const unobscured = hit === arguments[0] || arguments[0].contains(hit);
            if (rect.top < header) {
              return { ready: false, correction: rect.top - header - 24 };
            }
            if (rect.bottom > bottom) {
              return { ready: false, correction: rect.bottom - bottom + 24 };
            }
            if (!unobscured) {
              return { ready: false, correction: 180 };
            }
            return { ready: true, correction: 0 };
            """,
            element,
        )
        if not placement["ready"]:
            current.execute_script("window.scrollBy(0, arguments[0]);", placement["correction"])
            return False
        current.find_element(By.CSS_SELECTOR, f'[data-testid="{testid}"]').click()
        return True

    WebDriverWait(
        driver,
        timeout,
        ignored_exceptions=(StaleElementReferenceException,),
    ).until(click_when_ready)


def add_packable_rain_shell(driver, variant="M"):
    open_shop(driver)
    click_testid_centered(driver, "store-product-packable-rain-shell")
    wait_url(driver, "#/product/packable-rain-shell")
    click_testid_centered(driver, f"product-variant-{variant}")
    click_testid_centered(driver, TEST_IDS["productAddToCart"])
    wait_url(driver, "#/cart")


def open_checkout(driver, variant="M"):
    add_packable_rain_shell(driver, variant=variant)
    click_testid_centered(driver, TEST_IDS["cartCheckout"])
    first_webview(driver)
    by_testid(driver, TEST_IDS["checkoutAddressName"])


def order_from_state(state, order_id):
    return next(order for order in state["orders"] if order["id"] == order_id)


def latest_customer_order_placed(state):
    return next(
        (
            event
            for event in reversed(state["events"])
            if event["eventType"] == "order_placed"
            and event["role"] == "customer"
            and event["entityType"] == "order"
        ),
        None,
    )


def capture_rf01_checkpoint(driver, checkpoint, state, order_id):
    """Keep Appium's RF-01 evidence as explicit as Maestro's named checkpoints."""
    order = order_from_state(state, order_id)
    handoffs = [
        {
            "eventType": event["eventType"],
            "role": event["role"],
            "from": event["details"].get("from"),
            "to": event["details"].get("to"),
        }
        for event in state["events"]
        if event["entityId"] == order_id
        and event["eventType"]
        in {
            "order_placed",
            "refund_requested",
            "refund_escalated",
            "refund_supervisor_approved",
            "refund_cs_confirmed",
            "refund_succeeded",
        }
    ]
    artifact = {
        "checkpoint": checkpoint,
        "order": {
            "id": order["id"],
            "status": order["status"],
            "paymentStatus": order["paymentStatus"],
            "refundStatus": order["refundStatus"],
            "fulfillmentStatus": order["fulfillmentStatus"],
        },
        "handoffs": handoffs,
    }
    trace.record("rf01_checkpoint", **artifact)
    trace.write_json(f"rf01-{checkpoint}.json", artifact)
    directory = trace.artifact_dir()
    if not directory:
        return
    try:
        driver.get_screenshot_as_file(str(directory / f"rf01-{checkpoint}.png"))
    except WebDriverException as error:
        trace.record("evidence_capture_error", checkpoint=checkpoint, artifact="screenshot", error=str(error))


def test_sc04_route_guard_prevents_wrong_role_ui_access(driver):
    first_webview(driver)
    login_customer(driver)
    driver.execute_script("window.location.hash = '#/reports'")
    wait_url(driver, "#/access-denied")
    session = api_request(driver, "/auth/session")
    assert session.get("httpStatus") == 200, session
    assert session["body"]["authenticated"] is True, session
    assert session["body"]["user"]["role"] == "customer", session


def test_sc05_backend_api_rejects_bypassed_restricted_call(driver):
    first_webview(driver)
    login_customer(driver)
    forbidden = api_request(driver, "/orders")
    assert forbidden.get("httpStatus") == 403, forbidden
    assert forbidden["body"]["error"] == "This account cannot perform that action.", forbidden


def test_sc08_operations_canvas_report_renders(driver):
    first_webview(driver)
    login_role(driver, email="ops@example.com", role="operations", landing="#/ops/inventory")
    WebDriverWait(driver, 15).until(
        lambda current: current.find_element(By.XPATH, "//a[normalize-space()='Reports']")
    ).click()
    wait_url(driver, "#/reports")
    canvas = by_testid(driver, TEST_IDS["reportCanvas"])
    assert canvas.is_displayed()
    dimensions = driver.execute_script(
        "return {width: arguments[0].width, height: arguments[0].height};", canvas
    )
    assert dimensions["width"] >= 800, dimensions
    assert dimensions["height"] > 0, dimensions


def test_sc09_welcome20_ui_acknowledges_but_backend_rejects(driver):
    first_webview(driver)
    login_customer(driver)
    add_packable_rain_shell(driver, variant="M")
    by_testid(driver, TEST_IDS["cartCouponInput"]).send_keys("WELCOME20")
    click_testid_centered(driver, TEST_IDS["cartCouponApply"])
    wait_toast(driver, "Promo code checked.")
    state = wait_backend(
        "WELCOME20 backend rejection persisted",
        lambda current: current["coupon"]["status"] == "rejected",
    )
    assert state["coupon"]["code"] == "WELCOME20", state["coupon"]
    assert "WELCOME20 is expired" in state["coupon"]["reason"], state["coupon"]


def test_sc10_shipping_quote_delay_is_real_and_observable(driver):
    first_webview(driver)
    login_customer(driver)
    open_checkout(driver, variant="M")
    by_testid(driver, TEST_IDS["checkoutAddressName"]).send_keys("John Test")
    by_testid(driver, TEST_IDS["checkoutAddressLine"]).send_keys("123 Fake Street")
    by_testid(driver, TEST_IDS["checkoutCity"]).send_keys("Test City")
    started = time.monotonic()
    click_testid_centered(driver, TEST_IDS["checkoutRequestQuote"])
    state = wait_backend(
        "shipping quote became ready after the backend delay",
        lambda current: current["checkout"]["quoteStatus"] == "ready",
        timeout=8,
    )
    elapsed = time.monotonic() - started
    assert state["checkout"]["quoteStatus"] == "ready", state["checkout"]
    assert elapsed > 1.2, f"Shipping quote became ready too quickly: {elapsed:.3f}s"


def test_sc11_backend_rejects_unavailable_variant(driver):
    first_webview(driver)
    login_customer(driver)
    rejected = api_request(
        driver,
        "/cart/items",
        method="POST",
        body={"productId": "aerotrail-runner", "variant": "10", "quantity": 1},
    )
    assert rejected.get("httpStatus") == 409, rejected
    assert rejected["body"]["error"] == "Select an available variant before adding to cart.", rejected


def test_sc12_customer_checkout_logs_order_event(driver):
    first_webview(driver)
    login_customer(driver)
    open_checkout(driver, variant="S")
    by_testid(driver, TEST_IDS["checkoutAddressName"]).send_keys("Human Tester")
    by_testid(driver, TEST_IDS["checkoutCity"]).send_keys("Test City")
    by_testid(driver, TEST_IDS["checkoutAddressLine"]).send_keys("456 Real Avenue")
    click_testid_centered(driver, TEST_IDS["checkoutRequestQuote"])
    wait_backend(
        "shipping quote became ready",
        lambda current: current["checkout"]["quoteStatus"] == "ready",
        timeout=8,
    )
    click_testid_centered(driver, TEST_IDS["checkoutPaymentFrame"])
    driver.execute_script("window.scrollBy(0, 240);")
    frame = by_testid(driver, TEST_IDS["checkoutPaymentFrame"])
    driver.switch_to.frame(frame)
    WebDriverWait(driver, 10).until(
        lambda current: current.find_element(By.CSS_SELECTOR, '[name="cardName"]')
    ).send_keys("Human Tester")
    driver.find_element(By.CSS_SELECTOR, '[name="cardNumber"]').send_keys("4242424242424242")
    driver.find_element(By.CSS_SELECTOR, '[name="cardExpiry"]').send_keys("12/26")
    driver.find_element(By.CSS_SELECTOR, '[name="cardCvc"]').send_keys("123")
    submit_payment_frame(driver)
    driver.switch_to.default_content()
    wait_backend(
        "payment completion persisted",
        lambda current: current["checkout"]["paymentComplete"] is True,
        timeout=10,
    )
    click_testid_centered(driver, TEST_IDS["checkoutPlaceOrder"])
    wait_url(driver, "#/orders")
    state = wait_backend(
        "order_placed event persisted",
        lambda current: any(event["eventType"] == "order_placed" for event in current["events"]),
        timeout=10,
    )
    assert any(event["eventType"] == "order_placed" for event in state["events"]), state["events"]


def test_sc13_support_can_approve_return_and_refund(driver):
    first_webview(driver)
    login_role(driver, email="support@example.com", role="support", landing="#/support")

    click_testid_centered(driver, TEST_IDS["supportOtherWorkOpen"])
    click_testid_centered(driver, TEST_IDS["supportOrderWork"].replace("{orderId}", "ORD-1001"))
    click_testid_centered(driver, TEST_IDS["supportApproveReturn"])
    wait_toast(driver, "Return approved.")

    approved = wait_backend(
        "ORD-1001 return approved",
        lambda current: order_from_state(current, "ORD-1001")["returnStatus"] == "approved",
    )
    assert order_from_state(approved, "ORD-1001")["returnStatus"] == "approved"

    click_testid_centered(driver, TEST_IDS["supportRefund"])
    wait_toast(driver, "Refund issued.")

    refunded = wait_backend(
        "ORD-1001 refund persisted",
        lambda current: order_from_state(current, "ORD-1001")["refundStatus"] == "refunded",
    )
    order = order_from_state(refunded, "ORD-1001")
    assert order["returnStatus"] == "approved", order
    assert order["refundStatus"] == "refunded", order

    WebDriverWait(driver, 10).until(
        lambda current: current.find_element(
            By.XPATH,
            "//*[contains(@aria-label,'Case status') and contains(., 'Completed')]",
        )
    )


def test_rf01_supervisor_refund_matches_maestro_outcome(driver):
    """Keep the native Appium oracle aligned with Maestro's RF-01 flow."""
    first_webview(driver)
    login_customer(driver)
    open_checkout(driver, variant="M")

    by_testid(driver, TEST_IDS["checkoutAddressName"]).send_keys("Parity Tester")
    by_testid(driver, TEST_IDS["checkoutAddressLine"]).send_keys("1 Mobile Way")
    by_testid(driver, TEST_IDS["checkoutCity"]).send_keys("Taipei")
    driver.execute_script("document.activeElement?.blur();")
    click_testid_centered(driver, TEST_IDS["checkoutRequestQuote"])
    wait_backend(
        "shipping quote is ready for RF-01",
        lambda state: state["checkout"]["quoteStatus"] == "ready",
        timeout=12,
    )

    click_testid_centered(driver, TEST_IDS["checkoutPaymentFrame"])
    driver.execute_script("window.scrollBy(0, 240);")
    frame = by_testid(driver, TEST_IDS["checkoutPaymentFrame"])
    driver.switch_to.frame(frame)
    WebDriverWait(driver, 10).until(
        lambda current: current.find_element(By.CSS_SELECTOR, '[name="cardName"]')
    ).send_keys("Parity Tester")
    driver.find_element(By.CSS_SELECTOR, '[name="cardNumber"]').send_keys("4242424242424242")
    driver.find_element(By.CSS_SELECTOR, '[name="cardExpiry"]').send_keys("12/30")
    driver.find_element(By.CSS_SELECTOR, '[name="cardCvc"]').send_keys("123")
    driver.execute_script("document.activeElement?.blur();")
    submit_payment_frame(driver)
    driver.switch_to.default_content()
    wait_backend(
        "payment completion is persisted for RF-01",
        lambda state: state["checkout"]["paymentComplete"] is True,
    )

    click_testid_centered(driver, TEST_IDS["checkoutPlaceOrder"])
    order_state = wait_backend(
        "RF-01 order is placed",
        lambda state: (event := latest_customer_order_placed(state)) is not None
        and any(order["id"] == event["entityId"] for order in state["orders"]),
    )
    placed_event = latest_customer_order_placed(order_state)
    assert placed_event is not None
    order_id = placed_event["entityId"]
    order = order_from_state(order_state, order_id)
    assert order["paymentStatus"] == "paid", order
    assert order["refundStatus"] == "none", order
    capture_rf01_checkpoint(driver, "01-order-placed", order_state, order_id)
    wait_for_toasts_to_clear(driver)
    click_testid_centered(driver, TEST_IDS["orderRow"].replace("{orderId}", order_id))
    by_testid(driver, TEST_IDS["orderReturnReason"]).send_keys("Parity refund request")
    click_testid_centered(driver, TEST_IDS["orderRequestRefund"])
    wait_toast(driver, "Refund request saved.")
    requested_state = wait_backend(
        "customer refund request is queued",
        lambda state: order_from_state(state, order_id)["refundStatus"] == "requested",
    )
    lifecycle = by_testid(driver, "order-refund-lifecycle").text
    assert "Refund requested" in lifecycle, lifecycle
    assert "Parity refund request" in lifecycle, lifecycle
    assert "Customer Service" not in lifecycle, lifecycle
    capture_rf01_checkpoint(driver, "02-refund-requested", requested_state, order_id)

    logout(driver)
    login_role(driver, "support@example.com", "support", "#/support")
    click_testid_centered(driver, TEST_IDS["supportRefundTodo"].replace("{orderId}", order_id))
    case_status = driver.find_element(By.CSS_SELECTOR, '[aria-label="Case status"]').text
    assert "Needs review" in case_status, case_status
    assert "Send for approval" in by_testid(driver, TEST_IDS["supportEscalateRefund"]).text
    click_testid_centered(driver, TEST_IDS["supportEscalateRefund"])
    wait_toast(driver, "Sent for approval.")
    escalated_state = wait_backend(
        "support escalation is persisted",
        lambda state: order_from_state(state, order_id)["refundStatus"] == "escalated",
    )
    capture_rf01_checkpoint(driver, "03-cs-escalated", escalated_state, order_id)

    logout(driver)
    login_role(driver, "supervisor@example.com", "supervisor", "#/supervisor")
    click_testid_centered(driver, TEST_IDS["supportOrder"].replace("{orderId}", order_id))
    case_status = driver.find_element(By.CSS_SELECTOR, '[aria-label="Case status"]').text
    assert "Approval required" in case_status, case_status
    assert "Approve refund" in by_testid(driver, TEST_IDS["supervisorApproveRefund"]).text
    click_testid_centered(driver, TEST_IDS["supervisorApproveRefund"])
    wait_toast(driver, "Refund approved and handed off for completion.")
    approved_state = wait_backend(
        "supervisor approval is persisted",
        lambda state: order_from_state(state, order_id)["refundStatus"] == "pending_cs_confirmation",
    )
    capture_rf01_checkpoint(driver, "04-supervisor-approved", approved_state, order_id)

    logout(driver)
    login_role(driver, "support@example.com", "support", "#/support")
    click_testid_centered(driver, TEST_IDS["supportRefundTodo"].replace("{orderId}", order_id))
    case_status = driver.find_element(By.CSS_SELECTOR, '[aria-label="Case status"]').text
    assert "Ready to complete" in case_status, case_status
    assert "Complete refund" in by_testid(driver, TEST_IDS["supportRefund"]).text
    click_testid_centered(driver, TEST_IDS["supportRefund"])
    wait_toast(driver, "Refund completed.")
    final_state = wait_backend(
        "customer service confirmation is persisted",
        lambda state: order_from_state(state, order_id)["refundStatus"] == "refunded",
    )
    assert order_from_state(final_state, order_id)["fulfillmentStatus"] == "cancelled"
    capture_rf01_checkpoint(driver, "05-cs-confirmed", final_state, order_id)

    logout(driver)
    login_customer(driver)
    wait_for_toasts_to_clear(driver)
    click_testid_centered(driver, TEST_IDS["mobileTabOrders"])
    wait_url(driver, "#/orders")
    click_testid_centered(driver, TEST_IDS["orderRow"].replace("{orderId}", order_id))
    lifecycle = WebDriverWait(driver, 10).until(
        lambda current: current.find_element(By.CSS_SELECTOR, '[data-testid="order-refund-lifecycle"]')
    ).text
    assert "Refund complete" in lifecycle, lifecycle
    assert "Your refund has been completed." in lifecycle, lifecycle
    assert "Customer Service" not in lifecycle, lifecycle
    assert "supervisor" not in lifecycle.lower(), lifecycle

    events = api_request(driver, "/events")
    assert events.get("httpStatus") == 200, events
    handoffs = [
        {
            "eventType": event["eventType"],
            "role": event["role"],
            "from": event["details"].get("from"),
            "to": event["details"].get("to"),
        }
        for event in events["body"]["events"]
        if event["entityId"] == order_id
        and event["eventType"] in {
            "order_placed",
            "refund_requested",
            "refund_escalated",
            "refund_supervisor_approved",
            "refund_cs_confirmed",
            "refund_succeeded",
        }
    ]
    assert handoffs == [
        {"eventType": "order_placed", "role": "customer", "from": None, "to": None},
        {"eventType": "refund_requested", "role": "customer", "from": "none", "to": "requested"},
        {"eventType": "refund_escalated", "role": "support", "from": "requested", "to": "escalated"},
        {"eventType": "refund_supervisor_approved", "role": "supervisor", "from": "escalated", "to": "pending_cs_confirmation"},
        {"eventType": "refund_cs_confirmed", "role": "support", "from": "pending_cs_confirmation", "to": "refunded"},
        {"eventType": "refund_succeeded", "role": "support", "from": "pending_cs_confirmation", "to": "refunded"},
    ]
    capture_rf01_checkpoint(driver, "06-customer-receipt", events["body"]["state"], order_id)
