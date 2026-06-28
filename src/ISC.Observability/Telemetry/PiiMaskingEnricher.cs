using Serilog.Core;
using Serilog.Events;

namespace ISC.Observability.Telemetry;

/// <summary>
/// Serilog enricher that automatically masks PII (Personally Identifiable Information)
/// in log properties. Compliant with spec section 2.4.
/// 
/// Masks properties whose names contain sensitive keywords:
/// password, token, secret, creditcard, pin, otp, authorization
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

    public void Enrich(LogEvent logEvent, ILogEventPropertyFactory propertyFactory)
    {
        var propertiesToMask = new List<string>();

        foreach (var property in logEvent.Properties)
        {
            if (IsSensitiveProperty(property.Key))
            {
                propertiesToMask.Add(property.Key);
            }
        }

        foreach (var propName in propertiesToMask)
        {
            var originalValue = logEvent.Properties[propName].ToString().Trim('"');
            var maskedValue = MaskValue(originalValue);
            logEvent.AddOrUpdateProperty(
                propertyFactory.CreateProperty(propName, maskedValue));
        }
    }

    private static bool IsSensitiveProperty(string propertyName)
    {
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
        return $"{value[0]}{'*'.ToString().PadRight(value.Length - 2, '*')}{value[^1]}";
    }
}
