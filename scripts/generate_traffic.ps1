# Continuous Traffic Generator for SigNoz & ISC.Observability SDK Verification
Write-Host "Starting continuous traffic generator..." -ForegroundColor Green

while ($true) {
    # 1. MvpDemo.Service GET endpoints (mvp-demo-service)
    try { curl.exe -s http://localhost:5080/ | Out-Null } catch {}
    try { curl.exe -s http://localhost:5080/api/orders | Out-Null } catch {}
    try { curl.exe -s http://localhost:5080/api/orders/demo-pii | Out-Null } catch {}
    try { curl.exe -s http://localhost:5080/api/polyglot-test | Out-Null } catch {}
    
    # POST Create Order
    try {
        $jsonPayload = '{"customerName":"Nguyen Van A","totalAmount":150000.0,"items":[{"productName":"Observability SDK Book","quantity":1,"price":150000.0}]}'
        curl.exe -s -X POST http://localhost:5080/api/orders -H "Content-Type: application/json" -d $jsonPayload | Out-Null
    } catch {}

    # 2. SigNozTestApp GET endpoints (signoz-test-service)
    try { curl.exe -s http://localhost:5100/ | Out-Null } catch {}
    try { curl.exe -s http://localhost:5100/api/test-trace | Out-Null } catch {}
    try { curl.exe -s http://localhost:5100/api/test-pii | Out-Null } catch {}

    # Error simulation endpoints for Error rate tracking
    try { curl.exe -s http://localhost:5080/api/orders/simulate-error | Out-Null } catch {}
    try { curl.exe -s http://localhost:5100/api/test-error | Out-Null } catch {}

    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Telemetry traffic batch sent successfully to SigNoz!" -ForegroundColor Cyan
    Start-Sleep -Seconds 2
}
