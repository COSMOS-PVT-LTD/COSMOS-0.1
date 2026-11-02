"""Read-only Gmsh mesh diagnostic; no healing, welding, export or QA authority."""
import argparse
import json


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("step");parser.add_argument("--circle-points",type=int)
    parser.add_argument("--per-body",action="store_true")
    parser.add_argument("--resolve-tubes",action="store_true")
    parser.add_argument("--resolve-cylinders",action="store_true")
    parser.add_argument("--minimum-cylinder-aspect",type=float,default=0.)
    args=parser.parse_args()
    import gmsh
    import numpy as np
    gmsh.initialize([],readConfigFiles=False)
    try:
        gmsh.option.setNumber("General.Terminal",0);gmsh.option.setNumber("General.NumThreads",1)
        gmsh.option.setString("Geometry.OCCTargetUnit","MM");gmsh.option.setNumber("Geometry.OCCAutoFix",0)
        gmsh.model.add("diagnostic");gmsh.model.occ.importShapes(args.step);gmsh.model.occ.synchronize()
        bounds=gmsh.model.getBoundingBox(-1,-1);size=max(bounds[i+3]-bounds[i] for i in range(3))/32
        gmsh.option.setNumber("Mesh.MeshSizeMin",size/2);gmsh.option.setNumber("Mesh.MeshSizeMax",size)
        if args.circle_points:gmsh.option.setNumber("Mesh.MinimumCirclePoints",args.circle_points)
        if args.resolve_tubes:
            sizes=[]
            for _,body in gmsh.model.getEntities(3):
                faces=gmsh.model.getBoundary([(3,body)],combined=False,oriented=False,recursive=False)
                cylinders=[abs(tag) for _,tag in faces if gmsh.model.getType(2,abs(tag))=="Cylinder"]
                planes=[tag for _,tag in faces if gmsh.model.getType(2,abs(tag))=="Plane"]
                if len(faces)!=4 or len(cylinders)!=2 or len(planes)!=2:continue
                radii=[]
                for face in cylinders:
                    low,high=gmsh.model.getParametrizationBounds(2,face)
                    uv=((np.array(low)+np.array(high))/2).tolist()
                    radii.append(1/float(np.max(np.abs(gmsh.model.getCurvature(2,face,uv)))))
                local=min(size,min(radii)/4);sizes.append(local)
                points=gmsh.model.getBoundary([(3,body)],combined=False,oriented=False,recursive=True)
                gmsh.model.mesh.setSize(list(set(points)),local)
            if sizes:gmsh.option.setNumber("Mesh.MeshSizeMin",min(size/2,min(sizes)/2))
        if args.resolve_cylinders:
            sizes={}
            for _,face in gmsh.model.getEntities(2):
                if gmsh.model.getType(2,face)!="Cylinder":continue
                low,high=gmsh.model.getParametrizationBounds(2,face)
                curvature=float(np.max(np.abs(gmsh.model.getCurvature(2,face,((np.array(low)+np.array(high))/2).tolist()))))
                derivative=gmsh.model.getDerivative(2,face,((np.array(low)+np.array(high))/2).tolist())
                length=(high[1]-low[1])*float(np.linalg.norm(derivative[3:]))
                if length*curvature/2<=args.minimum_cylinder_aspect:continue
                local=min(size,1/curvature/4)
                for point in gmsh.model.getBoundary([(2,face)],combined=False,oriented=False,recursive=True):
                    sizes[point]=min(sizes.get(point,size),local)
            for point,local in sizes.items():gmsh.model.mesh.setSize([point],local)
            if sizes:gmsh.option.setNumber("Mesh.MeshSizeMin",min(size/2,min(sizes.values())/2))
        if not args.per_body:gmsh.model.mesh.generate(2)
        tags,xyz,_=gmsh.model.mesh.getNodes();coordinates=dict(zip(tags,np.array(xyz).reshape(-1,3),strict=True))
        results=[]
        for _,body in gmsh.model.getEntities(3):
            if args.per_body:
                gmsh.model.mesh.clear()
                gmsh.model.setVisibility(gmsh.model.getEntities(),0,recursive=False)
                gmsh.model.setVisibility([(3,body)],1,recursive=True)
                gmsh.option.setNumber("Mesh.MeshOnlyVisible",1)
                gmsh.model.mesh.generate(2)
                tags,xyz,_=gmsh.model.mesh.getNodes();coordinates=dict(zip(tags,np.array(xyz).reshape(-1,3),strict=True))
            triangles=[]
            for _,face in gmsh.model.getBoundary([(3,body)],combined=False,oriented=False,recursive=False):
                types,_,nodes=gmsh.model.mesh.getElements(2,abs(face))
                assert list(types)==[2]
                triangles.extend(np.array(nodes[0]).reshape(-1,3).tolist())
            triangles=np.array(triangles,dtype=np.int64)
            directed=np.vstack((triangles[:,[0,1]],triangles[:,[1,2]],triangles[:,[2,0]]))
            edges,inverse,counts=np.unique(np.sort(directed,axis=1),axis=0,return_inverse=True,return_counts=True)
            orientation=np.bincount(inverse,weights=np.where(directed[:,0]<directed[:,1],1,-1))
            points=np.array([[coordinates[int(k)] for k in row] for row in triangles])
            degenerate=int((np.linalg.norm(np.cross(points[:,1]-points[:,0],points[:,2]-points[:,0]),axis=1)<1e-16).sum())
            results.append({"body":body,"centroid_mm":gmsh.model.occ.getCenterOfMass(3,body),"triangles":len(triangles),
                "euler":len(np.unique(triangles))-len(edges)+len(triangles),"nonmanifold":int((counts!=2).sum()),
                "orientation_errors":int((orientation!=0).sum()),"zero_area_triangles":degenerate,
                "repeated_node_triangles":int(((triangles[:,0]==triangles[:,1])|(triangles[:,1]==triangles[:,2])|(triangles[:,2]==triangles[:,0])).sum()),
                "bad_edges":[{"count":int(n),"coordinates_mm":[coordinates[int(v)].tolist() for v in edge]}
                    for edge,n in zip(edges,counts,strict=True) if n!=2][:4]})
        print(json.dumps({"circle_points":args.circle_points,"nodes":len(tags),"parts":results},indent=2))
    finally:gmsh.finalize()


if __name__=="__main__":main()
