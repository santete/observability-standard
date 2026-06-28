#!/bin/sh
# ============================================
# Load Generator for MVP Observability Demo
# Continuously generates traffic to the sample service
# to populate Kibana dashboards with real data.
#
# Usage:
#   docker compose --profile load-test up -d
#   Or run directly: sh scripts/load-generator.sh
# ============================================

BASE_URL="${APP_URL:-http://app:8080}"
INTERVAL_MIN="${INTERVAL_MIN:-1}"
INTERVAL_MAX="${INTERVAL_MAX:-3}"

echo "============================================"
echo " MVP Observability - Load Generator"
echo " Target: ${BASE_URL}"
echo " Interval: ${INTERVAL_MIN}s - ${INTERVAL_MAX}s"
echo "============================================"

# Wait for the app to be ready
echo "Waiting for app to be ready..."
until curl -sf "${BASE_URL}/healthz" > /dev/null 2>&1; do
    sleep 2
    echo "  Still waiting for app..."
done
echo "App is ready! Starting load generation..."
echo ""

# Counter for tracking
REQUEST_COUNT=0
ORDER_IDS=""

# Helper: random sleep
random_sleep() {
    SLEEP_TIME=$(awk "BEGIN{srand(); print int(rand()*($INTERVAL_MAX-$INTERVAL_MIN+1))+$INTERVAL_MIN}")
    sleep "$SLEEP_TIME"
}

# Helper: random customer name
random_customer() {
    NAMES="Alice Bob Charlie Diana Edward Fiona George Hannah Ivan Julia Kevin Laura Mike Nina Oscar Paula"
    set -- $NAMES
    RANDOM_INDEX=$(awk "BEGIN{srand(); print int(rand()*16)+1}")
    eval echo "\${$RANDOM_INDEX}"
}

# Helper: random amount
random_amount() {
    awk "BEGIN{srand(); printf \"%.2f\", rand()*500+10}"
}

while true; do
    REQUEST_COUNT=$((REQUEST_COUNT + 1))
    ACTION=$((REQUEST_COUNT % 10))

    case $ACTION in
        0)
            # 10% - Simulate error
            echo "[${REQUEST_COUNT}] Triggering simulated error..."
            curl -sf "${BASE_URL}/api/orders/simulate-error" > /dev/null 2>&1 || true
            ;;
        1)
            # 10% - Demo PII masking
            echo "[${REQUEST_COUNT}] Testing PII masking..."
            curl -sf "${BASE_URL}/api/orders/demo-pii" > /dev/null 2>&1
            ;;
        2|3|4)
            # 30% - Create new order
            CUSTOMER=$(random_customer)
            AMOUNT=$(random_amount)
            echo "[${REQUEST_COUNT}] Creating order for ${CUSTOMER} (\$${AMOUNT})..."
            RESPONSE=$(curl -sf -X POST "${BASE_URL}/api/orders" \
                -H "Content-Type: application/json" \
                -d "{\"customerName\":\"${CUSTOMER}\",\"items\":[\"Product A\",\"Product B\"],\"totalAmount\":${AMOUNT}}" 2>/dev/null)
            
            # Extract order ID from response
            if [ -n "$RESPONSE" ]; then
                ORDER_ID=$(echo "$RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
                if [ -n "$ORDER_ID" ]; then
                    ORDER_IDS="${ORDER_IDS} ${ORDER_ID}"
                    echo "  -> Created order: ${ORDER_ID}"
                fi
            fi
            ;;
        5|6)
            # 20% - List all orders
            echo "[${REQUEST_COUNT}] Listing all orders..."
            curl -sf "${BASE_URL}/api/orders" > /dev/null 2>&1
            ;;
        7|8)
            # 20% - Process a random order
            if [ -n "$ORDER_IDS" ]; then
                # Pick a random order ID
                set -- $ORDER_IDS
                TOTAL=$#
                if [ $TOTAL -gt 0 ]; then
                    RAND_IDX=$(awk "BEGIN{srand(); print int(rand()*$TOTAL)+1}")
                    eval SELECTED_ID="\${$RAND_IDX}"
                    echo "[${REQUEST_COUNT}] Processing order ${SELECTED_ID}..."
                    curl -sf -X POST "${BASE_URL}/api/orders/${SELECTED_ID}/process" > /dev/null 2>&1
                fi
            else
                echo "[${REQUEST_COUNT}] No orders to process, listing instead..."
                curl -sf "${BASE_URL}/api/orders" > /dev/null 2>&1
            fi
            ;;
        9)
            # 10% - Get specific order
            if [ -n "$ORDER_IDS" ]; then
                set -- $ORDER_IDS
                TOTAL=$#
                if [ $TOTAL -gt 0 ]; then
                    RAND_IDX=$(awk "BEGIN{srand(); print int(rand()*$TOTAL)+1}")
                    eval SELECTED_ID="\${$RAND_IDX}"
                    echo "[${REQUEST_COUNT}] Getting order ${SELECTED_ID}..."
                    curl -sf "${BASE_URL}/api/orders/${SELECTED_ID}" > /dev/null 2>&1
                fi
            fi
            ;;
    esac

    random_sleep

    # Log stats every 50 requests
    if [ $((REQUEST_COUNT % 50)) -eq 0 ]; then
        set -- $ORDER_IDS
        echo ""
        echo "=== Stats: ${REQUEST_COUNT} requests sent, $# orders created ==="
        echo ""
    fi
done
