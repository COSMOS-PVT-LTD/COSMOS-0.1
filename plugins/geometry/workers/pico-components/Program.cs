// COSMOS-owned field recipes. PicoGK renders these fields directly; no OCCT mesh input.
using System.Numerics;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using PicoGK;

sealed class Hole { public double radius {get;set;} public double[] center_yz {get;set;}=[]; public double[] slope_yz {get;set;}=[]; public double[]? axial_range {get;set;} }
sealed class Cavity { public double[][] profile {get;set;}=[]; public double[]? sector {get;set;} public bool open_passage {get;set;} public string? open_face {get;set;} }
sealed class Cooling { public int count {get;set;} public double width_rad {get;set;} public double hot_ligament {get;set;} public double depth {get;set;} public double phase_rad {get;set;} }
sealed class Pipe { public double bore_radius {get;set;} public double outer_radius {get;set;} public double? bend_radius {get;set;} public double? angle_rad {get;set;} }
sealed class Part {
    public string part_id {get;set;}=""; public string feature_id {get;set;}=""; public string frame_id {get;set;}=""; public string role {get;set;}="";
    public double[][] profile {get;set;}=[]; public Hole[] holes {get;set;}=[]; public Cavity[] cavities {get;set;}=[];
    public double[]? sector {get;set;} public Cooling? cooling {get;set;} public Pipe? pipe {get;set;}
    public double[] rotation {get;set;}=[]; public double[] translation_m {get;set;}=[]; public double[] bounds_m {get;set;}=[];
}

