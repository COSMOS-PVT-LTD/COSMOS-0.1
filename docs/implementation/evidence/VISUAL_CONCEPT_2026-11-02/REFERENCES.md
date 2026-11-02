# Visual discussion reference index

The artwork in COSMOS is a fixed, unitless illustration. It uses disconnected
outer surfaces and decorative markers. It does not reproduce internal geometry,
fuel paths, fasteners, fittings, seals, measurements or manufacturing details.
The source pictures are retained where the user supplied them; none is copied into
the application. Names below identify local files, not proven design performance.

## User sketches

Directory: `/Users/vaibhavkumarn/Downloads/`

| File | Visible subject |
| --- | --- |
| `WhatsApp Image 2026-11-02 at 2.34.51 PM.jpeg` | Longitudinal hand-drawn assembly and annotations. |
| `WhatsApp Image 2026-11-02 at 2.34.51 PM (1).jpeg` | Enlarged upper assembly sketch. |
| `WhatsApp Image 2026-11-02 at 2.34.51 PM (2).jpeg` | Enlarged lower silhouette sketch. |
| `WhatsApp Image 2026-11-02 at 2.34.59 PM.jpeg` | Hand-drawn external top view. |
| `WhatsApp Image 2026-11-02 at 2.36.07 PM.jpeg` | Hand-drawn head view and notes. |

These drawings do not specify a scale for the artwork. The colored markers are
abstract decorations and are not models of ports, probes or fasteners.

## Other supplied images

Directory: `/Users/vaibhavkumarn/Desktop/COSMOS/materials /IMAGES/`

- Exterior silhouettes and assembly references: `dare.webp`, `hqdefault.jpg`,
  `images.jpeg`, `images (2).jpeg`, `images (10).jpeg`, `images (11).jpeg`,
  `images (12).jpeg`, `this-is-a-small-liquid-rocket-engine-that-i-have-been-v0-YfDr_4AVJptk-2Nh6zNwNkkL7bQ_VVzbe9cPzlNEB_I.webp`,
  `WhatsApp_Image_2025-06-03_at_14.50.webp` and
  `Thrust_Chamber_demonstrator_pillars.jpg`.
- Visible exterior textures and shapes: `images (3).jpeg`, `images (4).jpeg`,
  `images (5).jpeg`, `images (6).jpeg`, `images (7).jpeg`, `images (8).jpeg`,
  `images (9).jpeg`,
  `betatype_ntopology_nozzle-03-cb-12c72f805bd574dd749bb1e113448f96.jpg` and
  `Betatype_NTopology_Nozzle-04-1-e1564664866120.jpg`.
- Cutaway/reference illustration: `images (1).jpeg`, `tyz3g2iklef21.jpg`,
  `olms0692ji941.jpg`, `image_52.webp` and `leap71-starship-cover.jpeg`.
- Video supplied for reference: `m2-res_1080p.mp4`. No frame-by-frame video
  analysis was performed for this small exterior illustration.

Two additional photographs are on the Desktop:
`3D-Printed-Liquid-Rocket-Chamber-Injector-Head-1024x683.jpg` and
`120275343_2778462775723895_1786129063969936135_o.jpg`.

Image descriptions are visual groupings only. Internal operation, origin,
material and performance cannot be established from appearance alone.

## Generation and scope

`scripts/build_visual_concept.py` generates the fixed artifact from open OCCT
surface triangulations and a fixed PicoGK decorative marker. The application loads
the pre-generated artwork, so normal viewing does not invoke either kernel. It
contains no exposed geometry parameters, export action, scientific calculations,
material definition or project persistence. No existing baseline is changed.
