// Headless P07 adapter. Exact P06 text/hashes stay opaque; no native re-rounding.
using System.Numerics;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using PicoGK;

sealed class ContractError(string code, string message) : Exception(message)
{
    public string Code { get; } = code;
}

static class Program
{
    const string Protocol = "cosmos.ngg.worker.v1";
    const string Version = "picogk-2.2.0.p07v1";
    static TextWriter Out = Console.Out;
    static void Check(bool ok, string code, string message)
    {
        if (!ok) throw new ContractError(code, message);
    }
    static void Emit(object value) => Out.WriteLine(JsonSerializer.Serialize(value));
    static string Hash(byte[] data) => Convert.ToHexString(SHA256.HashData(data)).ToLowerInvariant();
    static void Keys(JsonElement element, params string[] expected)
    {
        Check(element.ValueKind == JsonValueKind.Object, "INVALID_FIELDS", "Expected an object");
        var keys = element.EnumerateObject().Select(p => p.Name).ToArray();
        Check(keys.Length == expected.Length && keys.Distinct().Count() == keys.Length && keys.All(expected.Contains), "INVALID_FIELDS", "Unknown, duplicate or missing fields");
    }
    static string Text(JsonElement element, string key) => element.GetProperty(key).GetString() ?? throw new ContractError("INVALID_TYPE", key);
    static void Id(string text) => Check(Regex.IsMatch(text, @"\A[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\z"), "INVALID_IDENTIFIER", "Invalid protocol identity");
    static double Number(JsonElement element)
    {
        Check(element.ValueKind == JsonValueKind.Number && element.TryGetDouble(out double n) && double.IsFinite(n), "NONFINITE", "Expected a finite number");
        return element.GetDouble();
    }
    static float Mm(double value)
    {
        float result = (float)(value * 1000);
        Check(float.IsFinite(result), "NONFINITE", "Kernel conversion overflow");
        return result;
    }
    static JsonDocument Wire(JsonElement envelope, string name, string type)
    {
        string text = Text(envelope.GetProperty("wires"), name);
        Check(Hash(Encoding.UTF8.GetBytes(text)) == Text(envelope.GetProperty("wire_sha256"), name), "HASH_MISMATCH", "Exact wire bytes changed");
        var doc = JsonDocument.Parse(text, new JsonDocumentOptions { MaxDepth = 24 });
        Check(Text(doc.RootElement, "schema_version") == "1.0.0" && Text(doc.RootElement, "contract_type") == type, "SCHEMA_VERSION", "Unsupported P06 DTO");
        return doc;
    }
    public static int Main(string[] args)
    {
        Out = Console.Out;
        Console.SetOut(Console.Error); // Keep upstream lifecycle text off protocol stdout.
        string job = "", correlation = "";
        try
        {
            Check(args.Length == 1 && Path.IsPathFullyQualified(args[0]) && Directory.Exists(args[0]), "OUTPUT_ARGUMENT", "Pass the private trusted job directory");
            using var stream = new MemoryStream();
            byte[] block = new byte[8192];
            using var input = Console.OpenStandardInput();
            int read;
            while ((read = input.Read(block)) > 0)
            {
                Check(stream.Length + read <= 2 * 1024 * 1024, "CONTRACT_LIMIT", "Envelope exceeds limit");
                stream.Write(block, 0, read);
            }
            using var document = JsonDocument.Parse(stream.ToArray(), new JsonDocumentOptions { MaxDepth = 24 });
            var envelope = document.RootElement;
            Keys(envelope, "protocol", "action", "job_id", "correlation_id", "wires", "wire_sha256");
            Check(Text(envelope, "protocol") == Protocol, "PROTOCOL_VERSION", "Unsupported protocol");
            job = Text(envelope, "job_id"); correlation = Text(envelope, "correlation_id"); Id(job); Id(correlation);
            Keys(envelope.GetProperty("wires"), "request", "snapshot", "graph");
            Keys(envelope.GetProperty("wire_sha256"), "request", "snapshot", "graph");
            using var rd = Wire(envelope, "request", "GeometryBuildRequest");
            using var sd = Wire(envelope, "snapshot", "DesignSnapshot");
            using var gd = Wire(envelope, "graph", "GeometryFeatureGraph");
            var request = rd.RootElement; var snapshot = sd.RootElement; var graph = gd.RootElement;
            Check(Text(request, "backend_id") == "picogk" && Text(request, "backend_version") == Version, "BACKEND_VERSION", "Unqualified backend");
            Check(Text(request, "snapshot_id") == Text(snapshot, "content_sha256") && Text(graph, "snapshot_id") == Text(snapshot, "content_sha256")
                && Text(request, "feature_graph_sha256") == Text(graph, "content_sha256") && Text(request, "feature_graph_id") == Text(graph, "graph_id")
                && Text(request, "correlation_id") == correlation, "STALE_REQUEST", "Lineage mismatch");
            Check(Text(request, "representation") == "implicit_field" && Text(request, "approximation_profile") == "sparse_volume", "REPRESENTATION_MISMATCH", "PicoGK builds implicit geometry only");
            Check(request.GetProperty("output_formats").EnumerateArray().Select(e => e.GetString()).SequenceEqual(new[] { "stl" }), "UNSUPPORTED_FORMAT", "This slice independently accepts STL only");
            var frames = snapshot.GetProperty("frames").EnumerateArray().ToArray();
            double[] identity = [1, 0, 0, 0, 1, 0, 0, 0, 1];
            Check(frames.Length == 1 && frames[0].GetProperty("parent_frame_id").ValueKind == JsonValueKind.Null
                && frames[0].GetProperty("origin_m").EnumerateArray().Select(Number).SequenceEqual(new double[] { 0, 0, 0 })
                && frames[0].GetProperty("rotation").EnumerateArray().Select(Number).SequenceEqual(identity)
                && Text(frames[0], "units") == "m" && Text(frames[0], "handedness") == "right", "UNSUPPORTED_FRAME", "Expected identity SI root");
            string frame = Text(frames[0], "frame_id");
            Check(Text(request, "frame_id") == frame && Text(snapshot, "frame_id") == frame, "UNSUPPORTED_FRAME", "Frame mismatch");
            double voxel = Number(request.GetProperty("voxel_resolution_m"));
            Check(voxel >= .00025 && voxel <= .002 && Number(request.GetProperty("source_tolerance_m")) > 0
                && Number(request.GetProperty("export_tolerance_m")) > 0, "RESOLUTION", "Outside bounded resolution/tolerances");
            var features = graph.GetProperty("features").EnumerateArray().ToDictionary(e => Text(e, "feature_id"));
            var boundParameters = features.Values.SelectMany(f => f.GetProperty("parameter_refs").EnumerateArray().Select(e => e.GetString()!)).ToHashSet();
            var parameters = new Dictionary<string, double>();
            foreach (var parameter in snapshot.GetProperty("parameters_si").EnumerateArray())
            {
                string name = Text(parameter, "name");
                if (!boundParameters.Contains(name)) continue; // Unbound physics parameters are not geometry dimensions.
                Check(Text(parameter, "unit_symbol") == "m" && parameter.GetProperty("dimension").EnumerateArray().Select(e => e.GetInt32()).SequenceEqual(new[] { 1, 0, 0, 0, 0, 0, 0 }), "INVALID_UNIT", "Geometry parameters require metres");
                double number = Number(parameter.GetProperty("value_si"));
                Check(Math.Abs(number) <= .1 && parameters.TryAdd(name, number), "DIMENSION_LIMIT", "Invalid or duplicate bounded parameter");
            }
            var outputs = graph.GetProperty("output_feature_ids").EnumerateArray().Select(e => e.GetString()!).ToArray();
            Check(features.Count is > 0 and <= 64 && outputs.Length == 1 && features.ContainsKey(outputs[0]), "INVALID_FEATURE", "Invalid graph size/output");
            foreach (var feature in features.Values)
                Check(Text(feature, "frame_id") == frame && Text(feature, "representation") == "implicit_field", "UNSUPPORTED_FRAME", "Feature frame/representation mismatch");
            double workBound = features.Values.Where(f => Text(f, "operation") == "primitive.sphere")
                .Sum(f => 8 * Math.Pow(parameters[Text(f, "feature_id") + ".radius"] / voxel, 3));
            Check(workBound <= 16000000, "CAPACITY_LIMIT", "Graph exceeds explicit native work bound");
            Check(Library.strVersion().Contains("26.2"), "NATIVE_ABI", "Native ABI mismatch");
            if (Text(envelope, "action") == "health")
            {
                Emit(new { protocol = Protocol, job_id = job, correlation_id = correlation, event_type = "health", backend_version = Version, native_version = Library.strVersion(), wire_sha256 = envelope.GetProperty("wire_sha256") });
                return 0;
            }
            Check(Text(envelope, "action") == "build", "UNSUPPORTED_OPERATION", "Unsupported action");
            Emit(new { protocol = Protocol, job_id = job, correlation_id = correlation, event_type = "started", backend_version = Version });
            using var lib = new Library(Mm(voxel));
            long before = lib.nTotalMemUsage();
            var nodes = new Dictionary<string, Voxels>();
            object? completed = null;
            try
            {
                while (nodes.Count < features.Count)
                {
                    bool advanced = false;
                    foreach (var (id, feature) in features.OrderBy(x => x.Key, StringComparer.Ordinal))
                    {
                        if (nodes.ContainsKey(id)) continue;
                        string op = Text(feature, "operation");
                        var deps = feature.GetProperty("dependency_ids").EnumerateArray().Select(e => e.GetString()!).ToArray();
                        if (deps.Any(d => !nodes.ContainsKey(d))) continue;
                        var refs = feature.GetProperty("parameter_refs").EnumerateArray().Select(e => e.GetString()!).ToArray();
                        if (op == "primitive.sphere")
                        {
                            Check(deps.Length == 0 && refs.Order().SequenceEqual(new[] { id + ".radius", id + ".x", id + ".y", id + ".z" }.Order()), "INVALID_FEATURE", "Sphere bindings mismatch");
                            double r = parameters[id + ".radius"];
                            Check(r > 0 && r / voxel >= 4 && r / voxel <= 160, "RESOLUTION", "Sphere resolution exceeds slice bounds");
                            nodes[id] = Voxels.voxSphere(lib, new Vector3(Mm(parameters[id + ".x"]), Mm(parameters[id + ".y"]), Mm(parameters[id + ".z"])), Mm(r));
                        }
                        else
                        {
                            Check(deps.Length == 2 && refs.Length == 0 && new[] { "boolean.union", "boolean.difference", "boolean.intersection" }.Contains(op), "UNSUPPORTED_OPERATION", "Unsupported Boolean intent");
                            if (op == "boolean.difference")
                            {
                                Check(deps.Count(d => d.EndsWith(".lhs", StringComparison.Ordinal)) == 1 && deps.Count(d => d.EndsWith(".rhs", StringComparison.Ordinal)) == 1,
                                    "INVALID_FEATURE", "Subtraction must declare .lhs/.rhs dependency roles");
                                deps = [deps.Single(d => d.EndsWith(".lhs", StringComparison.Ordinal)), deps.Single(d => d.EndsWith(".rhs", StringComparison.Ordinal))];
                            }
                            var result = nodes[deps[0]].voxDuplicate(); nodes[id] = result;
                            if (op == "boolean.union") result.BoolAdd(nodes[deps[1]]);
                            else if (op == "boolean.difference") result.BoolSubtract(nodes[deps[1]]);
                            else result.BoolIntersect(nodes[deps[1]]);
                        }
                        advanced = true;
                    }
                    Check(advanced, "FEATURE_CYCLE", "Dangling/cyclic graph");
                }
                var output = nodes[outputs[0]];
                Check(!output.bIsEmpty(), "EMPTY_GEOMETRY", "Empty geometry has no accepted export");
                output.CalculateProperties(out float volumeMm3, out _);
                string source = Path.Combine(args[0], "source.vdb"), export = Path.Combine(args[0], "export.stl");
                Check(!File.Exists(source) && !File.Exists(export), "ARTIFACT_EXISTS", "Refusing overwrite");
                using (var vdb = new OpenVdbFile(lib)) { vdb.nAdd(output, "geometry"); vdb.SaveToFile(source); }
                using (var mesh = output.mshAsMesh()) mesh.SaveToStlFile(export, Mesh.EStlUnit.M);
                completed = new { protocol = Protocol, job_id = job, correlation_id = correlation, event_type = "completed", backend_version = Version,
                    source_name = "source.vdb", source_sha256 = Hash(File.ReadAllBytes(source)),
                    exports = new[] { new { name = "export.stl", sha256 = Hash(File.ReadAllBytes(export)), format = "stl", file_unit = "m" } },
                    metrics = new { volume_m3 = volumeMm3 * 1e-9, native_peak_bytes = lib.nTotalMemUsage(), actual_voxel_m = lib.fVoxelSize / 1000.0,
                        kernel_unit = "mm", input_unit = "m", wire_sha256 = envelope.GetProperty("wire_sha256") } };
            }
            finally { foreach (var node in nodes.Values) node.Dispose(); }
            long allocations = lib.nVoxelsAllocated() + lib.nMeshesAllocated() + lib.nVdbFilesAllocated() + lib.nVdbMetasAllocated()
                + lib.nLatticesAllocated() + lib.nPolyLinesAllocated() + lib.nScalarFieldsAllocated() + lib.nVectorFieldsAllocated();
            Check(lib.nTotalMemUsage() == before && allocations == 0, "LIFECYCLE_LEAK", "Native objects remain after scope");
            Emit(completed!);
            return 0;
        }
        catch (Exception error)
        {
            string code = error switch { ContractError e => e.Code, JsonException => "INVALID_JSON", DllNotFoundException => "NATIVE_LOAD", EntryPointNotFoundException => "NATIVE_ABI", _ => "WORKER_FAILURE" };
            Emit(new { protocol = Protocol, job_id = job, correlation_id = correlation, event_type = "failed", backend_version = Version, code, message = error.Message });
            return 2;
        }
    }
}
