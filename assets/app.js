const palette = ["#245f93", "#b9822d", "#667a42", "#bd6b73", "#5a6c85"];
const metricLabels = {
  denuncias_tasa_100k: "Tasa de denuncias por 100,000 hab.",
  victimizacion_pct: "Victimizacion (%)",
  percepcion_inseguridad_pct: "Percepcion de inseguridad (%)",
  confianza_pnp_pct: "Confianza en la PNP (%)",
  brecha_percepcion_victimizacion: "Brecha percepcion - victimizacion",
};
const tooltip = document.querySelector("#tooltip");
const state = { year: 2024, metric: "denuncias_tasa_100k", department: "Todos", cluster: "Todos" };
let panel = [], clusters = [], modelMetrics = [], importance = [], summary = null;

async function text(path) { const res = await fetch(path); if (!res.ok) throw new Error(path); return res.text(); }
async function json(path) { const res = await fetch(path); if (!res.ok) throw new Error(path); const raw = await res.text(); return JSON.parse(raw.replace(/\bNaN\b/g, "null")); }
function parseCSV(raw) {
  const rows = []; let row = [], cell = "", quoted = false;
  for (let i = 0; i < raw.length; i++) {
    const c = raw[i], n = raw[i + 1];
    if (c === '"' && quoted && n === '"') { cell += '"'; i++; }
    else if (c === '"') quoted = !quoted;
    else if (c === ',' && !quoted) { row.push(cell); cell = ""; }
    else if ((c === '\n' || c === '\r') && !quoted) { if (c === '\r' && n === '\n') i++; row.push(cell); if (row.some(v => v !== "")) rows.push(row); row = []; cell = ""; }
    else cell += c;
  }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  const header = rows.shift();
  return rows.map(r => Object.fromEntries(header.map((h, i) => [h, coerce(r[i])])))
}
function coerce(v) { if (v === undefined || v === "") return null; const num = Number(v); return Number.isFinite(num) && String(v).trim() !== "" ? num : v; }
function fmt(v, digits = 1) { if (v == null || Number.isNaN(v)) return "n.d."; if (Math.abs(v) >= 1_000_000) return `${(v/1_000_000).toFixed(2)}M`; if (Math.abs(v) >= 1000) return Intl.NumberFormat("es-PE", { maximumFractionDigits: digits }).format(v); return Number(v).toFixed(digits); }
function pct(v) { return `${fmt(v, 1)}%`; }
function extent(data, key) { const vals = data.map(d => +d[key]).filter(Number.isFinite); return [Math.min(...vals), Math.max(...vals)]; }
function scale([d0,d1], [r0,r1]) { const span = d1 - d0 || 1; return v => r0 + ((v - d0) / span) * (r1 - r0); }
function svgRoot(el, w = 760, h = 340) { el.innerHTML = ""; const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg"); svg.setAttribute("viewBox", `0 0 ${w} ${h}`); svg.setAttribute("preserveAspectRatio", "xMidYMid meet"); el.appendChild(svg); return svg; }
function node(name, attrs = {}, textContent = null) { const n = document.createElementNS("http://www.w3.org/2000/svg", name); Object.entries(attrs).forEach(([k,v]) => n.setAttribute(k, v)); if (textContent != null) n.textContent = textContent; return n; }
function showTip(evt, html) { tooltip.innerHTML = html; tooltip.hidden = false; tooltip.style.left = `${evt.clientX + 14}px`; tooltip.style.top = `${evt.clientY + 14}px`; }
function hideTip() { tooltip.hidden = true; }
function groupBy(data, key) { return data.reduce((m,d) => ((m[d[key]] ||= []).push(d), m), {}); }

function drawAxes(svg, xTicks, yTicks, x, y, width, height, margin) {
  yTicks.forEach(t => { const yy = y(t); svg.appendChild(node("line", { x1: margin.left, y1: yy, x2: width - margin.right, y2: yy, class: "gridline" })); svg.appendChild(node("text", { x: margin.left - 8, y: yy + 4, "text-anchor": "end", class: "axis" }, fmt(t, 0))); });
  xTicks.forEach(t => svg.appendChild(node("text", { x: x(t), y: height - margin.bottom + 22, "text-anchor": "middle", class: "axis" }, t)));
}
function drawTrend() {
  const el = document.querySelector("#trend-chart"), svg = svgRoot(el, 760, 340), m = {left:58,right:24,top:18,bottom:44};
  const base = state.department === "Todos" ? Object.values(groupBy(panel, "anio")).map(rows => ({ anio: rows[0].anio, denuncias_tasa_100k: rows.reduce((a,b)=>a+b.denuncias_tasa_100k,0)/rows.length, victimizacion_pct: rows.reduce((a,b)=>a+b.victimizacion_pct,0)/rows.length, percepcion_inseguridad_pct: rows.reduce((a,b)=>a+b.percepcion_inseguridad_pct,0)/rows.length, confianza_pnp_pct: rows.reduce((a,b)=>a+b.confianza_pnp_pct,0)/rows.length })) : panel.filter(d => d.departamento === state.department);
  const years = [...new Set(panel.map(d => d.anio))].sort();
  const series = ["denuncias_tasa_100k", "victimizacion_pct", "percepcion_inseguridad_pct", "confianza_pnp_pct"];
  const normalized = [];
  series.forEach((key, si) => { const vals = base.map(d => d[key]); const [min,max] = [Math.min(...vals), Math.max(...vals)]; base.forEach(d => normalized.push({ anio: d.anio, key, value: d[key], index: ((d[key]-min)/((max-min)||1))*100, color: palette[si] })); });
  const x = scale([Math.min(...years), Math.max(...years)], [m.left, 760-m.right]); const y = scale([0,100], [340-m.bottom, m.top]);
  drawAxes(svg, years, [0,25,50,75,100], x, y, 760, 340, m);
  series.forEach((key, si) => { const pts = normalized.filter(d => d.key === key).sort((a,b)=>a.anio-b.anio); const path = pts.map((d,i)=>`${i?"L":"M"}${x(d.anio)},${y(d.index)}`).join(" "); svg.appendChild(node("path", { d: path, fill: "none", stroke: palette[si], "stroke-width": 3 })); pts.forEach(d => { const c = node("circle", { cx: x(d.anio), cy: y(d.index), r: 4.5, fill: palette[si], tabindex: 0 }); c.addEventListener("mousemove", e => showTip(e, `<b>${metricLabels[key]}</b><br>${d.anio}: ${fmt(d.value, 1)}`)); c.addEventListener("mouseleave", hideTip); svg.appendChild(c); }); });
  addLegend(el, series.map((s,i)=>({label: metricLabels[s], color: palette[i]})));
}
function drawRanking() {
  const el = document.querySelector("#ranking-chart"), svg = svgRoot(el, 520, 470), m = {left:142,right:40,top:12,bottom:24};
  const rows = panel.filter(d => d.anio === state.year).sort((a,b)=>b[state.metric]-a[state.metric]).slice(0, 15);
  document.querySelector("#ranking-title").textContent = `${metricLabels[state.metric]} (${state.year})`;
  const x = scale([0, Math.max(...rows.map(d => d[state.metric]))], [m.left, 520-m.right]);
  rows.forEach((d,i)=>{ const y = m.top + i*28; const w = x(d[state.metric])-m.left; svg.appendChild(node("text", {x:m.left-8,y:y+17,"text-anchor":"end",class:"axis"}, d.departamento)); const rect=node("rect",{x:m.left,y:y,width:Math.max(1,w),height:18,rx:4,fill:palette[d.cluster%palette.length]}); rect.addEventListener("mousemove",e=>showTip(e,`<b>${d.departamento}</b><br>${metricLabels[state.metric]}: ${fmt(d[state.metric],1)}<br>Cluster ${d.cluster}`)); rect.addEventListener("mouseleave",hideTip); svg.appendChild(rect); svg.appendChild(node("text",{x:x(d[state.metric])+6,y:y+14,class:"axis"},fmt(d[state.metric],1))); });
}
function drawScatter() {
  const el = document.querySelector("#scatter-chart"), svg = svgRoot(el, 560, 340), m = {left:54,right:18,top:18,bottom:46};
  const rows = panel.filter(d => d.anio === state.year || state.year === "Todos");
  const x = scale(extent(panel,"victimizacion_pct"), [m.left,560-m.right]); const y = scale(extent(panel,"percepcion_inseguridad_pct"), [340-m.bottom,m.top]);
  drawAxes(svg, [15,20,25,30,35], [10,25,40,55,70], x, y, 560, 340, m);
  rows.forEach(d=>{ const c=node("circle",{cx:x(d.victimizacion_pct),cy:y(d.percepcion_inseguridad_pct),r: state.department===d.departamento?7:4.5,fill:palette[d.cluster%palette.length],opacity: (state.department==="Todos"||state.department===d.departamento) ? .95 : .22}); c.addEventListener("mousemove",e=>showTip(e,`<b>${d.departamento} ${d.anio}</b><br>Victimizacion: ${pct(d.victimizacion_pct)}<br>Percepcion: ${pct(d.percepcion_inseguridad_pct)}<br>Brecha: ${fmt(d.brecha_percepcion_victimizacion,1)} pp`)); c.addEventListener("mouseleave",hideTip); svg.appendChild(c); });
  svg.appendChild(node("text",{x:280,y:330,"text-anchor":"middle",class:"axis"},"Victimizacion (%)"));
  svg.appendChild(node("text",{x:-170,y:14,transform:"rotate(-90)","text-anchor":"middle",class:"axis"},"Percepcion de inseguridad (%)"));
}
function drawCluster() {
  const el = document.querySelector("#cluster-chart"), svg = svgRoot(el, 560, 340), m = {left:42,right:18,top:18,bottom:42};
  const rows = panel.filter(d => state.cluster === "Todos" || String(d.cluster) === String(state.cluster));
  const x = scale(extent(panel,"pca1"), [m.left,560-m.right]); const y = scale(extent(panel,"pca2"), [340-m.bottom,m.top]);
  drawAxes(svg, [-4,-2,0,2,4], [-2,0,2,4], x, y, 560, 340, m);
  rows.forEach(d=>{ const c=node("circle",{cx:x(d.pca1),cy:y(d.pca2),r: state.department===d.departamento?7:4.5,fill:palette[d.cluster%palette.length],opacity: state.year===d.anio ? .9 : .35}); c.addEventListener("mousemove",e=>showTip(e,`<b>${d.departamento} ${d.anio}</b><br>Cluster ${d.cluster}<br>Tasa denuncias: ${fmt(d.denuncias_tasa_100k,1)}<br>Victimizacion: ${pct(d.victimizacion_pct)}`)); c.addEventListener("mouseleave",hideTip); svg.appendChild(c); });
}
function drawModelMetrics() {
  const el = document.querySelector("#model-chart"), svg = svgRoot(el, 560, 340), m = {left:62,right:18,top:18,bottom:58};
  const metrics = ["accuracy","precision","recall","f1"]; const w = (560-m.left-m.right)/(modelMetrics.length*metrics.length + modelMetrics.length);
  drawAxes(svg, [], [0,.25,.5,.75,1], v=>v, scale([0,1],[340-m.bottom,m.top]), 560, 340, m);
  modelMetrics.forEach((d,mi)=> metrics.forEach((met, i)=>{ const x=m.left+(mi*(metrics.length+1)+i)*w; const y=scale([0,1],[340-m.bottom,m.top])(d[met]); svg.appendChild(node("rect",{x,y,width:w*.82,height:340-m.bottom-y,fill:palette[i],rx:3})); svg.appendChild(node("title",{},`${d.modelo} ${met}: ${fmt(d[met],3)}`)); }));
  modelMetrics.forEach((d,mi)=>svg.appendChild(node("text",{x:m.left+(mi*(metrics.length+1)+1.8)*w,y:318,"text-anchor":"middle",class:"axis"},d.modelo.replace("Classifier",""))));
  addLegend(el, metrics.map((s,i)=>({label:s, color:palette[i]})));
}
function drawImportance() {
  const el = document.querySelector("#importance-chart"), svg = svgRoot(el, 560, 340), m = {left:210,right:32,top:12,bottom:24};
  const rows = importance.slice(0,10); const [min,max]=extent(rows,"importance_mean"); const x=scale([Math.min(0,min),max],[m.left,560-m.right]); const zero=x(0);
  rows.forEach((d,i)=>{ const y=m.top+i*29; const value=d.importance_mean; svg.appendChild(node("text",{x:m.left-8,y:y+17,"text-anchor":"end",class:"axis"},d.feature.replaceAll("_"," "))); svg.appendChild(node("rect",{x:Math.min(zero,x(value)),y,width:Math.abs(x(value)-zero),height:18,rx:4,fill:value>=0?"#b9822d":"#9aa5b1"})); svg.appendChild(node("text",{x:x(value)+(value>=0?6:-34),y:y+14,class:"axis"},fmt(value,3))); });
  svg.appendChild(node("line",{x1:zero,y1:m.top,x2:zero,y2:315,stroke:"#17202a","stroke-width":1}));
}
function drawClusterTable() {
  const table = document.querySelector("#cluster-table");
  table.innerHTML = `<thead><tr><th>Cluster</th><th>Observaciones</th><th>Tasa denuncias</th><th>Victimizacion</th><th>Percepcion</th><th>Confianza</th><th>Lectura</th></tr></thead>`;
  const tbody = document.createElement("tbody");
  clusters.forEach(c=>{ const lectura = c.cluster===0 ? "Mayor victimización relativa y menor confianza promedio." : c.cluster===1 ? "Menor incidencia relativa y menor percepción promedio." : "Mayor percepción y tasa registrada promedio."; const tr=document.createElement("tr"); tr.innerHTML = `<td>${c.cluster}</td><td>${c.observaciones}</td><td>${fmt(c.denuncias_tasa_100k,1)}</td><td>${pct(c.victimization)}</td><td>${pct(c.percepcion)}</td><td>${pct(c.confianza)}</td><td>${lectura}</td>`; tbody.appendChild(tr); });
  table.appendChild(tbody);
}
function addLegend(el, items) { const old = el.querySelector(".legend"); if (old) old.remove(); const legend=document.createElement("div"); legend.className="legend"; legend.innerHTML=items.map(i=>`<span><i style="background:${i.color}"></i>${i.label}</span>`).join(""); el.appendChild(legend); }
function populateControls() {
  const years = [...new Set(panel.map(d=>d.anio))].sort();
  document.querySelector("#year-select").innerHTML = years.map(y=>`<option value="${y}" ${y===2024?"selected":""}>${y}</option>`).join("");
  document.querySelector("#department-select").innerHTML = `<option>Todos</option>` + [...new Set(panel.map(d=>d.departamento))].sort().map(d=>`<option>${d}</option>`).join("");
  document.querySelector("#cluster-filter").innerHTML = `<option>Todos</option>` + [...new Set(panel.map(d=>d.cluster))].sort().map(c=>`<option>${c}</option>`).join("");
}
function render() { drawTrend(); drawRanking(); drawScatter(); drawCluster(); drawModelMetrics(); drawImportance(); drawClusterTable(); }
function bind() {
  document.querySelector("#year-select").addEventListener("change", e=>{ state.year = Number(e.target.value); render(); });
  document.querySelector("#metric-select").addEventListener("change", e=>{ state.metric = e.target.value; render(); });
  document.querySelector("#department-select").addEventListener("change", e=>{ state.department = e.target.value; render(); });
  document.querySelector("#cluster-filter").addEventListener("change", e=>{ state.cluster = e.target.value; render(); });
  document.querySelector("#reset-view").addEventListener("click", ()=>{ state.year=2024; state.metric="denuncias_tasa_100k"; state.department="Todos"; state.cluster="Todos"; populateControls(); render(); });
}
async function init() {
  [panel, clusters, modelMetrics, importance, summary] = await Promise.all([
    text("data/processed/panel_con_clusters.csv").then(parseCSV),
    text("outputs/tables/cluster_profiles.csv").then(parseCSV),
    text("outputs/tables/classification_benchmark.csv").then(parseCSV),
    text("outputs/tables/classification_permutation_importance.csv").then(parseCSV),
    json("outputs/tables/analysis_summary.json"),
  ]);
  importance.sort((a,b)=>b.importance_mean-a.importance_mean);
  const latest = summary.eda.by_year.find(d => d.anio === 2024);
  document.querySelector("#kpi-observaciones").textContent = panel.length;
  document.querySelector("#kpi-denuncias").textContent = fmt(latest.denuncias_total, 2);
  document.querySelector("#kpi-victimizacion").textContent = pct(latest.victimizacion_pct);
  document.querySelector("#kpi-f1").textContent = fmt(modelMetrics.find(d=>d.modelo==="RandomForest").f1, 3);
  populateControls(); bind(); render(); window.addEventListener("resize", render);
}
init().catch(err => { document.body.insertAdjacentHTML("beforeend", `<pre class="load-error">No se pudieron cargar los datos del tablero: ${err.message}</pre>`); });


