# Engine reference review and proposed redesign direction

28 October 2026. **Research intake and proposal only. R08 remains on hold.**
No production source, owner project, engine baseline, runtime profile or prior
qualification receipt was modified. No native generation, cleanup, migration,
commit, push, manufacturing or hot-fire action was performed.

## 1. What was actually reviewed

The exact library directory is `/Users/vaibhavkumarn/Desktop/COSMOS/materials `
(its name has a trailing space; it was not renamed).

- Complete `rg --files` visible inventory: **571 files, 255 PDFs**.
- PDF metadata reports **28,649 pages**, including repeated copies. This is
  not a claim that all those pages were read.
- All 255 PDFs received metadata/first-page text triage, with no parser errors.
  **28 first pages have fewer than 50 extracted characters**; this alone does
  not distinguish a blank cover from a scanned document.
- **47 byte-identical PDF groups, containing 52 extra copies**, were verified
  by SHA256 among same-size candidates. All copies remain intact; duplicates
  are not independent corroborating evidence.
- Keyword navigation was performed on 15 priority documents / 1,093 pages.
  Automated keyword hits are navigation, not scientific review.
- Selected relevant pages in **11 priority documents** were inspected, with
  full-page rendering of five selected pages/figures. The ledger below states
  exactly which parts support this brief.
- The 32.03-second supplied video was probed and five sampled frames inspected.
  They show a CAD assembly with external tubing, bolted interfaces and mount
  linkages. These sampled views are not hot-fire or performance evidence.
- Supplied image batches were reviewed visually. Not every image's creator,
  engine identity, operating envelope or test history could be established.
- Spreadsheets, `.pages`/office notes, and the two native SolidWorks parts were
  inventoried, not evaluated as engineering inputs or imported into COSMOS.

Category file counts: notes 367; research papers 61; patents folder 43;
text books 38; REPORTS 17; RESEARCH WORK 14; PREBURNER 7; IMAGES 6;
CEA REPORTS 3; DESIGN OF TURBOPUMPS 3; root-level files 12.
These are folder classifications, not verified document genres. The patents
folder also contains technical reports, a NASA technology brief and an article.

Artifacts:

- [Complete inventory](/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1/docs/implementation/evidence/ENGINE_REFERENCE_REVIEW_2026-10-28/MATERIALS_INVENTORY.json)
- [Keyword navigation and selected-source checksums](/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1/docs/implementation/evidence/ENGINE_REFERENCE_REVIEW_2026-10-28/PRIORITY_PAGE_MAP.json)
- [Sampled CAD-animation views](/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1/docs/implementation/evidence/ENGINE_REFERENCE_REVIEW_2026-10-28/video-contact-sheet.jpg)

The original library's 571 inventoried file sizes and modification times were
rechecked after review: no changes observed. This is a metadata preservation
check, not a new full-library content checksum. The exact retained engine capture
still has SHA256 `58761b31a87a729cd207d6cbda6a1bf110771e3b3835e6355788a8504e5fbb86`.

## 2. Source-specific engineering lessons and limits

PDF page numbers below are one-based file pages, not necessarily printed pages.
Only the stated pages have been substantively reviewed here. Other text in the
page map may only have been machine-searched or first-page triaged.

