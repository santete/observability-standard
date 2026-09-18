using BenchmarkDotNet.Attributes;
using BenchmarkDotNet.Running;
using ISC.Observability.Metadata;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Http.Features;
using System;

namespace ISC.Observability.Benchmarks
{
    [MemoryDiagnoser]
    public class FilterBenchmark
    {
        private HttpContext _httpContext;
        private string _requestPathStr;
        private object _requestPathObject; // Giả lập Serilog RequestPath PropertyValue

        [GlobalSetup]
        public void Setup()
        {
            // Setup cho New Way (GetLevel / Metadata)
            _httpContext = new DefaultHttpContext();
            var endpoint = new Endpoint(
                requestDelegate: context => System.Threading.Tasks.Task.CompletedTask,
                metadata: new EndpointMetadataCollection(new SuppressRequestLoggingMetadata()),
                displayName: "Health checks"
            );
            _httpContext.SetEndpoint(endpoint);

            // Setup cho Old Way (Filter.ByExcluding)
            _requestPathStr = "\"/health\"";
            _requestPathObject = _requestPathStr;
        }

        [Benchmark(Baseline = true)]
        public bool OldWay_StringMatching()
        {
            // Giả lập logic cũ: Lấy RequestPath từ LogEvent, gọi ToString(), Trim(), và so sánh 7 lần
            var path = _requestPathObject.ToString().Trim('"');
            return path.Equals("/health", StringComparison.OrdinalIgnoreCase) ||
                   path.Equals("/healthchecks", StringComparison.OrdinalIgnoreCase) ||
                   path.Equals("/healthcheck", StringComparison.OrdinalIgnoreCase) ||
                   path.Equals("/healthz", StringComparison.OrdinalIgnoreCase) ||
                   path.Equals("/ready", StringComparison.OrdinalIgnoreCase) ||
                   path.Equals("/alive", StringComparison.OrdinalIgnoreCase) ||
                   path.Equals("/hc", StringComparison.OrdinalIgnoreCase);
        }

        [Benchmark]
        public bool NewWay_MetadataMarker()
        {
            // Giả lập logic mới: Lấy Endpoint từ HttpContext và kiểm tra Metadata
            var endpoint = _httpContext.GetEndpoint();
            return endpoint?.Metadata.GetMetadata<SuppressRequestLoggingMetadata>() != null;
        }
    }
}
