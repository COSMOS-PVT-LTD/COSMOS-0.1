// Transport/parser conformance only. Python P06 retains full DTO semantic validation.
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

static class Program
{
    static void Visit(JsonElement item, List<string> bits)
    {
        if (item.ValueKind == JsonValueKind.Object)
        {
            var properties = item.EnumerateObject().ToArray();
            if (properties.Select(p => p.Name).Distinct().Count() != properties.Length) throw new InvalidDataException("Duplicate key");
            foreach (var property in properties.OrderBy(p => p.Name, StringComparer.Ordinal)) Visit(property.Value, bits);
        }
        else if (item.ValueKind == JsonValueKind.Array)
            foreach (var child in item.EnumerateArray()) Visit(child, bits);
        else if (item.ValueKind == JsonValueKind.Number)
        {
            double value = item.GetDouble();
            if (!double.IsFinite(value)) throw new InvalidDataException("Nonfinite number");
            bits.Add(BitConverter.DoubleToUInt64Bits(value).ToString("x16"));
        }
    }

    public static int Main()
    {
        try
        {
            using var memory = new MemoryStream();
            using var input = Console.OpenStandardInput();
            byte[] block = new byte[8192];
            int read;
            while ((read = input.Read(block)) > 0)
            {
                if (memory.Length + read > 2 * 1024 * 1024) throw new InvalidDataException("Wire limit");
                memory.Write(block, 0, read);
            }
            using var envelope = JsonDocument.Parse(memory.ToArray(), new JsonDocumentOptions { MaxDepth = 24 });
            var root = envelope.RootElement;
            if (root.EnumerateObject().Select(p => p.Name).Order().SequenceEqual(new[] { "contract_type", "content_sha256", "canonical_json" }.Order()) == false)
                throw new InvalidDataException("Envelope fields");
            string wire = root.GetProperty("canonical_json").GetString()!;
            using var dto = JsonDocument.Parse(wire, new JsonDocumentOptions { MaxDepth = 24 });
            string type = dto.RootElement.GetProperty("contract_type").GetString()!;
            if (type != root.GetProperty("contract_type").GetString() || dto.RootElement.GetProperty("schema_version").GetString() != "1.0.0")
                throw new InvalidDataException("DTO type/version");
            // P06 content_sha256 excludes that field. Reuse exact canonical text; never native number reserialization.
            string checksum = dto.RootElement.GetProperty("content_sha256").GetString()!;
            string removal = "\"content_sha256\":\"" + checksum + "\",";
            int offset = wire.IndexOf(removal, StringComparison.Ordinal);
            if (offset < 0) throw new InvalidDataException("Expected canonical checksum field");
            string body = wire.Remove(offset, removal.Length);
            string hash = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(body))).ToLowerInvariant();
            if (hash != checksum || checksum != root.GetProperty("content_sha256").GetString()) throw new InvalidDataException("Checksum mismatch");
            var bits = new List<string>(); Visit(dto.RootElement, bits);
            Console.WriteLine(JsonSerializer.Serialize(new { canonical_json = wire, content_sha256 = hash, number_bits = bits, semantic_validation_owner = "Python P06" }));
            return 0;
        }
        catch (Exception error) { Console.Error.WriteLine(error.Message); return 2; }
    }
}
