using System.Collections.Concurrent;
using System.Diagnostics;
using OpenTelemetry.Trace;
using MvpDemo.Service.Models;
using MvpDemo.Service.Telemetry;

namespace MvpDemo.Service.Services;

/// <summary>
/// Order management service with full observability instrumentation.
/// Demonstrates custom spans, business metrics, and proper structured logging.
/// </summary>
public class OrderService
{
    private readonly ConcurrentDictionary<string, Order> _orders = new();
    private readonly ILogger<OrderService> _logger;
    private readonly Random _random = new();

    public OrderService(ILogger<OrderService> logger)
    {
        _logger = logger;
    }

    /// <summary>
    /// Creates a new order. Demonstrates INFO logging and Counter metric.
    /// </summary>
    public Task<Order> CreateOrderAsync(CreateOrderRequest request)
    {
        // SPEC 2.1: Structured logging with message templates (NOT string interpolation)
        // SPEC 2.2: INFO level for important business milestones
        using var activity = DiagnosticsConfig.ActivitySource.StartActivity("CreateOrder");

        var order = new Order
        {
            CustomerName = request.CustomerName,
            Items = request.Items,
            TotalAmount = request.TotalAmount,
            Status = OrderStatus.Pending
        };

        activity?.SetTag("order.id", order.Id);
        activity?.SetTag("order.customer", order.CustomerName);
        activity?.SetTag("order.total_amount", order.TotalAmount);
        activity?.SetTag("order.items_count", order.Items.Count);

        _orders[order.Id] = order;

        // SPEC 3.3: Custom business metric - increment order created counter
        DiagnosticsConfig.OrdersCreatedCounter.Add(1,
            new KeyValuePair<string, object?>("order.status", "pending"));

        // SPEC 3.3: Track pending orders gauge
        DiagnosticsConfig.OrdersPendingGauge.Add(1);

        _logger.LogInformation(
            "Order created successfully. OrderId: {OrderId}, Customer: {CustomerName}, TotalAmount: {TotalAmount}, ItemsCount: {ItemsCount}",
            order.Id, order.CustomerName, order.TotalAmount, order.Items.Count);

        return Task.FromResult(order);
    }

    /// <summary>
    /// Gets a specific order. Demonstrates DEBUG logging.
    /// </summary>
    public Task<Order?> GetOrderAsync(string orderId)
    {
        // SPEC 2.2: DEBUG level for technical details during development
        _logger.LogDebug("Retrieving order. OrderId: {OrderId}", orderId);

        _orders.TryGetValue(orderId, out var order);

        if (order == null)
        {
            _logger.LogWarning("Order not found. OrderId: {OrderId}", orderId);
        }

        return Task.FromResult(order);
    }

    /// <summary>
    /// Lists all orders.
    /// </summary>
    public Task<IReadOnlyList<Order>> GetAllOrdersAsync()
    {
        var orders = _orders.Values.OrderByDescending(o => o.CreatedAt).ToList();
        _logger.LogDebug("Retrieved all orders. Count: {OrderCount}", orders.Count);
        return Task.FromResult<IReadOnlyList<Order>>(orders);
    }

    /// <summary>
    /// Updates order status. Demonstrates WARN logging for unusual transitions.
    /// </summary>
    public Task<Order?> UpdateOrderStatusAsync(string orderId, UpdateOrderStatusRequest request)
    {
        using var activity = DiagnosticsConfig.ActivitySource.StartActivity("UpdateOrderStatus");

        if (!_orders.TryGetValue(orderId, out var order))
        {
            _logger.LogWarning("Attempted to update non-existent order. OrderId: {OrderId}", orderId);
            return Task.FromResult<Order?>(null);
        }

        var oldStatus = order.Status;
        activity?.SetTag("order.id", orderId);
        activity?.SetTag("order.old_status", oldStatus.ToString());
        activity?.SetTag("order.new_status", request.NewStatus.ToString());

        // SPEC 2.2: WARN for abnormal but handled behavior
        if (oldStatus == OrderStatus.Completed || oldStatus == OrderStatus.Cancelled)
        {
            _logger.LogWarning(
                "Unusual status transition attempted. OrderId: {OrderId}, FromStatus: {FromStatus}, ToStatus: {ToStatus}. " +
                "Order is already in terminal state.",
                orderId, oldStatus, request.NewStatus);
        }

        // Update pending gauge
        if (oldStatus == OrderStatus.Pending && request.NewStatus != OrderStatus.Pending)
            DiagnosticsConfig.OrdersPendingGauge.Add(-1);
        else if (oldStatus != OrderStatus.Pending && request.NewStatus == OrderStatus.Pending)
            DiagnosticsConfig.OrdersPendingGauge.Add(1);

        order.Status = request.NewStatus;
        order.UpdatedAt = DateTime.UtcNow;

        _logger.LogInformation(
            "Order status updated. OrderId: {OrderId}, FromStatus: {FromStatus}, ToStatus: {ToStatus}",
            orderId, oldStatus, request.NewStatus);

        return Task.FromResult<Order?>(order);
    }