sealed class ComponentField : IBoundedImplicit {
    readonly Part p; public BBox3 oBounds {get;}
    public ComponentField(Part part,double voxel) {
        p=part; var b=p.bounds_m;
        oBounds=new BBox3(new Vector3((float)((b[0]-2*voxel)*1000),(float)((b[1]-2*voxel)*1000),(float)((b[2]-2*voxel)*1000)),
            new Vector3((float)((b[3]+2*voxel)*1000),(float)((b[4]+2*voxel)*1000),(float)((b[5]+2*voxel)*1000)));
    }
    static double Hypot(double a,double b)=>Math.Sqrt(a*a+b*b);
    static double Segment(double x,double r,double ax,double ar,double bx,double br) {
        double dx=bx-ax,dr=br-ar,d=dx*dx+dr*dr;
        double t=d==0?0:Math.Clamp(((x-ax)*dx+(r-ar)*dr)/d,0,1);
        return Hypot(x-ax-t*dx,r-ar-t*dr);
    }
    static double Radius(double[][] rows,double x,int column) {
        if(x<=rows[0][0])return rows[0][column];
        for(int i=1;i<rows.Length;i++)if(x<=rows[i][0]) {
            double t=(x-rows[i-1][0])/(rows[i][0]-rows[i-1][0]);return rows[i-1][column]*(1-t)+rows[i][column]*t;
        }
        return rows[^1][column];
    }
    static double Meridian(double[][] rows,double x,double r) {
        double distance=double.PositiveInfinity;bool inner=rows.Any(row=>row[1]>0);
        for(int i=1;i<rows.Length;i++) {
            distance=Math.Min(distance,Segment(x,r,rows[i-1][0],rows[i-1][2],rows[i][0],rows[i][2]));
            if(inner)distance=Math.Min(distance,Segment(x,r,rows[i-1][0],rows[i-1][1],rows[i][0],rows[i][1]));
        }
        distance=Math.Min(distance,Segment(x,r,rows[0][0],rows[0][1],rows[0][0],rows[0][2]));
        distance=Math.Min(distance,Segment(x,r,rows[^1][0],rows[^1][1],rows[^1][0],rows[^1][2]));
        return x>=rows[0][0]&&x<=rows[^1][0]&&r>=Radius(rows,x,1)&&r<=Radius(rows,x,2)?-distance:distance;
    }
    static double Wedge(double y,double z,double phase,double width) {
        double angle=phase+width/2,forward=y*Math.Cos(angle)+z*Math.Sin(angle),side=-y*Math.Sin(angle)+z*Math.Cos(angle);
        return Math.Abs(side)*Math.Cos(width/2)-forward*Math.Sin(width/2);
    }
    public double Residual(double wx,double wy,double wz) {
        var m=p.rotation;double dx=wx-p.translation_m[0],dy=wy-p.translation_m[1],dz=wz-p.translation_m[2];
        double x=dx*m[0]+dy*m[3]+dz*m[6],y=dx*m[1]+dy*m[4]+dz*m[7],z=dx*m[2]+dy*m[5]+dz*m[8],r=Hypot(y,z);
        if(p.pipe?.bend_radius is double bend) {
            double tube=Hypot(Hypot(x,y-bend)-bend,z),angle=p.pipe.angle_rad!.Value;
            return Math.Max(Math.Max(tube-p.pipe.outer_radius,p.pipe.bore_radius-tube),Math.Max(-x,Math.Cos(angle)*x+Math.Sin(angle)*(y-bend)));
        }
        double result=Meridian(p.profile,x,r);
        if(p.sector is not null)result=Math.Max(result,Wedge(y,z,p.sector[0],p.sector[1]));
        foreach(var h in p.holes) {
            if(h.axial_range is not null&&(x<h.axial_range[0]||x>h.axial_range[1]))continue;
            double a=y-h.center_yz[0],b=z-h.center_yz[1],s=h.slope_yz[0],t=h.slope_yz[1];
            double projection=(x+a*s+b*t)/(1+s*s+t*t);
            double cylinder=Math.Sqrt(Math.Pow(x-projection,2)+Math.Pow(a-projection*s,2)+Math.Pow(b-projection*t,2))-h.radius;
            result=Math.Max(result,-cylinder);
        }
        foreach(var c in p.cavities) {
            var rows=c.profile;double cut;
            if(c.open_face is not null) {
                cut=Math.Max(rows[0][1]-r,r-rows[0][2]);
                cut=Math.Max(cut,c.open_face=="start"?x-rows[^1][0]:rows[0][0]-x);
            } else if(c.open_passage) {
                if(x<rows[0][0]||x>rows[^1][0])continue;
                cut=Math.Max(Radius(rows,x,1)-r,r-Radius(rows,x,2));
            } else cut=Meridian(rows,x,r);
            if(c.sector is not null)cut=Math.Max(cut,Wedge(y,z,c.sector[0],c.sector[1]));
            result=Math.Max(result,-cut);
        }
        if(p.cooling is not null) {
            var c=p.cooling;double low=Radius(p.profile,x,1)+c.hot_ligament,angular=double.PositiveInfinity;
            for(int i=0;i<c.count;i++)angular=Math.Min(angular,Wedge(y,z,c.phase_rad+2*Math.PI*i/c.count,c.width_rad));
            result=Math.Max(result,-Math.Max(Math.Max(low-r,r-low-c.depth),angular));
        }
        return result; // Signed CSG constraint residual; not a global Euclidean-distance certificate.
    }
    public float fSignedDistance(in Vector3 v) {
        double value=1000*Residual(v.X/1000.0,v.Y/1000.0,v.Z/1000.0);
        // A grid node exactly on a cap must have one consistent sign. Otherwise
        // signed zero / double projection roundoff creates detached coplanar
        // sheets in the native zero-isosurface. This is a double-arithmetic tie
        // rule, not a voxel-sized offset or a manufacturing tolerance. Keep the
        // original residual everywhere outside this explicitly reported bound.
        double bound=64*2.220446049250313e-16*Math.Max(1,p.bounds_m.Max(Math.Abs)*1000);
        return (float)(Math.Abs(value)<=bound?bound:value);
    }
}

