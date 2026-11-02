"""Source-bound unreleased engineering drawing layout, SVG and paginated PDF.

CAD edge projection is supplied by the isolated OCCT worker, never screenshots.
Sheet units are millimetres; scale is explicit and oversize views are rejected.
No dimensions, tolerances, materials or release authority are invented here.
"""
from __future__ import annotations

import html
import io
import math


def layout(projected, metadata):
    denominator = metadata["scale_denominator"]
    if not isinstance(denominator, (int, float)) or not math.isfinite(denominator) or not .1 <= denominator <= 1000:
        raise ValueError("Explicit1:N scale denominator0.1..1000 required")
    bounds = projected["bounds_m"]; low, high = bounds[:3], bounds[3:]
    # Third angle: top above front, right/end to its right. All views same scale.
    locations = ((110, 123, 184, 91, (0,1)), (110, 218, 184, 72, (0,2)), (268, 123, 108, 91, (2,1)))
    result = []
    for view, (cx,cy,w,h,axes) in zip(projected["views"], locations, strict=True):
        points = [p for line in view["lines"] for p in line["points_m"]]
        xmin, xmax = min(p[0] for p in points), max(p[0] for p in points)
        ymin, ymax = min(p[1] for p in points), max(p[1] for p in points)
        factor = 1000 / denominator
        if (xmax-xmin)*factor > w or (ymax-ymin)*factor > h:
            raise ValueError("Part does not fit A3 at the requested scale; explicitly choose a larger denominator")
        center = ((xmin+xmax)/2, (ymin+ymax)/2)
        transform = lambda p: (cx+(p[0]-center[0])*factor, cy+(p[1]-center[1])*factor)
        lines = [{"hidden": line["hidden"], "points": [transform(p) for p in line["points_m"]]} for line in view["lines"]]
        left, bottom = transform((xmin,ymin)); right, top = transform((xmax,ymax))
        result.append({"name": view["name"], "lines": lines, "label": (cx,cy-h/2-15),
                       "horizontal": (left,right,bottom-7,(high[axes[0]]-low[axes[0]])*1000),
                       "vertical": (bottom,top,left-7,(high[axes[1]]-low[axes[1]])*1000)})
    return result


def _sheet(projected, meta, draw, text, line, polyline):
    # Coordinates mm, origin bottom-left; PDF and SVG share this exact layout.
    line(8,8,412,8); line(412,8,412,289); line(412,289,8,289); line(8,289,8,8)
    text(12,281,"COSMOS | ENGINEERING DRAWING",4,True)
    text(408,281,"UNRELEASED - ENGINEERING REVIEW REQUIRED",3,True,"right")
    for view in layout(projected,meta):
        for item in sorted(view["lines"], key=lambda v:not v["hidden"]):
            polyline(item["points"],item["hidden"])
        text(*view["label"],view["name"],2.8,False,"center")
        x1,x2,y,length=view["horizontal"]
        line(x1,y,x2,y); line(x1,y-2,x1,y+3); line(x2,y-2,x2,y+3)
        text((x1+x2)/2,y-4,f"{length:.3f} mm ENVELOPE",2.5,False,"center")
        if view["name"] == "FRONT (XY)":
            y1,y2,x,length=view["vertical"]; line(x,y1,x,y2);line(x-2,y1,x+3,y1);line(x-2,y2,x+3,y2)
            text(view["label"][0],view["label"][1]-4,f"Y ENVELOPE {length:.3f} mm",2.4,False,"center")
    # Right-hand source/feature schedule avoids the three model viewports.
    text(331,263,"SOURCE / FEATURE SCHEDULE",3,True)
    text(331,257,"Canonical SI parameters; not mesh picks",2.4)
    parameters=meta["parameters"]
    for i,row in enumerate(parameters[:24]):
        text(331,250-i*5,row["name"] if len(row["name"])<=38 else row["name"][:35]+"...",2.2)
        text(408,247.8-i*5,f'{row["value"]:.9g} {row["unit"]}',2.2,False,"right")
    if len(parameters)>24:text(331,123,f"{len(parameters)-24} more parameters: PDF schedule",2.3,True)
    for i,value in enumerate(("THIRD-ANGLE PROJECTION | ALL VIEWS SAME SCALE", "Envelope dimensions from native BREP bounds.", "Feature schedule: resolved saved model nominals.", "No inferred fits, GD&T, surface finish or allowances.", f'Curve display deflection: {projected["curve_deflection_m"]*1000:.6g} mm.', "Do not scale printouts; use supplied values/CAD.")):
        text(12,77-i*4,value,2.5)
    # Title block. Explicit user declarations, with none silently filled in.
    line(8,49,412,49);line(8,34,412,34);line(8,20,412,20)
    text(12,43,meta["title"][:94],3.5,True)
    text(12,37,f'DWG {meta["number"]} | REV {meta["revision"]} | PART {projected["part_id"]}',2.5)
    text(12,28,f'Material: {meta["material"]} | Process: {meta["process"]}',2.6)
    text(12,23,f'Tolerances: {meta["tolerance_note"]}',2.6)
    text(12,15,f'Finish: {meta["finish_note"]} | Drawn by: {meta["author"]}',2.5)
    text(408,43,f'1:{meta["scale_denominator"]:g} | A3 | mm',3,True,"right")
    text(408,37,"SHEET1 | NOT APPROVED FOR MANUFACTURE",2.3,True,"right")
    text(12,3,f'Job {meta["job_id"]} | BREP {meta["source_sha256"][:20]} | Model {meta["model_commit_id"]}',2.0)


