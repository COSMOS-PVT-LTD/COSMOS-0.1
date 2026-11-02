'use strict';
/* Synthetic bounded-contract timings. Not native/browser/aggregate memory qualification. */
const {performance}=require('node:perf_hooks'),{createHash}=require('node:crypto'),path=require('node:path');
const {validatePlot,extremaDecimate,ScientificChart}=require('../gui/static/visualization/chart.js');
const echarts=require('../gui/static/vendor/echarts/echarts.min.js');
const time=fn=>{const start=performance.now(),value=fn();return {ms:performance.now()-start,value};};
(async()=>{
 const count=100000,points=Array.from({length:count},(_,i)=>[i,i%100]);
 const source_record={result_id:'synthetic-workload',model_id:null,verification:{status:'NOT_VERIFIED',reference:null},validation:{status:'NOT_CLAIMED',reference:null},validity:{status:'UNKNOWN',checks:[],violations:[],valid_range:null},outputs:{synthetic_workload_points_sha256:createHash('sha256').update(JSON.stringify(points)).digest('hex')}};
 const canonical=JSON.stringify(source_record),plot={id:'synthetic-throughput',title:'Synthetic throughput (not engineering)',x:{label:'Synthetic index',unit:'1'},y:{label:'Synthetic value',unit:'1'},series:[{name:'Synthetic',role:'computed',points}],rows:points.map(([x,y])=>({index:x,value:y})),sample_count:count,clipping:'none',notes:['Synthetic fixture, not a measured or accepted model.'],uncertainty:'not quantified',source:{domain:'propulsion',design_id:'synthetic-workload',revision:0,result_id:'synthetic-workload',model_id:null,status:'CURRENT',freshness:'current',verification:source_record.verification,validation:source_record.validation,validity:source_record.validity,assumptions:[],warnings:[],source_record,source_canonical_json:canonical,content_sha256:createHash('sha256').update(canonical).digest('hex')}};
 const checked=time(()=>validatePlot(plot)),decimated=time(()=>extremaDecimate(checked.value.series[0].points));
 const container={clientWidth:1000,setAttribute(){},textContent:''};
 const renderer={init:()=>echarts.init(null,null,{renderer:'svg',ssr:true,width:1000,height:600})};
 const chart=new ScientificChart(container,renderer),rendered=time(()=>chart.setData(plot));
 if(!chart.plot)throw new Error('Supported synthetic workload could not render');
 let largeCsvError=null;
 try{chart.exportCSV();}catch(error){largeCsvError=error.code;}
 const exportCount=10000,exportPoints=points.slice(0,exportCount),exportRecord={...source_record,result_id:'synthetic-export-workload',outputs:{synthetic_workload_points_sha256:createHash('sha256').update(JSON.stringify(exportPoints)).digest('hex')}};
 const exportCanonical=JSON.stringify(exportRecord);
 chart.setData({...plot,sample_count:exportCount,rows:plot.rows.slice(0,exportCount),series:[{...plot.series[0],points:exportPoints}],source:{...plot.source,result_id:exportRecord.result_id,source_record:exportRecord,source_canonical_json:exportCanonical,content_sha256:createHash('sha256').update(exportCanonical).digest('hex')}});
 const csv=time(()=>chart.exportCSV()),svg=time(()=>chart.exportSVG());chart.dispose();
 const {prepareKnowledgeGraph,GRAPH_LIMITS}=await import(path.resolve(__dirname,'../gui/static/visualization/knowledge-graph.js'));
 const nodes=Array.from({length:GRAPH_LIMITS.nodes},(_,i)=>({id:'node-'+i,label:'Synthetic '+i,kind:'entity'})),edges=Array.from({length:GRAPH_LIMITS.edges},(_,i)=>({source:'node-'+i%nodes.length,target:'node-'+(i+1)%nodes.length,relationship:'synthetic-only'}));
 const graph=time(()=>prepareKnowledgeGraph({nodes,edges}));
 let oversizedCode;try{prepareKnowledgeGraph({nodes:[...nodes,{id:'too-many'}],edges});}catch(error){oversizedCode=error.code;}
 console.log(JSON.stringify({scope:'Node 26 synthetic model validation, decimation, actual ECharts SVG SSR and graph preparation. Not Mac UI latency, browser/native WebGL throughput or aggregate memory.',source_points:count,source_rows:count,displayed_points:decimated.value.displayedCount,validate_ms:checked.ms,decimate_ms:decimated.ms,echarts_ssr_render_ms:rendered.ms,large_csv_error:largeCsvError,export_source_points:exportCount,csv_ms:csv.ms,csv_bytes:Buffer.byteLength(csv.value.csv),svg_ms:svg.ms,svg_data_url_bytes:Buffer.byteLength(svg.value.dataURL),graph_nodes:nodes.length,graph_edges:edges.length,graph_prepare_ms:graph.ms,oversized_graph_error:oversizedCode,node_process_memory:process.memoryUsage()},null,2));
})().catch(error=>{console.error(error.code||error.name,error.message);process.exitCode=1;});
