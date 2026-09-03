# Refund workflow

```text
Customer places paid order
        ↓
Customer requests refund
        ↓
Support reviews and escalates
        ↓
Supervisor approves
        ↓
Support completes refund
        ↓
Customer sees final receipt
```

The accepted transition sequence is also represented as persisted domain events:

```text
order_placed
refund_requested
refund_escalated
refund_supervisor_approved
refund_cs_confirmed
refund_succeeded
```

Each transition has an actor and from/to state. UI language is asserted where customer or staff communication is itself the product property; persisted state/events remain the business oracle.