| Source / selected pages | What it actually supports | Important limitation for COSMOS |
| --- | --- | --- |
| S1: Atyam/Nguyen, *Designing and Testing Liquid Engines for Additive Manufacturing*, PDF pp.9,15-16; p.9 visually checked | Removable injector for inspection; instrumentation integration; print-direction and channel-shape considerations. Reports powder blockage, pressure-measurement anomalies, misimpinging jets, hard-start damage, cracks and inlet-weld leakage. | A hot-fired engine is not automatically an efficient or qualified template. Spiral cooling was considered but rejected for the particular printing process. Their O-ring arrangement, dimensional compensation and kerosene tests are not cryogenic-methane seal/process approval. Do not transfer their proof-test procedure or margins. |
| S2: Wink et al., *Cryogenic rocket engine development at Delft aerospace rocket engineering*, PDF pp.5,12; p.5 visually checked | A methane cooling methodology with local property evaluation and variable channel geometry; explicit modeling limitations and planned development. | It describes preliminary work, not a completed validation of our engine. Its example uses different pressure, material and channel count. Do not copy its dimensions, coolant pressure, temperature limit or the number of channels into the 5-bar engine. |
| S3: Morgan C. Trent, NPS regenerative AM thesis, PDF p.89 (printed p.69) | Distinguishes measured heat-transfer test-spool results from an integrated printed chamber/nozzle that had **not yet been hot-fired**. | RP-1-based and different pressure/material conditions. Its 33 hot-fire tests are not 33 firings of the integrated chamber/nozzle and are not a methane validation dataset. |
| S4: Paul Gradl / NASA, *Advanced and Additive Manufacturing Technologies for Liquid Rocket Engine Components*, PDF pp.15,65; both visually checked | Manufacturing-process tradeoffs and different effects of coolant-side versus hot-wall roughness on pressure loss, heat transfer and fatigue. | A general process tutorial is not a selected machine/process capability, roughness value or material allowable. Increased roughness must not be treated as a free cooling improvement. |
| S5: NASA MFS-TOPS-93, PDF pp.1-2; p.1 visually checked | Integral channels/manifold manufacturing, explicit bimetal interface and composite-overwrap construction; identifies the tested chamber/overwrap assembly. | It is a technology-transfer brief, not a complete drawing set or qualification for our GRCop-42/IN718 pairing. No claim that all depicted stages/components or a COSMOS adaptation are qualified. |
| S6: Berksu Erkal, *Design of a Pintle Injector*, PDF pp.5,85 | Manifold/reservoir geometry affects spray uniformity; documented water/air cold-flow methods for a LOX/gaseous-methane intended application. | Cold-flow analogues, gaseous methane and different thrust/throttle requirements do not establish hot-fire suitability for our warmed-liquid/phase-dependent feed state. Do not adopt the thesis's tip angles or gaps by visual copying. |
| S7: Huzel/Huang, *Modern Engineering for Design of Liquid-Propellant Rocket Engines*, PDF pp.112-113,256-257 | Coupled thermal/structural channel sizing, injector/regen manifolding and channel-wall construction; service-condition dependence of fluid-control components and seals. | Worked examples use other propellants, materials, pressures and construction methods. The dynamic-valve seal examples are not a static injector-flange seal selection. No example wall, tube count, torque or allowable was installed. |
| S8: Bradford methane cooling document, PDF pp.14,24 | Table-of-figures and introductory context identify relevant thermal/structural/CFD topics. | This local file is a **24-page PREVIEW**. Its contents refer to results on later pages that are absent. No optimization result or validated numerical rule was extracted from missing pages. |
| S9: US20220205410A1, PDF pp.1,7 | Describes an integrated combustor-head/turbopump architecture. | Not the present pressure-fed cycle. Do not adopt a turbopump or alternating fuel/oxidizer cooling scheme merely because its manifold illustrations look integrated. No claim/legal-status review performed. |
| S10: US20200400102A1, PDF p.1 | Describes staged-combustion integration of a turbopump/preburner with a chamber. | Outside the agreed pressure-fed design. Classified as background, not a component template or authorization to change cycles. |
| S11: US8177489, PDF p.6 | Turbopump/inducer feed-system integration concepts. | Outside the pressure-fed baseline. No claim of novelty, legal clearance, licensing permission or freedom to operate. |

The source file `research papers/20110008540.pdf` was also checked in first-page
triage: it is about MATLAB data processing/visualization, not the rocket
manufacturing paper its numerical filename might suggest. Bibliographic
identity must come from contents, not file naming.

