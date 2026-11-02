// Isolated P02 feasibility probe. Not a production API or engineering design tool.
using System.Diagnostics;
using System.Numerics;
using System.Security.Cryptography;
using System.Text.Json;
using PicoGK;

record Request(string Schema, string CorrelationId, string Unit, string Frame,
    string Operation, double RadiusM, double SeparationM, double VoxelM, int Cycles);

sealed class ContractError(string code, string message) : Exception(message)
{
    public string Code { get; } = code;
}

static class Program
{
    const string Schema = "cosmos.picogk.feasibility.v1";
    static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        UnmappedMemberHandling = System.Text.Json.Serialization.JsonUnmappedMemberHandling.Disallow
    };
    static TextWriter Protocol = Console.Out;

    static void Emit(object value) => Protocol.WriteLine(JsonSerializer.Serialize(value, JsonOptions));
    static void Check(bool value, string code, string message)
    {
        if (!value) throw new ContractError(code, message);
    }
    static float Mm(double m) => checked((float)(m * 1000.0));

    public static int Main(string[] args)
    {
        Protocol = Console.Out;
        // Upstream writes lifecycle messages to stdout. Keep protocol JSON uncontaminated.
        Console.SetOut(Console.Error);
        string? correlation = null;
        try
        {
            Check(args.Length == 1, "OUTPUT_ARGUMENT", "Pass one trusted fixture output directory.");
            // Read a bounded request before invoking any native API.
            char[] input = new char[8193];
            int count = Console.In.ReadBlock(input, 0, input.Length);
            Check(count <= 8192, "REQUEST_TOO_LARGE", "Request exceeds 8192 characters.");
            string payload = new string(input, 0, count);
            using var document = JsonDocument.Parse(payload);
            Check(document.RootElement.ValueKind == JsonValueKind.Object,
                "INVALID_JSON", "Expected a JSON object.");
            var keys = document.RootElement.EnumerateObject().Select(p => p.Name).ToArray();
            var expected = new[] { "schema", "correlationId", "unit", "frame", "operation",
                "radiusM", "separationM", "voxelM", "cycles" };
            Check(keys.Length == expected.Length && keys.Distinct().Count() == keys.Length
                && keys.All(expected.Contains), "FIELDS", "Expected exactly the required fields.");
            var req = JsonSerializer.Deserialize<Request>(payload, JsonOptions)
                ?? throw new ContractError("INVALID_JSON", "Expected a JSON object.");
            correlation = req.CorrelationId;
            Check(req.Schema == Schema, "SCHEMA", "Unsupported schema.");
            Check(Guid.TryParse(req.CorrelationId, out _), "CORRELATION", "Expected a UUID.");
            Check(req.Unit == "m", "UNIT", "Inputs must use SI metres.");
            Check(req.Frame == "right-handed-xyz", "FRAME", "Unsupported coordinate frame.");
            Check(double.IsFinite(req.RadiusM) && double.IsFinite(req.SeparationM)
                && double.IsFinite(req.VoxelM), "NONFINITE", "Dimensions must be finite.");
            Check(req.RadiusM > 0 && req.RadiusM <= 0.02 && req.SeparationM >= 0
                && req.SeparationM <= 0.05, "DIMENSION", "Outside bounded probe dimensions.");
            Check(req.VoxelM >= 0.000125 && req.VoxelM <= 0.002
                && req.RadiusM / req.VoxelM >= 4 && req.RadiusM / req.VoxelM <= 160,
                "RESOLUTION", "Outside bounded probe resolution.");
            Check(req.Cycles >= 1 && req.Cycles <= 10, "CYCLES", "Expected 1 to 10 lifecycle cycles.");
            Check(new[] { "sphere", "union", "difference", "intersection", "self_union",
                "self_difference", "disjoint_intersection" }.Contains(req.Operation),
                "OPERATION", "Unsupported Boolean operation.");
            string version = Library.strVersion();
            Check(version.Contains("26.2"), "ABI_VERSION", "Expected native ABI 26.2.");
            Emit(new { type = "started", schema = Schema, correlationId = correlation,
                nativeName = Library.strName(), nativeVersion = version,
                nativeBuild = Library.strBuildInfo(), inputUnit = "m", kernelUnit = "mm" });
            Directory.CreateDirectory(args[0]);
            var timer = Stopwatch.StartNew();
            var cycles = new List<object>();
            for (int cycle = 0; cycle < req.Cycles; cycle++)
            {
                using var lib = new Library(Mm(req.VoxelM));
                long before = lib.nTotalMemUsage();
                bool empty;
                float volumeMm3 = 0;
                string? path = null;
                string? hash = null;
                long peakKernel;
                using (var a = Voxels.voxSphere(lib, Vector3.Zero, Mm(req.RadiusM)))
                using (var b = Voxels.voxSphere(lib,
                    new Vector3(Mm(req.Operation == "disjoint_intersection"
                        ? req.RadiusM * 3 : req.SeparationM), 0, 0), Mm(req.RadiusM)))
                using (var result = a.voxDuplicate())
                {
                    switch (req.Operation)
                    {
                        case "union": result.BoolAdd(b); break;
                        case "difference": result.BoolSubtract(b); break;
                        case "intersection": case "disjoint_intersection": result.BoolIntersect(b); break;
                        case "self_union": result.BoolAdd(a); break;
                        case "self_difference": result.BoolSubtract(a); break;
                    }
                    empty = result.bIsEmpty();
                    if (!empty)
                    {
                        result.CalculateProperties(out volumeMm3, out _);
                        using var mesh = result.mshAsMesh();
                        path = Path.Combine(args[0], $"{req.Operation}-{cycle}.stl");
                        Check(!File.Exists(path), "ARTIFACT_EXISTS", "Refusing to overwrite an artifact.");
                        // STL coordinates explicitly written in metres; sidecar declares units.
                        mesh.SaveToStlFile(path, Mesh.EStlUnit.M);
                        hash = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))).ToLowerInvariant();
                    }
                    peakKernel = lib.nTotalMemUsage();
                }
                long after = lib.nTotalMemUsage();
                long allocations = lib.nMeshesAllocated() + lib.nVoxelsAllocated()
                    + lib.nLatticesAllocated() + lib.nVdbMetasAllocated()
                    + lib.nPolyLinesAllocated() + lib.nVdbFilesAllocated()
                    + lib.nScalarFieldsAllocated() + lib.nVectorFieldsAllocated();
                Check(after == before && allocations == 0, "LIFECYCLE_LEAK", "Native objects remain allocated.");
                cycles.Add(new { cycle, empty, nativeVolumeM3 = volumeMm3 * 1e-9,
                    path, sha256 = hash, artifactUnit = "m", peakKernelBytes = peakKernel,
                    nativeBytesBefore = before, nativeBytesAfter = after,
                    nativeAllocationsAfter = allocations });
            }
            timer.Stop();
            Emit(new { type = "completed", schema = Schema, correlationId = correlation,
                operation = req.Operation, voxelM = req.VoxelM, elapsedMs = timer.Elapsed.TotalMilliseconds,
                peakWorkingSetBytes = Process.GetCurrentProcess().PeakWorkingSet64, cycles });
            return 0;
        }
        catch (Exception ex)
        {
            string code = ex switch
            {
                ContractError typed => typed.Code,
                JsonException => "INVALID_JSON",
                DllNotFoundException => "NATIVE_LOAD",
                EntryPointNotFoundException => "NATIVE_ABI",
                _ => "WORKER_FAILURE"
            };
            Emit(new { type = "failed", schema = Schema, correlationId = correlation,
                error = new { code, message = ex.Message } });
            return 2;
        }
    }
}
