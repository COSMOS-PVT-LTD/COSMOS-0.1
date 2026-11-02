"""Kernel-independent component integrals and explicitly labelled CSG residuals."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from itertools import pairwise

import numpy as np

from systems.geometry.component_model import ComponentPlan, Part


def ring_integrals(profile, power=2):
    total, moment = [], []
    for (x, ri, ro), (end, ei, eo) in pairwise(profile):
        length = end-x
        coefficients = [math.comb(power,k)*(ro**(power-k)*((eo-ro)/length)**k-ri**(power-k)*((ei-ri)/length)**k) for k in range(power+1)]
        integral = math.fsum(a*length**(k+1)/(k+1) for k,a in enumerate(coefficients))
        total.append(integral)
        moment.append(x*integral+math.fsum(a*length**(k+2)/(k+2) for k,a in enumerate(coefficients)))
    return math.fsum(total), math.fsum(moment)


def meridian_residual(profile, data):
    """Exact signed Euclidean meridian distance before sector/Boolean composition."""
    data = np.asarray(data,dtype=float).reshape(-1,3)
    radial = np.hypot(data[:,1],data[:,2])
    points = np.column_stack((data[:,0],radial))
    inner = np.array([(x,ri) for x,ri,_ in profile])
    outer = np.array([(x,ro) for x,_,ro in profile])
    edges = list(pairwise(outer)) + [(inner[0],outer[0]),(inner[-1],outer[-1])]
    if np.any(inner[:,1] > 0):
        edges += list(pairwise(inner))
    distance = np.full(len(data),np.inf)
    for a,b in edges:
        delta = b-a
        alpha = np.clip(np.sum((points-a)*delta,axis=1)/float(delta@delta),0,1)
        distance = np.minimum(distance,np.linalg.norm(points-a-alpha[:,None]*delta,axis=1))
    inside = ((data[:,0]>=inner[0,0]) & (data[:,0]<=inner[-1,0])
              & (radial>=np.interp(data[:,0],inner[:,0],inner[:,1])) & (radial<=np.interp(data[:,0],outer[:,0],outer[:,1])))
    return np.where(inside,-distance,distance)


def wedge_residual(data, phase, width):
    angle = phase+width/2
    forward = data[:,1]*math.cos(angle)+data[:,2]*math.sin(angle)
    side = -data[:,1]*math.sin(angle)+data[:,2]*math.cos(angle)
    return np.abs(side)*math.cos(width/2)-forward*math.sin(width/2)


@dataclass(frozen=True)
class PartReference:
    plan: ComponentPlan
    part: Part

    @property
    def operation(self):
        return "component."+self.part.part_id

    @property
    def radius_m(self):
        if self.part.pipe:
            return self.part.pipe.outer_radius
        return min(ro for _,_,ro in self.part.profile)

    def local_integrals(self):
        part = self.part
        if part.pipe and part.pipe.bend_radius is not None:
            pipe = part.pipe; radius = pipe.bend_radius; angle = pipe.angle_rad
            assert angle is not None
            area = math.pi*(pipe.outer_radius**2-pipe.bore_radius**2)
            volume = area*radius*angle
            moment_factor = area*(radius**2+(pipe.outer_radius**2+pipe.bore_radius**2)/4)
            return volume, np.array([moment_factor*(1-math.cos(angle)), radius*volume-moment_factor*math.sin(angle), 0.])
        area, axial = ring_integrals(part.profile)
        factor = math.pi if part.sector is None else part.sector[1]/2
        volume = area*factor
        moment = np.array([axial*factor,0.,0.])
        if part.sector:
            phase,width = part.sector
            radial,_ = ring_integrals(part.profile,3)
            moment[1:] = np.array([math.sin(phase+width)-math.sin(phase),math.cos(phase)-math.cos(phase+width)])*radial/3
        for hole in part.holes:
            start,end = hole.axial_range or (part.profile[0][0],part.profile[-1][0])
            length = end-start
            removed = math.pi*hole.radius**2*length*math.sqrt(1+sum(v*v for v in hole.slope_yz))
            x = (start+end)/2
            centroid = np.r_[x,np.array(hole.center_yz)+x*np.array(hole.slope_yz)]
            volume -= removed
            moment -= removed*centroid
        for cavity in part.cavities:
            integral, axial = ring_integrals(cavity.profile)
            factor=math.pi if cavity.sector is None else cavity.sector[1]/2
            volume -= factor*integral
            moment[0] -= factor*axial
            if cavity.sector:
                phase,width=cavity.sector;radial,_=ring_integrals(cavity.profile,3)
                moment[1:]-=np.array([math.sin(phase+width)-math.sin(phase),math.cos(phase)-math.cos(phase+width)])*radial/3
        if part.cooling:
            c = part.cooling
            profile = tuple((x,ri+c.hot_ligament,ri+c.hot_ligament+c.depth) for x,ri,_ in part.profile)
            removed, axial = ring_integrals(profile)
            # Uniform azimuthal pattern cancels transverse moments analytically.
            fraction = c.count*c.width_rad/2
            volume -= removed*fraction
            moment[0] -= axial*fraction
        return volume,moment

    @property
    def volume_m3(self):
        return self.local_integrals()[0]

    @property
    def centroid_m(self):
        volume,moment = self.local_integrals()
        rotation,translation = self.plan.placement(self.part.frame_id)
        return rotation@(moment/volume)+translation

    @property
    def bounds_m(self):
        rotation,translation = self.plan.placement(self.part.frame_id)
        if self.part.pipe and self.part.pipe.bend_radius is not None:
            pipe = self.part.pipe; radius = pipe.bend_radius; angle = pipe.angle_rad
            assert angle is not None
            lows, highs = [], []
            for axis, row in enumerate(rotation):
                a, b, c = row[0], -row[1], row[2]
                critical = math.atan2(a, b)
                angles = [0., angle]+[critical+k*math.pi for k in range(-2, 3) if 0 <= critical+k*math.pi <= angle]
                values = [a*math.sin(phi)+b*math.cos(phi) for phi in angles]
                lower, upper = min(values), max(values)
                # Support of each circular cross-section. R>outer makes both
                # expressions monotone in the projected radial direction.
                lows.append(radius*(lower+row[1])-pipe.outer_radius*math.hypot(lower,c)+translation[axis])
                highs.append(radius*(upper+row[1])+pipe.outer_radius*math.hypot(upper,c)+translation[axis])
            return np.array(lows+highs)
        low,high = [],[]
        for axis in range(3):
            if self.part.sector is None:
                coefficient = math.hypot(rotation[axis,1],rotation[axis,2])
                low.append(min(rotation[axis,0]*x-coefficient*ro for x,_,ro in self.part.profile)+translation[axis])
                high.append(max(rotation[axis,0]*x+coefficient*ro for x,_,ro in self.part.profile)+translation[axis])
            else:
                phase,width = self.part.sector
                angles = [phase,phase+width]
                direction = math.atan2(rotation[axis,2],rotation[axis,1])
                angles += [direction+k*math.pi for k in range(-6,7) if phase<=direction+k*math.pi<=phase+width]
                values = [rotation[axis,0]*x+(rotation[axis,1]*math.cos(a)+rotation[axis,2]*math.sin(a))*r for x,ri,ro in self.part.profile for r in (ri,ro) for a in angles]
                low.append(min(values)+translation[axis]); high.append(max(values)+translation[axis])
        return np.array(low+high)

    def local(self,points):
        rotation,translation = self.plan.placement(self.part.frame_id)
        return (np.asarray(points,dtype=float).reshape(-1,3)-translation)@rotation

    def sdf(self,points):
        """CSG constraint residual, NOT general exact Euclidean/Hausdorff distance."""
        data = self.local(points)
        part = self.part
        if part.pipe and part.pipe.bend_radius is not None:
            pipe = part.pipe; radius = pipe.bend_radius; angle = pipe.angle_rad
            assert angle is not None
            tube = np.hypot(np.hypot(data[:,0], data[:,1]-radius)-radius, data[:,2])
            return np.maximum.reduce((tube-pipe.outer_radius, pipe.bore_radius-tube, -data[:,0],
                math.cos(angle)*data[:,0]+math.sin(angle)*data[:,1]-radius*math.sin(angle)))
        result = meridian_residual(part.profile,data)
        if part.sector:
            result = np.maximum(result,wedge_residual(data,*part.sector))
        for h in part.holes:
            direction = np.r_[1.,h.slope_yz]; direction /= np.linalg.norm(direction)
            delta = data-np.r_[0.,h.center_yz]
            cylinder = np.linalg.norm(delta-np.outer(delta@direction,direction),axis=1)-h.radius
            if h.axial_range is not None:
                # These cap bores open into a plenum/outside, not a blind cap.
                # Do not invent internal zero-residual disks at joined openings.
                a,b = h.axial_range
                # Rigid world->local subtraction can move a cap-plane point a
                # few ulps outside [a,b]. A strict comparison then invents a
                # metal disk across a real opening at the adjacent plenum cap.
                # Bound only this classification by transform roundoff; this
                # is not a physical/mesh QA tolerance or a changed cutter size.
                _,translation=self.plan.placement(part.frame_id)
                scale=max(abs(a),abs(b),float(np.abs(data[:,0]).max()),float(np.abs(translation).max()))
                roundoff=16*np.finfo(float).eps*scale
                cylinder = np.where((data[:,0]>=a-roundoff)&(data[:,0]<=b+roundoff),cylinder,np.inf)
            result = np.maximum(result,-cylinder)
        for cavity in part.cavities:
            constraint=meridian_residual(cavity.profile,data)
            if cavity.open_face:
                profile=np.array(cavity.profile);radial=np.hypot(data[:,1],data[:,2])
                constraint=np.maximum(profile[0,1]-radial,radial-profile[0,2])
                # Only the exterior end is open; the exact blind floor remains.
                plane=data[:,0]-profile[-1,0] if cavity.open_face=="start" else profile[0,0]-data[:,0]
                constraint=np.maximum(constraint,plane)
            elif cavity.open_passage:
                profile=np.array(cavity.profile);radial=np.hypot(data[:,1],data[:,2])
                low=np.interp(data[:,0],profile[:,0],profile[:,1]);high=np.interp(data[:,0],profile[:,0],profile[:,2])
                constraint=np.maximum(low-radial,radial-high)
                a,b=profile[0,0],profile[-1,0];_,translation=self.plan.placement(part.frame_id)
                scale=max(abs(a),abs(b),float(np.abs(data[:,0]).max()),float(np.abs(translation).max()))
                roundoff=16*np.finfo(float).eps*scale
                if cavity.sector:constraint=np.maximum(constraint,wedge_residual(data,*cavity.sector))
                constraint=np.where((data[:,0]>=a-roundoff)&(data[:,0]<=b+roundoff),constraint,np.inf)
            elif cavity.sector:
                constraint=np.maximum(constraint,wedge_residual(data,*cavity.sector))
            result = np.maximum(result,-constraint)
        if part.cooling:
            c = part.cooling
            # A through-channel has no retained metal cap at its inlet/outlet.
            # Including the cutter's coincident end-cap zero in a CSG residual
            # would falsely label the *open port interior* as a metal surface.
            profile=np.array(part.profile); radial=np.hypot(data[:,1],data[:,2])
            low=np.interp(data[:,0],profile[:,0],profile[:,1])+c.hot_ligament
            radial_constraint=np.maximum(low-radial,radial-low-c.depth)
            angular = np.min([wedge_residual(data,c.phase_rad+i*2*math.pi/c.count,c.width_rad) for i in range(c.count)],axis=0)
            channels = np.maximum(radial_constraint,angular)
            result = np.maximum(result,-channels)
        return result

    def surface_samples(self):
        part = self.part
        if part.pipe and part.pipe.bend_radius is not None:
            pipe = part.pipe; radius = pipe.bend_radius; angle = pipe.angle_rad
            assert angle is not None
            rows = []
            for phi in np.linspace(0.,angle,17):
                radii = np.linspace(pipe.bore_radius,pipe.outer_radius,5) if phi in (0.,angle) else (pipe.bore_radius,pipe.outer_radius)
                for r in radii:
                    for alpha in np.arange(24)*math.pi/12:
                        distance = radius+r*math.cos(alpha)
                        rows.append((distance*math.sin(phi), radius-distance*math.cos(phi), r*math.sin(alpha)))
            rotation,translation = self.plan.placement(part.frame_id)
            return np.array(rows)@rotation.T+translation
        original = np.array(part.profile)
        xs = sorted({x for x,_,_ in part.profile} | {(a[0]+b[0])/2 for a,b in pairwise(part.profile)})
        phase,width = part.sector if part.sector else (0.,2*math.pi)
        angles = np.linspace(phase,phase+width,9)[:-1] if part.sector is None else np.linspace(phase,phase+width,5)
        rows = []
        def point(x,r,a):
            rows.append((x,r*math.cos(a),r*math.sin(a)))
        for x in xs:
            ri,ro = np.interp(x,original[:,0],original[:,1]),np.interp(x,original[:,0],original[:,2])
            for r in ((ri,ro) if ri>0 else (ro,)):
                for a in angles: point(x,r,a)
            if part.sector:
                for a in (phase,phase+width): point(x,(ri+ro)/2,a)
            if part.cooling:
                c = part.cooling
                for i in range(c.count):
                    start = c.phase_rad+2*math.pi*i/c.count
                    for r in (ri+c.hot_ligament,ri+c.hot_ligament+c.depth): point(x,r,start+c.width_rad/2)
                    for a in (start,start+c.width_rad): point(x,ri+c.hot_ligament+c.depth/2,a)
        for x,ri,ro in (part.profile[0],part.profile[-1]):
            for r in np.linspace(ri,ro,5):
                for a in angles: point(x,r,a)
        for h in part.holes:
            axis = np.r_[1.,h.slope_yz]; axis /= np.linalg.norm(axis)
            first = np.cross(axis,[0.,0.,1.]); first /= np.linalg.norm(first)
            second = np.cross(axis,first)
            start,end = h.axial_range or (part.profile[0][0],part.profile[-1][0])
            for x in np.linspace(start,end,5):
                for a in np.arange(12)*math.pi/6:
                    offset = h.radius*(math.cos(a)*first+math.sin(a)*second)
                    t = (x-offset[0])/axis[0]
                    rows.append(tuple(np.r_[0.,h.center_yz]+axis*t+offset))
        for cavity in part.cavities:
            (begin,low,high),(end,_,_) = cavity.profile
            cavity_angles=angles if cavity.sector is None else np.linspace(cavity.sector[0],sum(cavity.sector),5)
            for x in (begin,(begin+end)/2,end):
                for r in (low,high):
                    for a in cavity_angles: point(x,r,a)
                if cavity.sector:
                    for a in (cavity.sector[0],sum(cavity.sector)):point(x,(low+high)/2,a)
            for x in (begin,end):
                for r in np.linspace(low,high,5):
                    for a in cavity_angles: point(x,r,a)
        rotation,translation = self.plan.placement(part.frame_id)
        world = np.array(rows)@rotation.T+translation
        # Exact source-surface membership roundoff filter, not a CAD tolerance.
        return world[np.abs(self.sdf(world))<=1e-12]

    def fluid_reference(self,index):
        c = self.part.cooling
        assert c is not None
        rows = tuple((x,ri+c.hot_ligament,ri+c.hot_ligament+c.depth) for x,ri,_ in self.part.profile)
        return PartReference(self.plan,replace(self.part,profile=rows,cooling=None,holes=(),sector=(c.phase_rad+2*math.pi*index/c.count,c.width_rad),role="coolant-fluid-domain"))


@dataclass(frozen=True)
class ComponentReference:
    plan: ComponentPlan
    worker_parts: tuple[dict, ...] = ()
    operation: str = "engine-components-v1"

    @property
    def radius_m(self):
        return min(PartReference(self.plan,p).radius_m for p in self.plan.parts)

    @property
    def volume_m3(self):
        return math.fsum(PartReference(self.plan,p).volume_m3 for p in self.plan.parts)

    @property
    def centroid_m(self):
        return sum((PartReference(self.plan,p).centroid_m*PartReference(self.plan,p).volume_m3 for p in self.plan.parts),np.zeros(3))/self.volume_m3

    def sdf(self,points):
        return np.min([PartReference(self.plan,p).sdf(points) for p in self.plan.parts],axis=0)

    def surface_samples(self):
        return np.vstack([PartReference(self.plan,p).surface_samples() for p in self.plan.parts])
