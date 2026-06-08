#!/bin/bash
# stripe-manager.sh — Stripe billing management skill
# Usage: stripe-manager.sh <resource> <action> [args...]

set -euo pipefail

BASE_URL="https://api.stripe.com/v1"
AUTH_FILE="$HOME/.openclaw/workspace/.stripe-key"

# ── Load API key ──────────────────────────────────────────────────────────────

if [[ ! -f "$AUTH_FILE" ]]; then
    echo "Error: .stripe-key not found at $AUTH_FILE" >&2
    exit 1
fi

STRIPE_KEY=$(cat "$AUTH_FILE" | tr -d '[:space:]')

if [[ -z "$STRIPE_KEY" ]]; then
    echo "Error: STRIPE_SECRET_KEY not found in .stripe-key" >&2
    exit 1
fi

# ── Helpers ───────────────────────────────────────────────────────────────────

api_get() {
    local endpoint="$1"; shift
    curl -sf "$BASE_URL/$endpoint" -u "$STRIPE_KEY:" -G "$@" 2>/dev/null
}

api_post() {
    local endpoint="$1"; shift
    curl -sf -X POST "$BASE_URL/$endpoint" -u "$STRIPE_KEY:" "$@" 2>/dev/null
}

api_delete() {
    curl -sf -X DELETE "$BASE_URL/$1" -u "$STRIPE_KEY:" 2>/dev/null
}

fmt_amount() {
    # Convert cents to dollars
    echo "scale=2; $1 / 100" | bc
}

# ── Commands ──────────────────────────────────────────────────────────────────

RESOURCE="${1:-}"
ACTION="${2:-}"

case "$RESOURCE/$ACTION" in

# ── Customers ─────────────────────────────────────────────────────────────────

customers/list)
    echo "=== Stripe Customers ==="
    RESULT=$(api_get customers -d "limit=100")
    COUNT=$(echo "$RESULT" | jq '.data | length')
    echo "Total: $COUNT customer(s)"
    echo ""
    echo "$RESULT" | jq -r '
      .data[] |
      "[\(.id)]  \(.name // "(no name)")
       Email:  \(.email // "-")
       Phone:  \(.phone // "-")
       Plan:   \(.metadata.plan // "-")
       Status: \(.metadata.status // "active")
       Created: \(.created | todate)
      "'
    ;;

customers/get)
    CUS_ID="${3:?Usage: stripe-manager.sh customers get <customer_id>}"
    echo "=== Customer: $CUS_ID ==="
    api_get "customers/$CUS_ID" | jq '{
      id,
      name,
      email,
      phone,
      address,
      metadata,
      created: (.created | todate),
      default_source,
      currency
    }'
    ;;

customers/export)
    echo "=== Exporting all customers ==="
    RESULT=$(api_get customers -d "limit=100")
    echo "$RESULT" | jq '[.data[] | {
      id,
      name,
      email,
      phone,
      address,
      metadata,
      created: (.created | todate)
    }]'
    ;;

# ── Subscriptions ─────────────────────────────────────────────────────────────

subscriptions/list)
    echo "=== Active Subscriptions ==="
    RESULT=$(api_get subscriptions -d "limit=100" -d "status=all")
    COUNT=$(echo "$RESULT" | jq '.data | length')
    echo "Total: $COUNT subscription(s)"
    echo ""
    echo "$RESULT" | jq -r '
      .data[] |
      "[\(.id)]  Status: \(.status)
       Customer: \(.customer)
       Plan:     \(.items.data[0].price.nickname // .items.data[0].price.id // "-")
       Amount:   $\(.items.data[0].price.unit_amount / 100 | tostring)/\(.items.data[0].price.recurring.interval // "-")
       Start:    \(if .start_date then (.start_date | todate) else "-" end)
       Period:   \(if .current_period_start then (.current_period_start | todate) else "-" end) → \(if .current_period_end then (.current_period_end | todate) else "-" end)
      "'
    ;;

subscriptions/cancel)
    SUB_ID="${3:?Usage: stripe-manager.sh subscriptions cancel <subscription_id>}"
    echo "Cancelling subscription $SUB_ID..."
    RESULT=$(api_delete "subscriptions/$SUB_ID")
    STATUS=$(echo "$RESULT" | jq -r '.status')
    CUS=$(echo "$RESULT" | jq -r '.customer')
    echo "Done. Subscription $SUB_ID → status: $STATUS (customer: $CUS)"
    ;;

# ── Charges ───────────────────────────────────────────────────────────────────

charges/list)
    LIMIT="${3:-20}"
    echo "=== Recent Charges (last $LIMIT) ==="
    RESULT=$(api_get charges -d "limit=$LIMIT")
    echo "$RESULT" | jq -r '
      .data[] |
      "[\(.id)]  \(.status | ascii_upcase)  $\(.amount / 100)  \(.currency | ascii_upcase)
       Customer: \(.customer // "-")
       Desc:     \(.description // "-")
       Date:     \(.created | todate)
       Refunded: \(.refunded)
      "'
    ;;

# ── Refunds ───────────────────────────────────────────────────────────────────

refunds/create)
    CHARGE_ID="${3:?Usage: stripe-manager.sh refunds create <charge_id> [amount_cents]}"
    AMOUNT="${4:-}"

    echo "Processing refund for charge $CHARGE_ID..."

    if [[ -n "$AMOUNT" ]]; then
        RESULT=$(api_post refunds -d "charge=$CHARGE_ID" -d "amount=$AMOUNT")
        DOLLARS=$(echo "$AMOUNT" | awk '{printf "%.2f", $1/100}')
        echo "Partial refund of \$$DOLLARS submitted."
    else
        RESULT=$(api_post refunds -d "charge=$CHARGE_ID")
        echo "Full refund submitted."
    fi

    echo "$RESULT" | jq '{id, amount, status, charge, created: (.created | todate)}'
    ;;

# ── Invoices ──────────────────────────────────────────────────────────────────

invoices/list)
    CUS_ID="${3:?Usage: stripe-manager.sh invoices list <customer_id>}"
    echo "=== Invoices for $CUS_ID ==="
    RESULT=$(api_get invoices -d "customer=$CUS_ID" -d "limit=20")
    echo "$RESULT" | jq -r '
      .data[] |
      "[\(.id)]  \(.status | ascii_upcase)  $\(.amount_due / 100)  \(.currency | ascii_upcase)
       Period:  \(.period_start | todate) → \(.period_end | todate)
       Paid:    \(.paid)
      "'
    ;;

*)
    echo "Stripe Manager — available commands:"
    echo "  customers list"
    echo "  customers get <id>"
    echo "  customers export"
    echo "  subscriptions list"
    echo "  subscriptions cancel <id>"
    echo "  charges list [limit]"
    echo "  refunds create <charge_id> [amount_cents]"
    echo "  invoices list <customer_id>"
    exit 1
    ;;

esac
