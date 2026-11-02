const test=require('node:test');
const assert=require('node:assert/strict');
const ui=require('../../gui/static/component-geometry.js');
test('Revised stack lands and native blind grooves remain distinct from sealed joints',()=>{
 const text=ui.jointSummary({header_joints:[],mounting_stack_contacts:[{from_part:'head',to_part:'plate',matched_bolt_axes:Array(8),bolt_axes_complete:true,continuous_annular_lands_m:[{inner_radius_m:.0514288,outer_radius_m:.0818}]}],native_grooves:[{part_id:'plate',face:'start',depth_m:.00127}]});
 assert.match(text,/head → plate: 8 matching stack bolt axes/);assert.match(text,/51.429–81.800 mm radius/);
 assert.match(text,/1 native blind face grooves/);assert.match(text,/selected seal NOT_SUPPLIED/);assert.match(text,/service fit NOT_ASSESSED/);
});
test('Matching joint geometry and land widths never become seal or pressure acceptance',()=>{
 const text=ui.jointSummary({header_joints:[{header_part_id:'upper',gas_to_coolant_radial_land_m:.0015,header_bolt_bores:8,gland_geometry:'NOT_GENERATED',contacts:[{part_id:'collar',matched_bolt_axes:Array(8),mating_bolt_bores:8,bolt_axes_complete:true}]}]});
 assert.match(text,/1.500 mm/);assert.match(text,/8\/8 matching bolt axes/);assert.match(text,/GEOMETRY_MATCHED/);assert.match(text,/gland NOT_GENERATED/);assert.match(text,/not seal, bolt-strength or pressure acceptance/);
});
test('Aligned injector discharges with zero attachment land stay visibly incomplete',()=>{
 const text=ui.jointSummary({header_joints:[],injector_chamber_interfaces:[{injector_part_id:'plate',discharge_geometry_connected:true,wall_contacts:[{wall_part_id:'chamber',annular_face_overlap_width_m:0,face_attachment_geometry:'ZERO_ANNULAR_FACE_LAND'}]}]});
 assert.match(text,/discharge geometry ALIGNED/);assert.match(text,/land 0.000 mm/);assert.match(text,/ZERO_ANNULAR_FACE_LAND/);assert.match(text,/pressure attachment NOT_DESIGNED/);
});
test('Interface report does not conflate mating openings with pressure/seal closure',()=>{
 const text=ui.interfaceSummary({upstream_current:true,authority:{commit_id:'retained'},ports:[1,2],matches:[1],unconnected_ports:[],pressure_closure:'NOT_CALCULATED'});
 assert.match(text,/2 actual openings/);assert.match(text,/1 distributor\/plate geometry connections/);assert.match(text,/Engine solution: INCOMPLETE/);assert.match(text,/seals: NOT_ASSESSED/);
});
test('Pipe and circuit topology are distinct from distributor counts and engine acceptance',()=>{
 const text=ui.interfaceSummary({upstream_current:true,authority:{commit_id:'pipe-source'},ports:Array(90),matches:[{opening:'MATCHING_PIPE_CIRCLES'},{opening:'MATCHING_WORLD_ANNULAR_SECTORS'},{opening:'CIRCULAR_BORE_TO_CONTAINING_INCLINED_ELLIPSE'}],unconnected_ports:[1,2],pressure_closure:'NOT_CALCULATED',circuits:{topology_complete:true,issues:[]}});
 assert.match(text,/1 distributor\/plate geometry connections/);assert.match(text,/1 header\/channel geometry connections/);assert.match(text,/1 pipe geometry connections/);
 assert.match(text,/GEOMETRICALLY_CONNECTED/);assert.match(text,/Engine solution: INCOMPLETE/);assert.match(text,/pressure closure: NOT_CALCULATED/);
});
test('Coolant geometry summary keeps historical and thermal-scope limits visible',()=>{
 const report={upstream_current:false,authority:{commit_id:'exact-model'},baseline_commit_id:'exact-engine',thermal_mapping:'UNSUPPORTED_SECTOR_TO_RECTANGULAR',passages:[{part_id:'channels',channel_count:6,minimum_axial_hydraulic_diameter_m:.003,maximum_axial_hydraulic_diameter_m:.004,total_channel_volume_m3:.00012}]};
 const summary=ui.coolingSummary(report);assert.match(summary,/HISTORICAL/);assert.match(summary,/exact-model/);assert.match(summary,/exact-engine/);assert.match(summary,/3\.00000–4\.00000 mm/);assert.match(summary,/120\.000 cm³/);assert.match(summary,/thermally sized: NO/);
 assert.match(ui.coolingSummary({...report,upstream_current:true,passages:[]}),/No exported cooled-metal part/);
});
test('Component profile rows retain exact SI stations without resampling',()=>{
 const q=ui.profileRows('0, 0.01, 0.02\n0.02, 0.005, 0.015\n0.05, 0.02, 0.03');
 assert.equal(q.point_count.value,3);assert.deepEqual(q.inner1,{value:.005,unit:'m'});
});
test('Component profile rejects omitted/nonfinite/solid-axis/ragged values',()=>{
 for(const value of ['', '0,0,1', '0,0,1\n1,NaN,2','0,0,1\n1,1'])assert.throws(()=>ui.profileRows(value));
 assert.throws(()=>ui.profileRows('0,.1,.2\n1,.1,.2',true));
 assert.equal(ui.profileRows('0,0,.2\n1,0,.2',true).inner1.value,0);
});
test('Component QA requires all six explicit separate ceilings and source',()=>{
 const raw={relative_volume:'.01',centroid:'.00001',implicit_residual:'.00002',reverse_distance:'.00003',semantic_relative_area:'.001',semantic_centroid:'.00001',source:'Synthetic software criteria only'};
 const qa=ui.qaSpecification(raw);assert.equal(qa.implicit_residual.value,.00002);assert.equal(qa.reverse_distance.value,.00003);
 for(const key of Object.keys(raw))assert.throws(()=>ui.qaSpecification({...raw,[key]:''}));
 assert.throws(()=>ui.qaSpecification({...raw,relative_volume:'.1'}));
});
test('New model has no engineering dimensions or automatic output/approval',()=>{
 const value=ui.blank();assert.equal(value.source,'');assert.equal(value.export_tolerance.value,'');assert.deepEqual(value.outputs,[]);assert.deepEqual(value.features,[]);
 assert.equal(value.frames[0].parent,null);assert.equal(ui.terminal('CANCELLED'),true);assert.equal(ui.terminal('RUNNING'),false);
});
