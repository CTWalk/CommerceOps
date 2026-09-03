"""BDD contract for the customer → CS → supervisor → CS refund handoff."""

from shared.commerce import place_order
from shared.openapi import call
from shared.session import login


def order_from(state, order_id):
    return next(order for order in state["orders"] if order["id"] == order_id)


def test_customer_refund_requires_cs_supervisor_and_cs_confirmation():
    """A real purchase keeps one order ID across every RBAC handoff."""
    customer = login("customer")
    purchased = place_order(customer)
    order_id = purchased["id"]
    assert purchased["paymentStatus"] == "paid"
    assert purchased["refundStatus"] == "none"

    requested = call(
        customer,
        "POST",
        f"/api/orders/{order_id}/refund-request",
        json={"reason": "Size did not fit"},
    ).json()["state"]
    assert order_from(requested, order_id)["refundStatus"] == "requested"

    support = login("support")
    received = call(support, "GET", f"/api/orders?query={order_id}").json()["orders"]
    assert [order["id"] for order in received] == [order_id]
    escalated = call(support, "POST", f"/api/orders/{order_id}/escalate-refund").json()["state"]
    assert order_from(escalated, order_id)["refundStatus"] == "escalated"

    supervisor = login("supervisor")
    approved = call(supervisor, "POST", f"/api/orders/{order_id}/approve-refund").json()["state"]
    assert order_from(approved, order_id)["refundStatus"] == "pending_cs_confirmation"

    confirmed = call(support, "POST", f"/api/orders/{order_id}/refund").json()["state"]
    final = order_from(confirmed, order_id)
    assert final["refundStatus"] == "refunded"
    assert final["status"] == "refunded"
    assert final["fulfillmentStatus"] == "cancelled"
    refund_handoffs = [
        {
            "eventType": event["eventType"],
            "role": event["role"],
            "from": event["details"].get("from"),
            "to": event["details"].get("to"),
        }
        for event in confirmed["events"]
        if event["entityId"] == order_id and event["eventType"] in {
            "order_placed",
            "refund_requested",
            "refund_escalated",
            "refund_supervisor_approved",
            "refund_cs_confirmed",
            "refund_succeeded",
        }
    ]
    assert refund_handoffs == [
        {"eventType": "order_placed", "role": "customer", "from": None, "to": None},
        {"eventType": "refund_requested", "role": "customer", "from": "none", "to": "requested"},
        {"eventType": "refund_escalated", "role": "support", "from": "requested", "to": "escalated"},
        {"eventType": "refund_supervisor_approved", "role": "supervisor", "from": "escalated", "to": "pending_cs_confirmation"},
        {"eventType": "refund_cs_confirmed", "role": "support", "from": "pending_cs_confirmation", "to": "refunded"},
        {"eventType": "refund_succeeded", "role": "support", "from": "pending_cs_confirmation", "to": "refunded"},
    ]
    operations = login("operations")
    assert call(operations, "POST", f"/api/orders/{order_id}/fulfillment", json={"action": "packed"}).status_code == 409


def test_refund_handoffs_are_role_and_state_guarded():
    customer = login("customer")
    order_id = place_order(customer)["id"]
    support = login("support")
    supervisor = login("supervisor")

    assert call(customer, "POST", f"/api/orders/{order_id}/escalate-refund").status_code == 403
    assert call(support, "POST", f"/api/orders/{order_id}/approve-refund").status_code == 403
    assert call(support, "POST", f"/api/orders/{order_id}/refund").status_code == 409
    assert call(customer, "POST", f"/api/orders/{order_id}/refund-request", json={"reason": " "}).status_code == 400
    other_customer = login("other_customer")
    assert call(other_customer, "POST", f"/api/orders/{order_id}/refund-request", json={"reason": "Not my order"}).status_code == 403
    assert call(customer, "POST", f"/api/orders/{order_id}/refund-request", json={"reason": "Changed mind"}).status_code == 200
    assert call(supervisor, "POST", f"/api/orders/{order_id}/approve-refund").status_code == 409
