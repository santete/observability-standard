using Xunit;

// Các test đều thao tác Serilog.Log (static global) và Console.SetOut (static global),
// nên phải chạy tuần tự để tránh race condition giữa các test class.
[assembly: CollectionBehavior(DisableTestParallelization = true)]
