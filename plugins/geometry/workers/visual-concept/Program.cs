// One fixed, abstract decorative marker for a display-only illustration.
// No inputs, geometry parameters, units, CAD solids or export formats.
using System.Numerics;
using System.Text.Json;
using PicoGK;

sealed class Marker : IBoundedImplicit
{
    public BBox3 oBounds { get; } = new(new Vector3(-12), new Vector3(12));
    public float fSignedDistance(in Vector3 p) => p.Length() - 8;
}

static class Program
{
    static int Main()
    {
        var output = Console.Out;
        Console.SetOut(Console.Error);
        try
        {
            using var library = new Library(2f);
            using var voxels = new Voxels(library, new Marker());
            using var mesh = voxels.mshAsMesh();
            var count = mesh.nTriangleCount();
            if (count <= 0 || count > 20000) throw new InvalidOperationException("Marker preview exceeds display budget.");
            var triangles = new List<float>(count * 9);
            for (int i = 0; i < count; i++)
            {
                mesh.GetTriangle(i, out Vector3 a, out Vector3 b, out Vector3 c);
                foreach (var p in new[] { a, b, c })
                    triangles.AddRange(new[] { p.X / 100, p.Y / 100, p.Z / 100 });
            }
            output.WriteLine(JsonSerializer.Serialize(new { backend = "PicoGK", triangles }));
            return 0;
        }
        catch (Exception error)
        {
            Console.Error.WriteLine(error.Message);
            return 1;
        }
    }
}