sealed class ContractError(string code,string message):Exception(message) {public string Code {get;}=code;}
static class Program {
    const string Protocol="cosmos.ngg.worker.v1",Version="picogk-2.2.0.components.v1",Schema="cosmos.picogk-components-field.v1";
    static TextWriter Out=Console.Out;
    public static void Check(bool value,string code,string text){if(!value)throw new ContractError(code,text);}
    static string Hash(byte[] bytes)=>Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
    static string Text(JsonElement e,string key)=>e.GetProperty(key).GetString()??throw new ContractError("PICO_FIELDS",key);
    static void Keys(JsonElement e,params string[] names) {var keys=e.EnumerateObject().Select(p=>p.Name).ToArray();Check(keys.Length==names.Length&&keys.Distinct().Count()==keys.Length&&keys.All(names.Contains),"PICO_FIELDS","Exact unique fields required");}
    static JsonDocument Wire(JsonElement e,string key,string type) {
        string raw=Text(e.GetProperty("wires"),key);Check(Hash(Encoding.UTF8.GetBytes(raw))==Text(e.GetProperty("wire_sha256"),key),"HASH_MISMATCH","Exact wire hash mismatch");
        var d=JsonDocument.Parse(raw);Check(Text(d.RootElement,"contract_type")==type&&Text(d.RootElement,"schema_version")=="1.0.0","PICO_SCHEMA","Wrong typed wire contract");return d;
    }
    static void Validate(Part p) {
        foreach(string id in new[]{p.part_id,p.feature_id,p.frame_id})Check(Regex.IsMatch(id,@"\A[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\z"),"PICO_ID","Invalid part identity");
        bool elbow=p.pipe?.bend_radius is not null;
        Check(p.rotation.Length==9&&p.translation_m.Length==3&&p.bounds_m.Length==6&&(elbow||p.profile.Length>=2)&&p.profile.Length<=129&&p.holes.Length<=128&&p.cavities.Length<=128,"PICO_CAPACITY","Bounded field data required");
        foreach(double n in p.rotation.Concat(p.translation_m).Concat(p.bounds_m).Concat(p.profile.SelectMany(x=>x)))Check(double.IsFinite(n)&&Math.Abs(n)<=10,"PICO_NUMBER","Nonfinite/outside envelope");
        Check(p.profile.All(r=>r.Length==3&&r[1]>=0&&r[2]>r[1])&&p.profile.Zip(p.profile.Skip(1)).All(v=>v.First[0]<v.Second[0]),"PICO_PROFILE","Strict ordered positive profile required");
        Check(Enumerable.Range(0,3).All(i=>p.bounds_m[i]<p.bounds_m[i+3]),"PICO_BOUNDS","Invalid field bounds");
        for(int i=0;i<3;i++)for(int j=0;j<3;j++)Check(Math.Abs(Enumerable.Range(0,3).Sum(k=>p.rotation[3*k+i]*p.rotation[3*k+j])-(i==j?1:0))<=1e-9,"PICO_FRAME","Orthogonal source placement required");
        var m=p.rotation;Check(Math.Abs(m[0]*(m[4]*m[8]-m[5]*m[7])-m[1]*(m[3]*m[8]-m[5]*m[6])+m[2]*(m[3]*m[7]-m[4]*m[6])-1)<1e-9,"PICO_FRAME","Proper rotation required");
        foreach(var h in p.holes)Check(h.center_yz.Length==2&&h.slope_yz.Length==2&&double.IsFinite(h.radius)&&h.radius>0&&h.radius<1&&h.center_yz.Concat(h.slope_yz).All(double.IsFinite)&&(h.axial_range is null||(h.axial_range.Length==2&&h.axial_range.All(double.IsFinite)&&h.axial_range[0]<h.axial_range[1])),"PICO_HOLE","Invalid finite bore");
        if(p.cooling is not null)Check(p.cooling.count>0&&p.cooling.count<=128&&p.cooling.depth>0&&p.cooling.hot_ligament>0&&double.IsFinite(p.cooling.phase_rad)&&p.cooling.width_rad>0&&p.cooling.width_rad<2*Math.PI/p.cooling.count,"PICO_COOLING","Invalid cooling field");
        foreach(var c in p.cavities)Check(c.profile.Length>=2&&c.profile.Length<=129&&c.profile.All(r=>r.Length==3&&r.All(double.IsFinite)&&r[1]>=0&&r[2]>r[1])&&(c.open_face is null||c.open_face=="start"||c.open_face=="end")&&(c.sector is null||(c.sector.Length==2&&c.sector.All(double.IsFinite)&&c.sector[1]>0&&c.sector[1]<Math.PI)),"PICO_CAVITY","Invalid cavity");
        if(p.sector is not null)Check(p.sector.Length==2&&p.sector.All(double.IsFinite)&&p.sector[1]>0&&p.sector[1]<Math.PI,"PICO_SECTOR","Invalid angular sector");
        if(p.pipe?.bend_radius is double bend)Check(bend>p.pipe.outer_radius&&p.pipe.bore_radius>0&&p.pipe.outer_radius>p.pipe.bore_radius&&p.pipe.angle_rad>0&&p.pipe.angle_rad<Math.PI,"PICO_PIPE","Invalid elbow field");
    }
    static (int kept,int removed) WriteMesh(BinaryWriter writer,Mesh mesh) {
        int kept=0,removed=0;
        for(int i=0;i<mesh.nTriangleCount();i++) {
            mesh.GetTriangle(i,out Vector3 aa,out Vector3 bb,out Vector3 cc);
            // Explicit mm->metre float32 export; topology checks use these exact final vertices.
            var a=new[]{(float)(aa.X/1000.0),(float)(aa.Y/1000.0),(float)(aa.Z/1000.0)};
            var b=new[]{(float)(bb.X/1000.0),(float)(bb.Y/1000.0),(float)(bb.Z/1000.0)};
            var c=new[]{(float)(cc.X/1000.0),(float)(cc.Y/1000.0),(float)(cc.Z/1000.0)};
            Check(a.Concat(b).Concat(c).All(float.IsFinite),"PICO_MESH","Nonfinite exported vertex");
            double ux=(double)b[0]-a[0],uy=(double)b[1]-a[1],uz=(double)b[2]-a[2],vx=(double)c[0]-a[0],vy=(double)c[1]-a[1],vz=(double)c[2]-a[2];
            double nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx,length=Math.Sqrt(nx*nx+ny*ny+nz*nz);
            if(length==0){removed++;continue;}
            writer.Write((float)(nx/length));writer.Write((float)(ny/length));writer.Write((float)(nz/length));
            foreach(float n in a.Concat(b).Concat(c))writer.Write(n);writer.Write((ushort)0);kept++;
            Check(kept<=4000000,"PICO_CAPACITY","Part exceeds4M implicit mesh triangles");
        }
        // This distinct component encoding removes only zero-area triangles.
        // Their fraction is observed, not a dimensional tolerance. The complete
        // surviving mesh must independently pass closure/genus/orientation/size.
        Check(kept>0,"PICO_DEGENERACY","No positive-area triangles survive encoding");return(kept,removed);
    }
    public static int Main(string[] args) {
        Out=Console.Out;Console.SetOut(Console.Error);string job="",correlation="";
        try {
            using var stream=new MemoryStream();using var input=Console.OpenStandardInput();byte[] block=new byte[8192];int n;
            while((n=input.Read(block))>0){Check(stream.Length+n<=2*1024*1024,"PICO_CAPACITY","Bounded input required");stream.Write(block,0,n);}
            using var doc=JsonDocument.Parse(stream.ToArray(),new JsonDocumentOptions{MaxDepth=32});var e=doc.RootElement;
            if(args.Length==1&&args[0]=="--sample") {
                // Pure managed recipe probe for cross-language verification, never exposed by HTTP.
                var part=e.GetProperty("part").Deserialize<Part>()!;Validate(part);var field=new ComponentField(part,1e-4);
                var points=e.GetProperty("points").Deserialize<double[][]>()!;Check(points.Length<=4096&&points.All(v=>v.Length==3&&v.All(double.IsFinite)),"PICO_CAPACITY","Bounded probe points required");
                Out.WriteLine(JsonSerializer.Serialize(points.Select(p=>field.Residual(p[0],p[1],p[2]))));return 0;
            }
            Check(args.Length==1&&Path.IsPathFullyQualified(args[0])&&Directory.Exists(args[0]),"PICO_OUTPUT","Private existing output directory required");
            Keys(e,"protocol","action","job_id","correlation_id","wires","wire_sha256","component_schema","fields_wire","fields_sha256");
            Check(Text(e,"protocol")==Protocol&&Text(e,"action")=="build"&&Text(e,"component_schema")==Schema,"PICO_SCHEMA","Explicit component build protocol required");
            job=Text(e,"job_id");correlation=Text(e,"correlation_id");Check(Regex.IsMatch(job,@"\A[A-Za-z0-9_.:-]{1,128}\z")&&Regex.IsMatch(correlation,@"\A[A-Za-z0-9_.:-]{1,128}\z"),"PICO_ID","Invalid job/correlation");
            using var rq=Wire(e,"request","GeometryBuildRequest");using var sn=Wire(e,"snapshot","DesignSnapshot");using var gr=Wire(e,"graph","GeometryFeatureGraph");var r=rq.RootElement;
            Check(Text(r,"backend_id")=="picogk"&&Text(r,"backend_version")==Version&&Text(r,"representation")=="implicit_field"&&Text(r,"approximation_profile")=="sparse_volume"&&Text(r,"correlation_id")==correlation,"PICO_POLICY","Wrong backend/representation/version/correlation");
            Check(Text(r,"snapshot_id")==Text(sn.RootElement,"content_sha256")&&Text(r,"feature_graph_sha256")==Text(gr.RootElement,"content_sha256")&&Text(r,"feature_graph_id")==Text(gr.RootElement,"graph_id"),"PICO_LINEAGE","Stale source wires");
            Check(r.GetProperty("output_formats").EnumerateArray().Select(x=>x.GetString()).SequenceEqual(new[]{"stl"}),"PICO_FORMAT","No implicit-to-STEP substitution");
            double h=r.GetProperty("voxel_resolution_m").GetDouble();Check(double.IsFinite(h)&&h>=2.5e-5&&h<=.002,"PICO_RESOLUTION","Outside explicit voxel envelope");
            string fields=Text(e,"fields_wire");Check(Hash(Encoding.UTF8.GetBytes(fields))==Text(e,"fields_sha256"),"HASH_MISMATCH","Field recipe hash mismatch");
            var parts=JsonSerializer.Deserialize<Part[]>(fields)!;Check(parts.Length>0&&parts.Length<=64&&parts.Select(p=>p.part_id).Distinct().Count()==parts.Length,"PICO_CAPACITY","Unique bounded parts required");foreach(var p in parts)Validate(p);
            double cells=parts.Sum(p=>Enumerable.Range(0,3).Aggregate(1.0,(a,i)=>a*((p.bounds_m[i+3]-p.bounds_m[i])/h+5)));
            Check(cells<=120000000,"PICO_CAPACITY","Field sampling exceeds120M cells");
            Check(Library.strVersion().Contains("26.2"),"PICO_ABI","Wrong native ABI");
            Out.WriteLine(JsonSerializer.Serialize(new{protocol=Protocol,job_id=job,correlation_id=correlation,event_type="started",backend_version=Version}));Out.Flush();
            using var lib=new Library((float)(h*1000));long before=lib.nTotalMemUsage(),peak=before;int count=0;var observations=new List<object>();
            string source=Path.Combine(args[0],"source.vdb"),export=Path.Combine(args[0],"export.stl");Check(!File.Exists(source)&&!File.Exists(export),"ARTIFACT_EXISTS","Refuse artifact overwrite");
            using(var vdb=new OpenVdbFile(lib))using(var file=new FileStream(export,FileMode.CreateNew))using(var writer=new BinaryWriter(file)) {
                byte[] header=new byte[80];Encoding.ASCII.GetBytes("COSMOS PicoGK component mesh; UNITS= m; implicit fields; NOT manufacturing approved").AsSpan(0,79).CopyTo(header);writer.Write(header);writer.Write((uint)0);
                foreach(var p in parts) {
                    var field=new ComponentField(p,h);using var vox=new Voxels(lib,field);Check(!vox.bIsEmpty(),"PICO_EMPTY","Field part is empty at requested resolution: "+p.part_id);
                    vdb.nAdd(vox,p.part_id);using var mesh=vox.mshAsMesh();var written=WriteMesh(writer,mesh);int start=count;count+=written.kept;Check(count<=4000000,"PICO_CAPACITY","Assembly exceeds4M implicit triangles; split explicit outputs");
                    observations.Add(new{p.part_id,p.feature_id,p.frame_id,p.role,triangle_start=start,triangle_count=written.kept,removed_exact_zero_faces=written.removed,field_name=p.part_id});peak=Math.Max(peak,lib.nTotalMemUsage());
                }
                writer.Seek(80,SeekOrigin.Begin);writer.Write((uint)count);vdb.SaveToFile(source);
            }
            using(var reimport=new OpenVdbFile(lib,source))foreach(var p in parts){using var vox=reimport.voxGet(p.part_id);Check(!vox.bIsEmpty(),"PICO_REIMPORT","Named field lost after VDB round trip");}
            long allocations=lib.nVoxelsAllocated()+lib.nMeshesAllocated()+lib.nVdbFilesAllocated()+lib.nVdbMetasAllocated()+lib.nScalarFieldsAllocated()+lib.nVectorFieldsAllocated()+lib.nLatticesAllocated()+lib.nPolyLinesAllocated();
            Check(allocations==0&&lib.nTotalMemUsage()==before,"PICO_LIFECYCLE","Native allocations remain after disposal");
            Out.WriteLine(JsonSerializer.Serialize(new{protocol=Protocol,job_id=job,correlation_id=correlation,event_type="completed",backend_version=Version,source_name="source.vdb",source_sha256=Hash(File.ReadAllBytes(source)),
                exports=new[]{new{name="export.stl",sha256=Hash(File.ReadAllBytes(export)),format="stl",file_unit="m"}},
                metrics=new{parts=observations,triangle_count=count,input_unit="m",kernel_unit="mm",actual_voxel_m=lib.fVoxelSize/1000.0,native_peak_bytes=peak,native_allocations_after=allocations,vdb_roundtrip_fields=parts.Select(p=>p.part_id),
                    conditioning="per-part exact-zero-only faces after float32 metre export; surviving vertices unchanged; no weld/smooth",
                    zero_isovalue_tie_break="positive within 64 double ULP scale of source bounds (mm); nominal recipes unchanged",
                    zero_isovalue_max_bound_m=parts.Max(p=>64*2.220446049250313e-16*Math.Max(1,p.bounds_m.Max(Math.Abs)*1000))/1000,
                    fields_sha256=Text(e,"fields_sha256"),wire_sha256=e.GetProperty("wire_sha256")}}));return 0;
        }catch(Exception error){Out.WriteLine(JsonSerializer.Serialize(new{protocol=Protocol,job_id=job,correlation_id=correlation,event_type="failed",backend_version=Version,code=error is ContractError c?c.Code:"PICO_WORKER_FAILURE",message=error.Message}));return 1;}
    }
}