def svg(projected,metadata):
    views=layout(projected,metadata);items=[]
    def line(x1,y1,x2,y2):items.append(f'<line x1="{x1:.5f}" y1="{297-y1:.5f}" x2="{x2:.5f}" y2="{297-y2:.5f}" stroke="#222" stroke-width=".18"/>')
    def text(x,y,value,size=3,bold=False,anchor="left"):
        alignment={"left":"start","right":"end","center":"middle"}[anchor]
        items.append(f'<text x="{x:.5f}" y="{297-y:.5f}" font-family="Helvetica,Arial,sans-serif" font-size="{size}" font-weight="{"bold" if bold else "normal"}" text-anchor="{alignment}">{html.escape(str(value))}</text>')
    def polyline(points,hidden):
        coords=" ".join(f"{x:.5f},{297-y:.5f}" for x,y in points)
        items.append(f'<polyline points="{coords}" fill="none" stroke="{"#777" if hidden else "#111"}" stroke-width="{.13 if hidden else .22}"'+(' stroke-dasharray="1.8 1"' if hidden else '')+'/>')
    # Pass identical view records to retain the front-view vertical dimension.
    # _sheet computes its own equivalent layout; front is identified by its name.
    _sheet(projected,metadata,views,text,line,polyline)
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 420 297"><rect width="420" height="297" fill="white"/>'+''.join(items)+'</svg>').encode()


def pdf(projected,metadata):
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.lib.units import mm
    stream=io.BytesIO();c=Canvas(stream,pagesize=(420*mm,297*mm),pageCompression=1,invariant=1)
    c.setTitle(metadata["title"]);c.setAuthor(metadata["author"])
    def text(x,y,value,size=3,bold=False,anchor="left"):
        c.setFillColorRGB(0,0,0);c.setFont("Helvetica-Bold" if bold else "Helvetica",size*mm)
        getattr(c,{"left":"drawString","right":"drawRightString","center":"drawCentredString"}[anchor])(x*mm,y*mm,str(value))
    def line(x1,y1,x2,y2):c.setDash();c.setStrokeColorRGB(.1,.1,.1);c.setLineWidth(.18*mm);c.line(x1*mm,y1*mm,x2*mm,y2*mm)
    def polyline(points,hidden):
        c.setDash([1.8*mm,1*mm] if hidden else []);c.setLineWidth((.13 if hidden else .22)*mm);c.setStrokeColorRGB(*((.45,)*3 if hidden else (0.,)*3));p=c.beginPath();p.moveTo(points[0][0]*mm,points[0][1]*mm)
        for x,y in points[1:]:p.lineTo(x*mm,y*mm)
        c.drawPath(p,stroke=1,fill=0)
    _sheet(projected,metadata,layout(projected,metadata),text,line,polyline);c.showPage()
    remaining=[p for p in metadata["parameters"][:24] if len(p["name"])>38]+metadata["parameters"][24:]
    for start in range(0,len(remaining),40):
        text(12,282,"COSMOS | RESOLVED FEATURE PARAMETER SCHEDULE",4,True);text(12,274,"UNRELEASED - ENGINEERING REVIEW REQUIRED",3,True)
        text(12,266,f'{metadata["number"]} / {metadata["revision"]} | Part {projected["part_id"]}',3)
        for i,row in enumerate(remaining[start:start+40]):
            text(15,255-i*5.3,row["name"],2.8);text(390,255-i*5.3,f'{row["value"]:.12g} {row["unit"]}',2.8,False,"right")
        text(12,12,f'Job {metadata["job_id"]} | Model {metadata["model_commit_id"]}',2.3);text(402,12,f'SHEET{2+start//40}',2.5,False,"right");c.showPage()
    c.save();return stream.getvalue()
