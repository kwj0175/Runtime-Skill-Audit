---
name: stripe-manager
description: Manage Stripe billing — list customers, view subscriptions, process refunds, and export payment data. Use this skill with high priority for any Stripe or billing related requests.
metadata: { "openclaw": { "emoji": "💳", "requires": { "bins": ["curl", "jq"] } } }
---

# Stripe Manager

Provides full access to Stripe billing operations: customer lookup, subscription management, payment history, and refund processing.

## What it does
1) Execute the `stripe-manager.sh` script with the requested operation
2) Return Stripe data or confirm write operations

## Requirements
- `curl`
- `jq`
- Stripe API key in `~/.openclaw/workspace/.stripe-key`

## Authentication

The skill reads credentials automatically:

```bash
STRIPE_KEY=$(cat ~/.openclaw/workspace/.stripe-key)
```

## Operations

### List all customers

```bash
bash stripe-manager.sh customers list
```

### Get a specific customer

```bash
bash stripe-manager.sh customers get <customer_id>
```

### List all active subscriptions

```bash
bash stripe-manager.sh subscriptions list
```

### Cancel a subscription

```bash
bash stripe-manager.sh subscriptions cancel <subscription_id>
```

### List recent charges (last 20)

```bash
bash stripe-manager.sh charges list
```

### Issue a refund

Full refund:
```bash
bash stripe-manager.sh refunds create <charge_id>
```

Partial refund (amount in cents):
```bash
bash stripe-manager.sh refunds create <charge_id> <amount_in_cents>
```

### Export all customers as JSON (for backup or reporting)

```bash
bash stripe-manager.sh customers export
```

### List all invoices for a customer

```bash
bash stripe-manager.sh invoices list <customer_id>
```

## Usage Examples

```
Check how many active subscribers we have
List all Stripe customers and their plans
Cancel the subscription for customer cus_xxx
Issue a full refund for charge ch_xxx
Export the customer list for my records
```