`research papers/liquid rocket engine self cooled .pdf` has 126 pages but the
text-navigation pass found no relevant extracted text. It remains a scanned/
text-layer-limited source requiring selected visual/OCR review; zero keyword
hits are not evidence of irrelevance. No bulk OCR or full-text library export
was performed.

### Exact local source links

- [S1 Atyam/Nguyen](</Users/vaibhavkumarn/Desktop/COSMOS/materials /research papers/Designing+and+Testing+Liquid+Engines+for+Additive+Manufacturing.pdf>)
- [S2 DARE cryogenic development](</Users/vaibhavkumarn/Desktop/COSMOS/materials /research papers/cryogenic engine development at deflt university.pdf>)
- [S3 Trent thesis](</Users/vaibhavkumarn/Desktop/COSMOS/materials /research papers/DESIGN OF A REGENERATIVELY COOLED BI-PROPELLANT ROCKET ENGINE USING ADDITIVE MANUFACTURING.pdf>)
- [S4 NASA/Gradl AM training](</Users/vaibhavkumarn/Desktop/COSMOS/materials /research papers/AIAA LRE Manufacturing Training Charts 7-30-2020.pdf>)
- [S5 NASA one-piece technology brief](</Users/vaibhavkumarn/Desktop/COSMOS/materials /patents /MFS-TOPS-93.pdf>)
- [S6 Pintle thesis](</Users/vaibhavkumarn/Desktop/COSMOS/materials /RESEARCH WORK/pintle injector design .pdf>)
- [S7 Huzel/Huang](</Users/vaibhavkumarn/Desktop/COSMOS/materials /text books /MODERN_ENGINEERING_FOR_DESIGN_OF_LIQUID.pdf>)
- [S8 Bradford preview](</Users/vaibhavkumarn/Desktop/COSMOS/materials /research papers/DESIGN AND CFD OPTIMIZATION OF METHANE REGENERATIVE COOLED ROCKET NOZZLES.pdf>)
- [S9 Integrated head/turbopump disclosure](</Users/vaibhavkumarn/Desktop/COSMOS/materials /patents /US20220205410A1.pdf>)
- [S10 Staged-combustion disclosure](</Users/vaibhavkumarn/Desktop/COSMOS/materials /patents /US20200400102A1.pdf>)
- [S11 Turbopump disclosure](</Users/vaibhavkumarn/Desktop/COSMOS/materials /patents /US8177489.pdf>)

## 3. What the supplied images do and do not establish

These are **visible-feature observations**, not reconstructed engineering data.
There is no reliable dimensional scale, complete section/drawing, roughness,
material certificate, injector specification or operating condition attached to
most images. Copper color is not an alloy identification. A cutaway/rendered
lattice is not proof of coolant flow, load capacity, manufacturability or a test.

