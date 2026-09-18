using BenchmarkDotNet.Running;

namespace ISC.Observability.Benchmarks
{
    class Program
    {
        static void Main(string[] args)
        {
            var summary = BenchmarkRunner.Run<FilterBenchmark>();
        }
    }
}
