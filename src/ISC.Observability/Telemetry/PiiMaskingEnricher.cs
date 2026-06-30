using Serilog.Core;
using Serilog.Events;
using System.Collections.Concurrent;

namespace ISC.Observability.Telemetry;

/// <summary>
/// Serilog enricher that automatically masks PII (Personally Identifiable Information)
/// in log properties. Compliant with spec section 2.4.
/// 
/// Performance Optimized: Uses ConcurrentDictionary to cache property name checks
/// to prevent garbage collection pressure from string allocations during heavy logging.
/// </summary>
public class PiiMaskingEnricher : ILogEventEnricher
{
    private static readonly HashSet<string> SensitiveKeywords = new(StringComparer.OrdinalIgnoreCase)
    {
        "password", "passwd", "pwd",
        "token", "accesstoken", "refreshtoken",
        "secret", "secretkey", "apikey",
        "creditcard", "cardnumber",
        "pin", "otp",
        "authorization", "auth"
    };

    // Cache kết quả kiểm tra property name (Zero-allocation cho các lần kiểm tra sau)
    private static readonly ConcurrentDictionary<string, bool> SensitivityCache = new(StringComparer.Ordinal);

    public void Enrich(LogEvent logEvent, ILogEventPropertyFactory propertyFactory)
    {
        List<string>? propertiesToMask = null;

        foreach (var property in logEvent.Properties)
        {
            if (IsSensitiveProperty(property.Key))
            {
                propertiesToMask ??= new List<string>();
                propertiesToMask.Add(property.Key);
            }
        }

        if (propertiesToMask != null)
        {
            foreach (var propName in propertiesToMask)
            {
                var originalValue = logEvent.Properties[propName].ToString().Trim('"');
                var maskedValue = MaskValue(originalValue);
                logEvent.AddOrUpdateProperty(
                    propertyFactory.CreateProperty(propName, maskedValue));
            }
        }
    }

    private static bool IsSensitiveProperty(string propertyName)
    {
        // Nếu đã từng kiểm tra property này, lấy từ Cache ra luôn (O(1) & Zero Allocation)
        return SensitivityCache.GetOrAdd(propertyName, EvaluateSensitivity);
    }

    private static bool EvaluateSensitivity(string propertyName)
    {
        // Chỉ cấp phát bộ nhớ trong lần đầu tiên bắt gặp property name này
        var normalized = propertyName.Replace("_", "").Replace("-", "").Replace(".", "");
        return SensitiveKeywords.Any(keyword =>
            normalized.Contains(keyword, StringComparison.OrdinalIgnoreCase));
    }

    private static string MaskValue(string value)
    {
        if (string.IsNullOrEmpty(value))
            return "***";

        // For credit card-like values (16+ digits), keep last 4
        if (value.Length >= 12 && value.All(c => char.IsDigit(c) || c == ' ' || c == '-'))
        {
            var digits = new string(value.Where(char.IsDigit).ToArray());
            if (digits.Length >= 12)
                return $"****-****-****-{digits[^4..]}";
        }

        // For short values (< 4 chars), fully mask
        if (value.Length <= 4)
            return "****";

        // For other values, show first char and last char
        return $"{value[0]}{new string('*', value.Length - 2)}{value[^1]}";
    }
}
