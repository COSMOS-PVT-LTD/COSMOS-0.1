// New, deliberately unqualified research entry point. No changes to v1 receipts.
using System.Numerics;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using PicoGK;

sealed class CompactGroup {
    public string part_id {get;set;}="";
    public Part[] add {get;set;}=[];
    public Part[] subtract {get;set;}=[];
    public double[] bounds_m {get;set;}=[];
}
// Pure-sector cuts may share one meridian: min_i max(M,W_i)=max(M,min_i W_i).
// This factorization changes neither profile stations nor the CSG zero surface.
// Everything outside this strict identical-profile/placement case keeps the
// original ComponentField evaluator. The admitted component source is unchanged.
sealed class SharedSectorCuts {
    readonly ComponentField ring;
    readonly double[] rotation, translation;
    readonly (double cosine, double sine, double halfCosine, double halfSine)[] wedges;
    static bool Same(double[] a,double[] b)=>a.Length==b.Length&&a.Zip(b).All(v=>BitConverter.DoubleToInt64Bits(v.First)==BitConverter.DoubleToInt64Bits(v.Second));
    static bool Pure(Part p)=>p.sector is not null&&p.holes.Length==0&&p.cavities.Length==0&&p.pipe is null&&p.cooling is null;
    public static SharedSectorCuts? Create(Part[] parts,double h) {
        if(parts.Length<2||parts.Any(p=>!Pure(p)))return null;
        Part first=parts[0];
        if(parts.Any(p=>p.profile.Length!=first.profile.Length||!Same(p.rotation,first.rotation)||!Same(p.translation_m,first.translation_m)||
            p.profile.Zip(first.profile).Any(v=>!Same(v.First,v.Second))))return null;
        return new SharedSectorCuts(parts,h);
    }
    SharedSectorCuts(Part[] parts,double h) {
        Part first=parts[0];rotation=first.rotation;translation=first.translation_m;
        var full=new Part{part_id=first.part_id,feature_id=first.feature_id,frame_id=first.frame_id,role=first.role,
            profile=first.profile,rotation=first.rotation,translation_m=first.translation_m,bounds_m=first.bounds_m};
        ring=new ComponentField(full,h);
        wedges=parts.Select(p=>{
            var s=p.sector!;double angle=s[0]+s[1]/2;
            return(Math.Cos(angle),Math.Sin(angle),Math.Cos(s[1]/2),Math.Sin(s[1]/2));
        }).ToArray();
    }
    public double Residual(double wx,double wy,double wz) {
        double dx=wx-translation[0],dy=wy-translation[1],dz=wz-translation[2];var m=rotation;
        double y=dx*m[1]+dy*m[4]+dz*m[7],z=dx*m[2]+dy*m[5]+dz*m[8],angular=double.PositiveInfinity;
        foreach(var w in wedges) {
            double forward=y*w.cosine+z*w.sine,side=-y*w.sine+z*w.cosine;
            double next=Math.Abs(side)*w.halfCosine-forward*w.halfSine;
            if(next<angular)angular=next; // Enumerable.Min retains the first equal minimum, including signed zero.
        }
        return Math.Max(ring.Residual(wx,wy,wz),angular);
    }
}
sealed class CompactField : IBoundedImplicit {
    readonly ComponentField[] positive, negative;
    readonly SharedSectorCuts? sharedNegative;
    readonly double tie;
    public BBox3 oBounds {get;}
    public bool SharedSectors=>sharedNegative is not null;
    public double TieBoundMm=>tie;
    public CompactField(CompactGroup group, double h) {
        positive=group.add.Select(p=>new ComponentField(p,h)).ToArray();
        negative=group.subtract.Select(p=>new ComponentField(p,h)).ToArray();
        sharedNegative=SharedSectorCuts.Create(group.subtract,h);
        var b=group.bounds_m;
        oBounds=new BBox3(new Vector3((float)((b[0]-2*h)*1000),(float)((b[1]-2*h)*1000),(float)((b[2]-2*h)*1000)),
                         new Vector3((float)((b[3]+2*h)*1000),(float)((b[4]+2*h)*1000),(float)((b[5]+2*h)*1000)));
        tie=64*2.220446049250313e-16*Math.Max(1,b.Max(Math.Abs)*1000);
    }
    double ReferenceResidual(double x,double y,double z) {
        double value=positive.Min(f=>f.Residual(x,y,z));
        return negative.Length==0?value:Math.Max(value,-negative.Min(f=>f.Residual(x,y,z)));
    }
    public double Residual(double x,double y,double z,bool reference=false) {
        if(reference)return ReferenceResidual(x,y,z);
        double value=positive[0].Residual(x,y,z);
        for(int i=1;i<positive.Length;i++) {
            double next=positive[i].Residual(x,y,z);if(next<value)value=next;
        }
        if(negative.Length==0)return value;
        double cut;
        if(!reference&&sharedNegative is not null)cut=sharedNegative.Residual(x,y,z);
        else {
            cut=negative[0].Residual(x,y,z);
            for(int i=1;i<negative.Length;i++) {
                double next=negative[i].Residual(x,y,z);if(next<cut)cut=next;
            }
        }
        return Math.Max(value,-cut);
    }
    public float Classified(double x,double y,double z,bool reference=false) {
        double value=Residual(x,y,z,reference)*1000;
        if(Math.Abs(value)<=tie) {
            // A common end face inside a true union is not an exterior surface.
            // Classify only the ULP-sized zero band using a tiny neighborhood;
            // neither operand coordinates nor nonzero field values are moved.
            bool outside=false;double probe=1e-10;
            for(int i=-1;i<=1;i++)for(int j=-1;j<=1;j++)for(int k=-1;k<=1;k++)
                if((i!=0||j!=0||k!=0)&&Residual(x+i*probe,y+j*probe,z+k*probe,reference)*1000>tie)outside=true;
            value=outside?tie:-tie;
        }
        return (float)value;
    }
    public float fSignedDistance(in Vector3 v)=>Classified(v.X/1000.0,v.Y/1000.0,v.Z/1000.0);
}
static class CompactProgram {
    static void Check(bool value,string message) {if(!value)throw new ArgumentException(message);}
    static bool Finite(double x)=>double.IsFinite(x)&&Math.Abs(x)<=10;
    static void Rows(double[][] rows) {
        Check(rows.Length>=2&&rows.Length<=129&&rows.All(r=>r.Length==3&&r.All(Finite)&&r[1]>=0&&r[2]>r[1]),"Invalid bounded profile");
        Check(rows.Zip(rows.Skip(1)).All(v=>v.First[0]<v.Second[0]),"Unordered profile");
    }
    static void Validate(Part p) {
        Check(p.rotation.Length==9&&p.translation_m.Length==3&&p.bounds_m.Length==6,"Invalid placement/bounds");
        Check(p.rotation.Concat(p.translation_m).Concat(p.bounds_m).All(Finite),"Invalid coordinate");
        Check(Enumerable.Range(0,3).All(i=>p.bounds_m[i]<p.bounds_m[i+3]),"Invalid ordered bounds");
        for(int i=0;i<3;i++)for(int j=0;j<3;j++)Check(Math.Abs(Enumerable.Range(0,3).Sum(k=>p.rotation[3*k+i]*p.rotation[3*k+j])-(i==j?1:0))<1e-9,"Invalid rotation");
        var m=p.rotation;Check(Math.Abs(m[0]*(m[4]*m[8]-m[5]*m[7])-m[1]*(m[3]*m[8]-m[5]*m[6])+m[2]*(m[3]*m[7]-m[4]*m[6])-1)<1e-9,"Improper rotation");
        if(p.pipe?.bend_radius is not null) {
            var pipe=p.pipe;
            Check(Finite(pipe.bend_radius.Value)&&pipe.bend_radius>pipe.outer_radius&&pipe.bore_radius>0&&pipe.outer_radius>pipe.bore_radius&&pipe.angle_rad>0&&pipe.angle_rad<Math.PI,"Invalid elbow");
        } else Rows(p.profile);
        Check(p.holes.Length<=128&&p.cavities.Length<=128&&p.cooling is null,"Only expanded bounded compact operands accepted");
        foreach(var hole in p.holes)Check(hole.radius>0&&hole.radius<1&&hole.center_yz.Length==2&&hole.slope_yz.Length==2&&hole.center_yz.Concat(hole.slope_yz).Append(hole.radius).All(Finite)&&
            (hole.axial_range is null||(hole.axial_range.Length==2&&hole.axial_range.All(Finite)&&hole.axial_range[0]<hole.axial_range[1])),"Invalid hole");
        foreach(var cavity in p.cavities) {
            Rows(cavity.profile); Sector(cavity.sector);
            Check(cavity.open_face is null or "start" or "end","Invalid open cavity");
        }
        Sector(p.sector);
    }
    static void Sector(double[]? sector) {if(sector is not null)Check(sector.Length==2&&sector.All(Finite)&&sector[1]>0&&sector[1]<Math.PI,"Invalid sector");}
    static int SampleCompare(CompactGroup[] groups,double h,TextWriter output) {
        var reports=new List<object>();bool passed=true;var random=new Random(20261030);
        foreach(var group in groups) {
            var field=new CompactField(group,h);var points=new List<(double x,double y,double z,string basis)>();var b=group.bounds_m;
            void Add(double x,double y,double z,string basis) {
                Check(points.Count<65536,"Bounded managed comparison exceeded65,536points pergroup");points.Add((x,y,z,basis));
            }
            for(int n=0;n<2048;n++)Add(b[0]-2*h+random.NextDouble()*(b[3]-b[0]+4*h),
                b[1]-2*h+random.NextDouble()*(b[4]-b[1]+4*h),b[2]-2*h+random.NextDouble()*(b[5]-b[2]+4*h),"seeded_interior_exterior");
            for(int i=0;i<=8;i++)for(int j=0;j<=8;j++)for(int k=0;k<=8;k++)
                Add(Math.Round((b[0]+(b[3]-b[0])*i/8)/h)*h,Math.Round((b[1]+(b[4]-b[1])*j/8)/h)*h,
                    Math.Round((b[2]+(b[5]-b[2])*k/8)/h)*h,"voxel_grid");
            foreach(var part in group.add.Concat(group.subtract)) {
                if(part.profile.Length==0)continue;
                var angles=part.sector is null?new[]{0.0,Math.PI/2,Math.PI}:new[]{part.sector[0],part.sector[0]+part.sector[1]/2,part.sector[0]+part.sector[1]};
                foreach(var row in part.profile)foreach(double radius in new[]{row[1],(row[1]+row[2])/2,row[2]})
                foreach(double angle in angles)foreach(double offset in new[]{-1e-10,0.0,1e-10}) {
                    double x=row[0]+offset,y=radius*Math.Cos(angle),z=radius*Math.Sin(angle);var m=part.rotation;var t=part.translation_m;
                    Add(m[0]*x+m[1]*y+m[2]*z+t[0],m[3]*x+m[4]*y+m[5]*z+t[1],m[6]*x+m[7]*y+m[8]*z+t[2],"profiles_caps_sectors_near_interfaces");
                }
            }
            double maximum=0;int rawBits=0,doubleClassBits=0,floatGridBits=0,nearTie=0;var witnesses=new List<object>();
            foreach(var p in points) {
                double baseline=field.Residual(p.x,p.y,p.z,true),optimized=field.Residual(p.x,p.y,p.z);
                Check(double.IsFinite(baseline)&&double.IsFinite(optimized),"Nonfinite managed reference/residual");
                double error=Math.Abs(baseline-optimized);maximum=Math.Max(maximum,error);
                if(BitConverter.DoubleToInt64Bits(baseline)!=BitConverter.DoubleToInt64Bits(optimized))rawBits++;
                float a=field.Classified(p.x,p.y,p.z,true),c=field.Classified(p.x,p.y,p.z);
                if(BitConverter.SingleToInt32Bits(a)!=BitConverter.SingleToInt32Bits(c))doubleClassBits++;
                var v=new Vector3((float)(p.x*1000),(float)(p.y*1000),(float)(p.z*1000));
                a=field.Classified(v.X/1000.0,v.Y/1000.0,v.Z/1000.0,true);c=field.fSignedDistance(v);
                if(BitConverter.SingleToInt32Bits(a)!=BitConverter.SingleToInt32Bits(c))floatGridBits++;
                if(Math.Abs(baseline*1000)<=field.TieBoundMm)nearTie++;
                if(error>0&&witnesses.Count<8)witnesses.Add(new{point_m=new[]{p.x,p.y,p.z},p.basis,baseline,optimized,error});
            }
            bool same=maximum==0&&rawBits==0&&doubleClassBits==0&&floatGridBits==0;passed&=same;
            reports.Add(new{group.part_id,sample_count=points.Count,shared_sector_factoring=field.SharedSectors,
                maximum_absolute_residual_error_m=maximum,raw_bitwise_differences=rawBits,
                double_coordinate_tie_classification_bitwise_differences=doubleClassBits,float32_kernel_coordinate_bitwise_differences=floatGridBits,
                reference_tie_band_samples=nearTie,passed=same,witnesses});
        }
        output.WriteLine(JsonSerializer.Serialize(new{schema="cosmos.compact-managed-residual-comparison.v1",passed,
            seed=20261030,groups=reports,native_generation=false,qualification="NOT_PERFORMED",
            scope="Bounded original-ComponentField CSG vs shared-sector algebra and allocation-free combination samples, including tie neighborhoods; not native topology, engine fidelity, refinement or engineering acceptance"}));
        return passed?0:1;
    }
    static (int kept,int removed) WriteMesh(BinaryWriter writer,Mesh mesh,int previous) {
        int kept=0,removed=0;
        for(int i=0;i<mesh.nTriangleCount();i++) {
            mesh.GetTriangle(i,out Vector3 aa,out Vector3 bb,out Vector3 cc);
            Vector3 a=aa/1000,b=bb/1000,c=cc/1000;
            var values=new[]{a.X,a.Y,a.Z,b.X,b.Y,b.Z,c.X,c.Y,c.Z};
            Check(values.All(float.IsFinite),"Nonfinite mesh vertex");
            double ux=(double)b.X-a.X,uy=(double)b.Y-a.Y,uz=(double)b.Z-a.Z,vx=(double)c.X-a.X,vy=(double)c.Y-a.Y,vz=(double)c.Z-a.Z;
            double nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx,length=Math.Sqrt(nx*nx+ny*ny+nz*nz);
            if(length==0){removed++;continue;}
            Check(previous+kept<4000000,"Compact triangle budget exceeded");
            writer.Write((float)(nx/length));writer.Write((float)(ny/length));writer.Write((float)(nz/length));
            foreach(float value in values)writer.Write(value);writer.Write((ushort)0);kept++;
        }
        Check(kept>0,"No positive-area faces");return(kept,removed);
    }
    public static int Main(string[] args) {
        var output=Console.Out;Console.SetOut(Console.Error);
        try {
            bool sampleCompare=args.Length==1&&args[0]=="--sample-compare";
            Check(sampleCompare||(args.Length==1&&Path.IsPathFullyQualified(args[0])&&Directory.Exists(args[0])),"Private existing output directory or explicit bounded sample comparison required");
            using var input=Console.OpenStandardInput();using var memory=new MemoryStream();byte[] block=new byte[8192];int read;
            while((read=input.Read(block))>0){Check(memory.Length+read<=2097152,"Input exceeds 2MiB");memory.Write(block,0,read);}
            using var document=JsonDocument.Parse(memory.ToArray(),new JsonDocumentOptions{MaxDepth=32});var root=document.RootElement;
            Check(root.GetProperty("research_only").GetBoolean(),"Explicit research-only execution required");
            double h=root.GetProperty("voxel_m").GetDouble();Check(double.IsFinite(h)&&h>=2.5e-5&&h<=.002,"Explicit supported voxel size required");
            var recipe=root.GetProperty("recipe");Check(recipe.GetProperty("schema").GetString()=="cosmos.compact-engine-csg.v1","Wrong recipe schema");
            var groups=JsonSerializer.Deserialize<CompactGroup[]>(recipe.GetProperty("groups"))!;
            Check(groups.Length>0&&groups.Length<=24&&groups.Select(g=>g.part_id).Distinct().Count()==groups.Length,"Unique bounded groups required");
            foreach(var g in groups) {
                Check(Regex.IsMatch(g.part_id,@"\A[A-Za-z0-9_.:-]{1,128}\z")&&g.add.Length>0&&g.add.Length<=24&&g.subtract.Length<=16,"Invalid group");
                Check(g.bounds_m.Length==6&&g.bounds_m.All(Finite)&&Enumerable.Range(0,3).All(i=>g.bounds_m[i]<g.bounds_m[i+3]),"Invalid group bounds");
                foreach(var p in g.add.Concat(g.subtract))Validate(p);
            }
            double cells=groups.Sum(g=>Enumerable.Range(0,3).Aggregate(1.0,(a,i)=>a*((g.bounds_m[i+3]-g.bounds_m[i])/h+5)));
            Check(cells<=120000000,"Compact field budget exceeds 120M cells");
            if(sampleCompare)return SampleCompare(groups,h,output);
            Check(Library.strVersion().Contains("26.2"),"Unsupported PicoGK native ABI");
            string source=Path.Combine(args[0],"UNQUALIFIED-source.vdb"),meshFile=Path.Combine(args[0],"UNQUALIFIED-export.stl");
            Check(!File.Exists(source)&&!File.Exists(meshFile),"Refuse artifact overwrite");
            using var lib=new Library((float)(h*1000));long before=lib.nTotalMemUsage();int count=0;var observations=new List<object>();
            using(var vdb=new OpenVdbFile(lib))using(var file=new FileStream(meshFile,FileMode.CreateNew))using(var writer=new BinaryWriter(file)) {
                byte[] header=new byte[80];Encoding.ASCII.GetBytes("COSMOS COMPACT RESEARCH ONLY; UNITS= m; NOT QUALIFIED").CopyTo(header,0);writer.Write(header);writer.Write((uint)0);
                foreach(var g in groups) {
                    using var vox=new Voxels(lib,new CompactField(g,h));Check(!vox.bIsEmpty(),"Empty compact field: "+g.part_id);
                    vdb.nAdd(vox,g.part_id);using var mesh=vox.mshAsMesh();var written=WriteMesh(writer,mesh,count);
                    observations.Add(new{g.part_id,role="metal",triangle_start=count,triangle_count=written.kept,removed_exact_zero_faces=written.removed});count+=written.kept;
                }
                writer.Seek(80,SeekOrigin.Begin);writer.Write((uint)count);vdb.SaveToFile(source);
            }
            using(var check=new OpenVdbFile(lib,source))foreach(var g in groups){using var vox=check.voxGet(g.part_id);Check(!vox.bIsEmpty(),"VDB roundtrip lost group");}
            Check(lib.nTotalMemUsage()==before,"Native allocation leak");
            output.WriteLine(JsonSerializer.Serialize(new{ok=true,backend="picogk",qualification="NOT_PERFORMED",recipe_sha256=recipe.GetProperty("recipe_sha256").GetString(),
                voxel_m=lib.fVoxelSize/1000.0,triangle_count=count,parts=observations,file_unit="m",scope="Approximate native implicit mesh; no exact STEP, feature coverage or physical acceptance"}));return 0;
        } catch(Exception error) {output.WriteLine(JsonSerializer.Serialize(new{ok=false,error=error.Message,qualification="NOT_PERFORMED"}));return 1;}
    }
}