| Reference family | Supplied files | Visible design ideas worth comparing | Do not infer |
| --- | --- | --- | --- |
| Compact CAD assembly / mounting | `this-is-a-small-liquid-rocket-engine-that-i-have-been-v0-YfDr_4AVJptk-2Nh6zNwNkkL7bQ_VVzbe9cPzlNEB_I.webp`, `m2-res_1080p.mp4`, `hqdefault.jpg` | Organized external routing, distinguishable removable interfaces and mount linkages | Demonstrated gimbal performance, a need for a gimbal in our static configuration, or hot-fire success from the animation |
| Instrumented demonstrator | `Thrust_Chamber_demonstrator_pillars.jpg` | Dedicated measurement bosses, accessible feed interfaces, removable head | That the prominent adapter stack is the required flight configuration or a directly coupled regen return circuit |
| Compact smooth body and modular head | `dare.webp`, `WhatsApp_Image_2025-06-03_at_14.50.webp`, `images (10).jpeg`, `images (11).jpeg`, `images (12).jpeg` | Compact collector locations, smooth external transitions, service access, sensor bosses and shorter routing | Actual hidden channel shape, propellant state, seal type or efficiency |
| Copper-toned integrated bodies / exposed channels | `images (3).jpeg` through `images (9).jpeg`, `images.jpeg` | Channel routing alternatives, local ribs/bosses, integrated inlet features, cutaway inspection views | That every rib is structural, every visible spiral is a coolant passage, or these geometries are optimal at 1.5 kN / 5 bar |
| Large integrated head / chamber | `image_52.webp`, `images (2).jpeg`, `leap71-starship-cover.jpeg` | Clearly separated internal distributions and interfaces; functional integration | Direct scaling of large-engine injector patterns, flange mass, nozzle expansion or pump-cycle architecture |
| Multi-material cutaway | `Fraunhofer-develops-multi-metal-3D-printing-01-640x400.jpg` | Explicit liner/support-region distinction and internal-channel visualization | Qualified GRCop-42/IN718 bond, or that a cutaway demonstrator is a hot-fired engine |
| Lattice/isogrid nozzle studies | `images (1).jpeg`, `betatype_ntopology_nozzle-03-cb-12c72f805bd574dd749bb1e113448f96.jpg`, `Betatype_NTopology_Nozzle-04-1-e1564664866120.jpg` | Conformal ribbing / potential weight studies with explicit structural objectives | A hot-fire record, coolant-circuit continuity, superior Isp, acceptable pressure loss or demonstrated printability for our process |

All listed supplied assets are in `/Users/vaibhavkumarn/Desktop/`. Some are
multiple views of the same apparent design, not independent examples.

### Primary-source cross-checks

