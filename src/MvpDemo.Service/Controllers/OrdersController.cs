using Microsoft.AspNetCore.Mvc;
using MvpDemo.Service.Models;
using MvpDemo.Service.Services;

namespace MvpDemo.Service.Controllers;

/// <summary>
/// REST API controller for Order management.
/// All endpoints are automatically instrumented by OpenTelemetry ASP.NET Core instrumentation.
/// </summary>
[ApiController]
[Route("api/[controller]")]
public class OrdersController : ControllerBase
{
    private readonly OrderService _orderService;
    private readonly ILogger<OrdersController> _logger;

    public OrdersController(OrderService orderService, ILogger<OrdersController> logger)
    {
        _orderService = orderService;
        _logger = logger;
    }

    /// <summary>
    /// GET /api/orders - List all orders
    /// </summary>
    [HttpGet]
    public async Task<ActionResult<IReadOnlyList<Order>>> GetAll()
    {
        var orders = await _orderService.GetAllOrdersAsync();
        return Ok(orders);
    }

    /// <summary>
    /// GET /api/orders/{id} - Get order by ID
    /// </summary>
    [HttpGet("{id}")]
    public async Task<ActionResult<Order>> GetById(string id)
    {
        var order = await _orderService.GetOrderAsync(id);
        if (order == null)
            return NotFound(new { message = $"Order {id} not found", orderId = id });

        return Ok(order);
    }

    /// <summary>
    /// POST /api/orders - Create a new order
    /// </summary>
    [HttpPost]
    public async Task<ActionResult<Order>> Create([FromBody] CreateOrderRequest request)
    {
        if (string.IsNullOrWhiteSpace(request.CustomerName))
            return BadRequest(new { message = "CustomerName is required" });

        if (request.Items == null || request.Items.Count == 0)
            return BadRequest(new { message = "At least one item is required" });

        if (request.TotalAmount <= 0)
            return BadRequest(new { message = "TotalAmount must be greater than 0" });

        var order = await _orderService.CreateOrderAsync(request);
        return CreatedAtAction(nameof(GetById), new { id = order.Id }, order);
    }

    /// <summary>
    /// PUT /api/orders/{id}/status - Update order status
    /// </summary>
    [HttpPut("{id}/status")]
    public async Task<ActionResult<Order>> UpdateStatus(string id, [FromBody] UpdateOrderStatusRequest request)
    {
        var order = await _orderService.UpdateOrderStatusAsync(id, request);
        if (order == null)
            return NotFound(new { message = $"Order {id} not found", orderId = id });

        return Ok(order);
    }

    /// <summary>
    /// POST /api/orders/{id}/process - Trigger order processing
    /// </summary>
    [HttpPost("{id}/process")]
    public async Task<ActionResult<Order>> Process(string id)
    {
        var order = await _orderService.ProcessOrderAsync(id);
        if (order == null)
            return NotFound(new { message = $"Order {id} not found", orderId = id });

        return Ok(order);
    }

    /// <summary>
    /// GET /api/orders/simulate-error - Deliberately trigger an error for testing
    /// </summary>
    [HttpGet("simulate-error")]
    public async Task<ActionResult> SimulateError()
    {
        await _orderService.SimulateErrorAsync();
        return Ok(); // Never reached
    }

    /// <summary>
    /// GET /api/orders/demo-pii - Demonstrate PII masking in logs
    /// </summary>
    [HttpGet("demo-pii")]
    public ActionResult DemoPiiMasking()
    {
        // SPEC 2.4: These sensitive values will be automatically masked by PiiMaskingEnricher
        _logger.LogInformation(
            "PII masking demo. Password: {Password}, CreditCard: {CreditCardNumber}, Token: {AccessToken}, Pin: {Pin}",
            "SuperSecret123", "4532015112830366", "eyJhbGciOiJIUzI1NiJ9.test", "1234");

        return Ok(new
        {
            message = "PII masking demo executed. Check logs in Kibana — sensitive values should be masked.",
            hint = "Search for 'PII masking demo' in Kibana Discover view"
        });
    }
}
