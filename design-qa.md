# COSMOS mechanical 3D workspace — design QA

Date: 2026-10-22

final result: passed

## Comparison contract

- Source visual truth: `/Users/vaibhavkumarn/Desktop/Mechanical-ui-image__2_.png`.
- User intent: use the BricsCAD screenshot as **inspiration and development reference**, not a branded or pixel-identical clone. Adapt it to the existing COSMOS scientific application and real retained engine geometry.
- Rendered implementation: `http://localhost:8896/app/workbench/native-geometry?project=bb7ebea6-15f9-43b8-b6c0-fd2a2d358155`.
- Final implementation screenshot: `output/cad-workspace-2026-10-22/10-final-current-cad.png`.
- State: expanded workspace, Assembly ribbon, dimetric/orthographic projection, real 16-body retained engine assembly, illustrative exploded layout, source-origin world axes, orientation widget, display-only colours. No project edits or engineering-material assignments.
- Source pixels: **2448 × 1020**; source CSS size/device density is unknown because this is a supplied image.
- Implementation pixels and CSS viewport: **1280 × 720**. Docked workspace widths separately exercised: **677 px and 541 px**.
- Normalization: compared corresponding application regions and proportions at a common visual width, without stretching either image. The source's wider aspect ratio, OS/title chrome, mechanical subject, vendor branding and larger command catalogue are intentional differences. No pixel/fidelity percentage is asserted.

## Full-view and focused evidence

The supplied source and final browser screenshot were opened together in the same comparison input. The comparison checked the top title/tab/ribbon bands, canvas proportions, left tool rail, per-part colour/edge readability and visible axes. Screenshot `06-tree-properties-colour.png` additionally covers linked selection, tree and properties; `07-docked-responsive.png` and `08-narrow-541px-properties.png` cover embedded layouts.

Focused review used the readable top 166 px ribbon region, lower-left orientation widget and the selected part/property region in the full-resolution captures. Separate crops were unnecessary: command labels, axis signs, selected outlines and property units were legible in these captures.

## Findings and comparison history

1. **[P2, resolved] First rendering underused the canvas and clipped the final ribbon group.**
   Evidence: `qa-01-before-fit-and-ribbon.png`.
   Fix: projected-bounds fit rather than bounding-sphere fit, and vertically stacked camera selectors to reduce ribbon width.
   Post-fix comparison: `qa-02-fit-and-ribbon.png`; final dimetric exploded composition in `10-final-current-cad.png` occupies the canvas without clipping the model. Camera/background controls are visible at the tested desktop width.
2. **[P2, resolved] Axis buttons could coincide at a principal-view pole.**
   Fix: deterministic label separation while retaining signed world-axis identities. All six signed axis buttons were exercised sequentially in the browser; coincident pole placement has an automated regression test.
3. **[P2, resolved] Two docked panels could consume a narrow embedded canvas.**
   Fix: workspace-width container queries, one active side panel below 900 px, and overlay properties below 600 px. Browser evidence at 677 px and 541 px showed no horizontal page overflow; narrow properties were observed as an absolute overlay. Temporary shell navigation resizing was restored to its original **224 px**.
4. **[P3, non-blocking] Exact vendor toolbar density and gear imagery are not replicated.**
   The implementation only exposes functioning COSMOS display commands. Sketch/solid modelling, constraints and BOM functions from the inspiration are not fabricated as decorative controls. The reference's raster subject is replaced with real source-bound 3D engine geometry.

No actionable P0/P1/P2 finding remains in the tested states.

## Required fidelity surfaces

| Surface | Review result |
| --- | --- |
| Fonts / typography | Compact system UI font with Segoe UI fallback, 10–12 px ribbon/metadata, clear document/tab/command hierarchy. Deliberately native on macOS rather than downloading a Windows typeface. No branding/font-parity claim. |
| Spacing / layout | Title, tabs and grouped ribbon above a dominant canvas; thin rail; optional model browser and properties; low-radius CAD-style surfaces. Desktop and two embedded widths checked. |
| Colours / tokens | Scoped charcoal chrome, neutral graphite canvas, active blue tabs, amber selected-part edges; red X, green Y, blue Z with textual labels. Dark badges keep axis letters readable on the grey background. Light/dark canvas choices remain available. |
| Image / assets | Live Three.js geometry, not a flattened screenshot. 21 unmodified official Tabler v3.44.0 SVG icons, stored locally with MIT licence. No generated image assets, placeholder mechanical imagery or copied BricsCAD marks. |
| Copy / content | Only implemented display actions appear. Source job identity, real part IDs, source-preview extents in mm, SI world/grid information and display-only/metrology limits remain visible or contextual. Signed-axis controls say “View from … toward pivot” to avoid direction ambiguity. |

## Interaction and accessibility checks

- Ribbon View / Assembly / Inspect / Appearance navigation, including arrow-key tab selection.
- All six signed world-axis view buttons, camera-linked orientation labels and source-origin axes.
- World grid, declared plane/spacing, selection highlighting and background choices.
- Model-browser filtering without hiding source geometry; part selection linked to the properties panel; per-part colour application.
- Explode/reassemble, section/clear section, all eight existing visual styles; navigation mode switching.
- Existing unit/scene coverage includes auxiliary/detail/broken views and original-source vertex picking.
- Expanded modal background inert; forward/reverse focus wrapping and Escape restoration.
- SVG icon loading and browser console: **no warnings or errors** in this campaign.
- **466 JavaScript tests passed**, including 27 focused viewer/CAD tests. **15 HTTP tests passed, 2 explicit native-campaign tests skipped**.
- Reused fixture previews refresh the ribbon's source-job identity only after an exact nonstale load; the final source-identity regression test is included above. This has no visual change to the captured component-job state.

## Remaining test boundaries

Formal human usability, VoiceOver, high-contrast certification and a broad macOS/device matrix have not been performed. They are not claimed by this visual/internal QA pass. No fresh native CAD kernel campaign, hardware validation, structural qualification or production readiness is implied. The previously reported incomplete temporary OCP environment was not changed by this workspace task.

## Implementation checklist

- [x] Reference-inspired application chrome and functional ribbon.
- [x] Native world-origin axes and signed, camera-linked XYZ orientation control.
- [x] Linked retained-body browser / canvas highlight / display properties.
- [x] Existing view/style/section/layout/appearance tools preserved.
- [x] Expanded and embedded responsive states checked and defects fixed.
- [x] Source and current implementation compared together after fixes.
- [x] Detailed implementation/test evidence retained inside the repository.

Follow-up polish: broader device and assistive-technology testing; no further visual redesign is required to hand off this scoped implementation.