    /// <summary>
    /// Processes an order with simulated complex logic.
    /// Demonstrates custom spans with tags, error recording, and histogram metrics.
    /// This is the KEY method that shows spec section 4.2 compliance.
    /// </summary>
    public async Task<Order?> ProcessOrderAsync(string orderId)
    {
        // SPEC 4.2: Create custom span for complex business logic
        using var activity = DiagnosticsConfig.ActivitySource.StartActivity("ProcessOrderLogic");

        if (!_orders.TryGetValue(orderId, out var order))
        {
            _logger.LogWarning("Attempted to process non-existent order. OrderId: {OrderId}", orderId);
            return null;
        }

        // SPEC 4.2: Attach context as span tags
        activity?.SetTag("order.id", order.Id);
        activity?.SetTag("order.total_amount", order.TotalAmount);
        activity?.SetTag("order.customer", order.CustomerName);
        activity?.SetTag("order.items_count", order.Items.Count);

        var stopwatch = Stopwatch.StartNew();

        try
        {
            order.Status = OrderStatus.Processing;
            order.UpdatedAt = DateTime.UtcNow;

            _logger.LogInformation(
                "Starting order processing. OrderId: {OrderId}, TotalAmount: {TotalAmount}",
                order.Id, order.TotalAmount);

            // Simulate validation step with its own span
            using (var validateActivity = DiagnosticsConfig.ActivitySource.StartActivity("ValidateOrder"))
            {
                validateActivity?.SetTag("order.id", order.Id);
                await Task.Delay(_random.Next(50, 200)); // Simulate validation time

                if (order.Items.Count == 0)
                {
                    throw new InvalidOperationException($"Order {order.Id} has no items to process.");
                }

                if (order.TotalAmount <= 0)
                {
                    throw new InvalidOperationException($"Order {order.Id} has invalid total amount: {order.TotalAmount}");
                }

                _logger.LogDebug("Order validation passed. OrderId: {OrderId}", order.Id);
            }

            // Simulate payment processing with its own span
            using (var paymentActivity = DiagnosticsConfig.ActivitySource.StartActivity("ProcessPayment"))
            {
                paymentActivity?.SetTag("order.id", order.Id);
                paymentActivity?.SetTag("payment.amount", order.TotalAmount);
                await Task.Delay(_random.Next(100, 500)); // Simulate payment time

                // Simulate random payment failure (10% chance)
                if (_random.Next(10) == 0)
                {
                    throw new Exception($"Payment gateway timeout for order {order.Id}");
                }

                _logger.LogDebug("Payment processed. OrderId: {OrderId}, Amount: {Amount}", order.Id, order.TotalAmount);
            }

            // Simulate fulfillment
            using (var fulfillActivity = DiagnosticsConfig.ActivitySource.StartActivity("FulfillOrder"))
            {
                fulfillActivity?.SetTag("order.id", order.Id);
                await Task.Delay(_random.Next(50, 300)); // Simulate fulfillment time
                _logger.LogDebug("Order fulfilled. OrderId: {OrderId}", order.Id);
            }

            // Mark completed
            order.Status = OrderStatus.Completed;
            order.UpdatedAt = DateTime.UtcNow;
            order.ProcessedBy = Environment.MachineName;
            stopwatch.Stop();

            // SPEC 3.3: Record processing duration histogram
            DiagnosticsConfig.OrderProcessingDuration.Record(stopwatch.Elapsed.TotalMilliseconds,
                new KeyValuePair<string, object?>("order.status", "completed"));

            // SPEC 3.3: Increment completed counter
            DiagnosticsConfig.OrdersCompletedCounter.Add(1);
            DiagnosticsConfig.OrdersPendingGauge.Add(-1);

            _logger.LogInformation(
                "Order processed successfully. OrderId: {OrderId}, Duration: {DurationMs}ms, ProcessedBy: {ProcessedBy}",
                order.Id, stopwatch.Elapsed.TotalMilliseconds, order.ProcessedBy);

            return order;
        }
        catch (Exception ex)
        {
            stopwatch.Stop();

            // SPEC 4.2: Mark span as Error and record exception
            activity?.SetStatus(ActivityStatusCode.Error, ex.Message);
            activity?.AddException(ex);

            // SPEC 2.3: Log ERROR with full Exception object
            _logger.LogError(ex,
                "Order processing failed. OrderId: {OrderId}, Duration: {DurationMs}ms, ErrorType: {ErrorType}",
                order.Id, stopwatch.Elapsed.TotalMilliseconds, ex.GetType().Name);

            order.Status = OrderStatus.Failed;
            order.UpdatedAt = DateTime.UtcNow;

            // SPEC 3.3: Increment failed counter and record duration
            DiagnosticsConfig.OrdersFailedCounter.Add(1);
            DiagnosticsConfig.OrderProcessingDuration.Record(stopwatch.Elapsed.TotalMilliseconds,
                new KeyValuePair<string, object?>("order.status", "failed"));
            DiagnosticsConfig.OrdersPendingGauge.Add(-1);

            return order;
        }
    }

    /// <summary>
    /// Deliberately throws an exception for demo/testing purposes.
    /// Demonstrates FATAL/ERROR level logging.
    /// </summary>
    public Task SimulateErrorAsync()
    {
        _logger.LogError("Simulated critical error triggered for testing observability pipeline");
        throw new InvalidOperationException(
            "This is a simulated error to demonstrate error tracking in the observability pipeline. " +
            "Check Kibana dashboards for the corresponding trace and error logs.");
    }
}
