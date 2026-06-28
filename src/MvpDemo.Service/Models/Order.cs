namespace MvpDemo.Service.Models;

/// <summary>
/// Order domain model for the MVP Demo service.
/// </summary>
public class Order
{
    public string Id { get; set; } = Guid.NewGuid().ToString("N")[..8].ToUpper();
    public string CustomerName { get; set; } = string.Empty;
    public List<string> Items { get; set; } = new();
    public decimal TotalAmount { get; set; }
    public OrderStatus Status { get; set; } = OrderStatus.Pending;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime? UpdatedAt { get; set; }
    public string? ProcessedBy { get; set; }
}

/// <summary>
/// Order lifecycle status enum.
/// </summary>
public enum OrderStatus
{
    Pending = 0,
    Processing = 1,
    Completed = 2,
    Failed = 3,
    Cancelled = 4
}

/// <summary>
/// DTO for creating a new order.
/// </summary>
public record CreateOrderRequest(
    string CustomerName,
    List<string> Items,
    decimal TotalAmount
);

/// <summary>
/// DTO for updating order status.
/// </summary>
public record UpdateOrderStatusRequest(
    OrderStatus NewStatus
);
