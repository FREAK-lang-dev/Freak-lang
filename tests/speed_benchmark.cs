// Pure CPU benchmark for bragging-rights runs.
// Usage:
//   dotnet build or csc speed_benchmark.cs
//   speed_benchmark.exe
//   speed_benchmark.exe 50000000

using System;
using System.Diagnostics;

internal static class SpeedBenchmark
{
    private const long BenchMod = 1_000_003L;

    private static long BenchStep(long x)
    {
        long a = x * 123L + 4567L;
        long q = a / BenchMod;
        return a - q * BenchMod;
    }

    private static long RunBenchmark(int iterations)
    {
        long a = 1;
        long b = 2;
        long c = 3;
        long d = 4;

        for (int i = 0; i < iterations; i++)
        {
            a = BenchStep(a + i);
            b = BenchStep(b + a);
            c = BenchStep(c + b);
            d = BenchStep(d + c);
        }

        return a + b + c + d;
    }

    private static int Main(string[] args)
    {
        int iterations = 10_000_000;
        if (args.Length > 0 && int.TryParse(args[0], out int parsed))
        {
            iterations = parsed;
        }

        Console.WriteLine("C# pure speed benchmark");
        Console.WriteLine($"iterations={iterations}");

        var sw = Stopwatch.StartNew();
        long checksum = RunBenchmark(iterations);
        sw.Stop();

        Console.WriteLine($"checksum={checksum}");
        Console.WriteLine($"elapsed_ms={sw.ElapsedMilliseconds}");
        return 0;
    }
}