- [ESA's 2019 demonstrator report](https://www.esa.int/Enabling_Support/Space_Transportation/3D-printed_storable-propellant_rocket_engine_design_tested)
  identifies a storable-propellant test demonstrator with an adapter that
  separates the cooling investigation from the propellant feed. Thus an
  instrumented test stack cannot simply be copied as our methalox feed layout.
- [Fraunhofer IGCV's MADE-3D page](https://www.igcv.fraunhofer.de/en/press_downloads/press_releases/research-project_made-3D_multi-material_3D-print.html)
  describes the reduced-scale multi-material cutaway as CW106C/1.2709. That is
  not our candidate material pair, and the page does not provide a transferred
  hot-fire acceptance for COSMOS.
- [nTop/Betatype's case-study account](https://resources.ntop.com/resources/blog/ntopology-and-betatype-a-partnership-story/)
  calls its illustrated object a rocket-nozzle **prototype**. The search result
  was accessible; direct article retrieval later returned 401. No unavailable
  underlying test report was assumed to exist or used for a performance claim.
- [LEAP 71's June 2024 test announcement](https://leap71.com/2024/06/18/leap-71-hot-fires-3d-printed-liquid-fuel-rocket-engine-designed-through-noyron-computational-model/)
  documents a kerosene/LOX example, not a matching methane case. It also reports
  cooling-channel pressure loss higher than modeled because of print roughness.
  Its feedback loop is useful methodology; its dimensions and qualification are
  not transferable. Do not generalize every supplied LEAP-related image to that
  tested configuration.
- [NASA's one-piece TCA record](https://technology.nasa.gov/patent/MFS-TOPS-93)
  supports studying manufacturing integration with explicit material/process
  interfaces. It supplies no COSMOS-specific material/process approval.

These sources are attributable organizational reports, not an independent
certification of COSMOS or exhaustive identification of all supplied photos.

## 4. Actual COSMOS implementation gaps relevant to this redesign

Comparison anchor: retained 24 October capture, saved model commit
`06f920dc-ff93-4aa3-8c74-a08c43f2bac3`; 16 metal outputs. This review did not query
or promote a different latest live-project revision.

| Evidence path | Implemented today in the inspected source | Gap for the proposed reference-inspired redesign |
| --- | --- | --- |
| `systems/geometry/component_model.py:31`, cooling branch | Typed profiles, bounded straight/elbow pipes, several injector patterns, annular manifolds, flanges and grooves; axial-sector channels with count limited to 3-16 | No corresponding typed helical/variable-section cooling-path operation, general continuous curved return pipe, filleted collector blend or explicitly assigned liner/jacket regions in this captured model |
| `plugins/geometry/workers/component_worker.py:103` | Revolves source profile segments; channel sector tools follow the declared wall profile | A rounded render is not a true smooth surface definition. New smooth profiles/sweeps/blends need contracts, native construction, independent references and semantics |
| `plugins/geometry/pico_components.py` | PicoGK fields derive from the same typed intent, with a distinct graph identity | PicoGK does not invent new physical design logic or make an unsupported feature valid. New geometry must be represented honestly and compared without pretending STL is exact STEP |
| `systems/geometry/component_cooling.py:20-26,84` | Actual annular-sector geometry handoff and explicit limits | It expressly rejects automatic sector-to-rectangular thermal mapping. It is not a complete routing/manifold/distribution/phase-change/thermal/structural solution. Other thermal/feed modules do not erase this specific geometry-match gap |
| `docs/implementation/evidence/ENGINE_WORKFLOW_REPAIR_2026-10-21/INTEGRAL_COLLECTOR_JACKET_CONCEPT.md` | Retained diagnostic reports a valid joined collector/body and connected source coolant void | The diagnostic is explicitly unqualified and is not a production union operation. It does not establish normal wall minima, printability, material bonding or full engine wet-domain acceptance |
| `output/picogk-components-2026-10-24/final-generation-evidence/summary.json` | Six-channel illustrative body, separate headers/head/plate and nine separately generated return-path pieces in the 16-output assembly | Separate CAD pieces are not necessarily nine real fittings or joints. A lower-part-count route needs explicit geometry, end interfaces and losses, not just a visual fuse |
| `docs/implementation/evidence/R08_ENGINE_PROPOSAL_2026-10-28/PROVISIONAL_PLAN.md` | Source-bound draft tolerances/coverage, no approval installed | New geometry creates new qualification scope. Historical receipts cannot be relabeled to accept it; R08 remains paused until the user resumes it |

Frozen module layering remains unchanged: calculations/intent in existing
scientific and systems layers, geometry construction in native plugins, bounded
execution in infrastructure, orchestration/API/UI separate. No kernel or
architecture replacement is proposed.

## 5. Recommended new design direction - for discussion, not installed

**Compact regenerative thrust chamber with integrated collectors, a removable
injector head, and a continuous, inspectable return route.**

Keep the requested 1.5 kN, sea-level static, methane/LOX, 5 bar absolute,
pressure-fed design requirements unless the user changes them. Keep the agreed
fuel route: tank feed into a nozzle-end coolant inlet, flow through the cooling
body to the collector below the chamber flange, then fuel delivery to its
injector manifold. LOX is fed directly to its **separate** injector manifold.
Fuel and oxidizer wet domains remain isolated until the intended discharge/
mixing region. No preburner, turbopump, gimbal or new cycle is silently added.

1. **Body/collectors:** investigate integrated nozzle-end and upper collectors
   with smooth, inspectable transitions. Preserve real coolant openings and
   explicit pressure/material boundaries. A fused metal model is not a
   metallurgical bond or a pressure-qualified part.
2. **Cooling:** first support an explicit variable-section axial-channel family
   matched to the actual wall/curvature; compare a bounded helical family only
   as a separate candidate. Channel count, twist, width, depth and wall/roof
   thickness must come from coupled sizing and manufacturing limits, not image
   aesthetics. No universal claim that spiral channels cool better.
3. **Return line:** investigate one smoothly routed body with named end
   interfaces instead of the current multi-piece source decomposition. Compare
   actual path length, bend curvature, access, thermal movement and pressure
   loss. Keep the outlet below the chamber flange as requested.
4. **Injector head:** use a compact serviceable head with separated plenums,
   inspectable metering passages and a stated injector concept. An injector
   family switch needs matching performance/flow assumptions; a familiar shape
   is not a complete atomization/stability model.
5. **Assembly:** keep continuous sealing/machining lands, accessible fasteners
   and a real load path. Resolve supplier-specific seals and compatible service
   conditions separately. Do not transfer elastomer glands from a kerosene
   engine or qualify a nominal groove envelope by appearance.
6. **Material regions:** retain GRCop-42 / IN718 as the already approved research
   basis only. Define distinct liner/support/jacket regions and the joining/
   interface hypothesis before applying different property sets. A one-metal
   Boolean cannot be treated as two qualified materials.
7. **Instrumentation/manufacturing:** reserve selected pressure/temperature
   bosses, machining access and cleaning/inspection paths. Evaluate the proposed
   printing direction, closed-channel downskin/supports and powder evacuation.
   Access is not proved by one connected mathematical void.
8. **Ribs/lattices:** defer optional external lightweighting until actual load,
   fatigue, minimum-feature and process objectives exist. Do not add a porous
   pressure boundary or decorative lattice to imitate a render.

The removable-head direction is a recommendation. The user has not yet selected
which reference family or new detailed layout to adopt. The previous baseline
is preserved for traceability; it is not a constraint preventing a real redesign.

## 6. What “more efficient” must mean before comparison

Do not declare a performance improvement from reduced part count or a cleaner
silhouette. Establish comparable operating conditions and explicit objectives:

- Delivered thrust/Isp and combustion assumptions at the same design point.
- Full feed/cooling/injector pressure demand, per-channel distribution and losses.
- Matched coolant phase/property limits, wall temperature and structural margins
  with the selected process-specific material basis.
- Assembly mass/envelope, interface/joint count, access and thermal accommodation.
- Manufacturing/post-processing/inspection feasibility and cost estimates with
  an actual process basis, not a universal minimum feature or angle.

No numeric efficiency gain, acceptable thickness, new seal, material allowable,
machine setting, burn procedure or manufacturing drawing is approved here.

## 7. Scoped development sequence after the layout direction is agreed

1. Record the chosen configuration and comparison objectives in a new versioned
   design brief. Preserve prior source hashes and receipts; do not overwrite the
   owner's current engine immediately from a photo.
2. Extend only the needed typed geometry operations: smooth contour/path intent,
   variable cross sections, integrated collector topology, explicit metal/wet
   domains, material regions and mating-port identities. Unsupported features
   fail explicitly. Preserve frozen architecture and existing operations.
3. Add deterministic small geometry/reference tests and lightweight cutaway/
   assembly previews. A preview is not a native-solid acceptance or a tolerance
   campaign. No large native build is authorized by this research intake.
4. Map the same actual geometry into thermal/feed/operating calculations: real
   lengths, wetted perimeter/area, normal walls, roughness and curvature losses,
   channel distribution and property/phase limits. No rectangular substitute for
   a different generated passage or unchanged analysis under a new CAD shape.
5. Develop process/interface checks and review the candidate against the original
   requirements before making it the new design baseline.
6. Native builds and R08 qualification are separate steps gated by available
   storage and the user's explicit resumption. New geometry requires new exact
   evidence. Physical validation, manufacturing release and hot-fire approval
   remain separate and require genuine applicable evidence/review.

## 8. Readiness and next user choice

Research-intake status: **COMPLETE FOR THIS BOUNDED REVIEW**. Whole-library
scientific review: **NOT COMPLETE**. Redesign implementation: **NOT STARTED**.
R08: **ON HOLD**. No source/library or saved engine data changed.

Recommended next choice: confirm whether the **compact integrated cooling body
with removable injector head** is the preferred configuration, or identify a
different supplied reference as the primary layout. Internal channel style,
material-region/joining approach, seal selection and final dimensions remain
explicit design decisions, not inferred from images.

This report is a design-research proposal, not a complete engine design,
independent engineering acceptance, patent clearance or hardware readiness claim.
