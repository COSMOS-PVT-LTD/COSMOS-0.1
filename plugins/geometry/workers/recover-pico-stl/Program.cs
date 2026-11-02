// Isolated byte-recovery attempt: remesh retained native fields, never rebuild a
// different design or write the authority store. Restoration is somebody else's
// explicit step and requires the original length AND SHA256 to match exactly.
using System.Numerics;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using PicoGK;

static class Recovery {
    const string ExpectedVdb="4b3b860732f22c5463a7d37273b91a2e478e44ee8befdd960cf5b07c3d0fa596";
    const string ExpectedStl="db02644594cf9bbced1796e4d7bb77fd44833dedc4ec712e6ebfa148916f4245";
    const long ExpectedLength=184726884, ExpectedVdbLength=46264101;
    static void Require(bool value,string message) {if(!value)throw new InvalidDataException(message);}
    static string Hash(string path) {
        using var stream=File.OpenRead(path);return Convert.ToHexString(SHA256.HashData(stream)).ToLowerInvariant();
    }
    // Exact source encoder from the pinned original component worker, lines
    // 128-148. Do not swap in STL library export or a new triangle ordering.
    static (int kept,int removed) WriteMesh(BinaryWriter writer,Mesh mesh) {
        int kept=0,removed=0;
        for(int i=0;i<mesh.nTriangleCount();i++) {
            mesh.GetTriangle(i,out Vector3 aa,out Vector3 bb,out Vector3 cc);
            var a=new[]{(float)(aa.X/1000.0),(float)(aa.Y/1000.0),(float)(aa.Z/1000.0)};
            var b=new[]{(float)(bb.X/1000.0),(float)(bb.Y/1000.0),(float)(bb.Z/1000.0)};
            var c=new[]{(float)(cc.X/1000.0),(float)(cc.Y/1000.0),(float)(cc.Z/1000.0)};
            Require(a.Concat(b).Concat(c).All(float.IsFinite),"Nonfinite exported vertex");
            double ux=(double)b[0]-a[0],uy=(double)b[1]-a[1],uz=(double)b[2]-a[2],vx=(double)c[0]-a[0],vy=(double)c[1]-a[1],vz=(double)c[2]-a[2];
            double nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx,length=Math.Sqrt(nx*nx+ny*ny+nz*nz);
            if(length==0){removed++;continue;}
            writer.Write((float)(nx/length));writer.Write((float)(ny/length));writer.Write((float)(nz/length));
            foreach(float n in a.Concat(b).Concat(c))writer.Write(n);writer.Write((ushort)0);kept++;
            Require(kept<=4000000,"Part exceeds4M implicit mesh triangles");
        }
        Require(kept>0,"No positive-area triangles survive encoding");return(kept,removed);
    }
    public static int Main(string[] args) {
        var output=Console.Out;Console.SetOut(Console.Error);
        try {
            Require(args.Length==4,"Explicit VDB, retained summary, NEW STL and NEW report paths required");
            string source=args[0],summary=args[1],target=args[2],report=args[3];
            Require(args.All(Path.IsPathFullyQualified),"Absolute paths required");
            Require(File.Exists(source)&&File.Exists(summary),"Existing retained VDB/summary required");
            Require(!File.Exists(target)&&!File.Exists(report)&&Directory.Exists(Path.GetDirectoryName(target))&&Directory.Exists(Path.GetDirectoryName(report)),"New outputs with existing parent required");
            Require(new FileInfo(source).Length==ExpectedVdbLength&&Hash(source)==ExpectedVdb,"Retained original VDB hash/length mismatch");
            Require(new FileInfo(summary).Length<2097152,"Bounded retained summary required");
            using var document=JsonDocument.Parse(File.ReadAllBytes(summary));var root=document.RootElement;
            var attachments=root.GetProperty("attachments").EnumerateArray().ToArray();
            Require(attachments.Any(v=>v.GetProperty("name").GetString()=="source.vdb"&&v.GetProperty("content_hash").GetString()==ExpectedVdb&&v.GetProperty("byte_length").GetInt64()==ExpectedVdbLength),"Retained summary does not bind this VDB");
            Require(attachments.Any(v=>v.GetProperty("name").GetString()=="export.stl"&&v.GetProperty("content_hash").GetString()==ExpectedStl&&v.GetProperty("byte_length").GetInt64()==ExpectedLength),"Retained summary does not bind the missing historical STL");
            var observed=root.GetProperty("worker_observations");double h=observed.GetProperty("actual_voxel_m").GetDouble();
            Require(double.IsFinite(h)&&h>0&&h<=.002,"Bounded retained voxel size required");
            var parts=observed.GetProperty("parts").EnumerateArray().ToArray();Require(parts.Length>0&&parts.Length<=64,"Bounded named fields required");
            Require(parts.Select(p=>p.GetProperty("field_name").GetString()).Distinct().Count()==parts.Length,"Distinct retained field order required");
            Require(Library.strVersion().Contains("26.2"),"Original PicoGK native26.2 ABI required");
            var observations=new List<object>();int count=0;long before;
            using(var lib=new Library((float)(h*1000))) {
                before=lib.nTotalMemUsage();
                using(var vdb=new OpenVdbFile(lib,source))using(var file=new FileStream(target,FileMode.CreateNew,FileAccess.Write))using(var writer=new BinaryWriter(file)) {
                    Require(vdb.nFieldCount()==parts.Length,"Retained VDB field coverage differs from summary");
                    byte[] header=new byte[80];Encoding.ASCII.GetBytes("COSMOS PicoGK component mesh; UNITS= m; implicit fields; NOT manufacturing approved").AsSpan(0,79).CopyTo(header);writer.Write(header);writer.Write((uint)0);
                    foreach(var part in parts) {
                        string name=part.GetProperty("field_name").GetString()!;
                        Require(part.GetProperty("triangle_start").GetInt32()==count,"Original part-span ordering inconsistent");
                        using var vox=vdb.voxGet(name);Require(!vox.bIsEmpty(),"Retained named field is empty");
                        using var mesh=vox.mshAsMesh();var written=WriteMesh(writer,mesh);
                        Require(written.kept==part.GetProperty("triangle_count").GetInt32(),"Remeshed field triangle count differs from history: "+name);
                        Require(written.removed==part.GetProperty("removed_exact_zero_faces").GetInt32(),"Removed-zero count differs from history: "+name);
                        observations.Add(new{field_name=name,triangle_start=count,triangle_count=written.kept,removed_exact_zero_faces=written.removed});count+=written.kept;
                        Require(count<=4000000&&file.Position<=256*1024*1024,"Bounded native mesh output exceeded");
                        Console.Error.WriteLine(name+": "+written.kept);
                    }
                    writer.Seek(80,SeekOrigin.Begin);writer.Write((uint)count);
                }
                Require(lib.nTotalMemUsage()==before,"Native allocations not released");
            }
            string actual=Hash(target);long length=new FileInfo(target).Length;bool sourceUnchanged=Hash(source)==ExpectedVdb;
            bool exact=actual==ExpectedStl&&length==ExpectedLength&&sourceUnchanged;
            var evidence=new{schema="cosmos.exact-pico-stl-recovery-attempt.v1",exact_byte_match=exact,
                source_vdb=source,source_vdb_sha256=ExpectedVdb,source_vdb_unchanged=sourceUnchanged,
                retained_summary=summary,retained_summary_sha256=Hash(summary),recovered_candidate=target,
                expected_sha256=ExpectedStl,actual_sha256=actual,expected_length=ExpectedLength,actual_length=length,
                triangle_count=count,actual_voxel_m=h,parts=observations,
                original_authority_modified=false,geometry_regenerated_from_new_design=false,
                method="Retained named VDB field remesh with original exact-zero-only float32 metre STL encoder/header/order; source fields unchanged",
                engineering_acceptance="NOT_PERFORMED",physical_validation="NOT_PERFORMED"};
            using(var stream=new FileStream(report,FileMode.CreateNew))JsonSerializer.Serialize(stream,evidence,new JsonSerializerOptions{WriteIndented=true});
            output.WriteLine(JsonSerializer.Serialize(new{exact_byte_match=exact,actual_sha256=actual,actual_length=length,report}));
            return exact?0:2;
        } catch(Exception error) {
            output.WriteLine(JsonSerializer.Serialize(new{exact_byte_match=false,error=error.Message,original_authority_modified=false}));return 1;
        }
    }
}
