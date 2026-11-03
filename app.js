/* Estudo UNIP: portal de revisão. Dados em window.DADOS[COD] (gerados por build.py). */
const PROVAS = [
  {dia:"2026-11-03", hora:"12:30", cod:"D05E", nome:"Linguagem e Comunicação Jurídica"},
  {dia:"2026-11-03", hora:"13:15", cod:"803X", nome:"Teoria Geral do Processo"},
  {dia:"2026-11-03", hora:"14:45", cod:"883X", nome:"Bases Constitucionais da Administração Pública"},
  {dia:"2026-11-03", hora:"16:15", cod:"18A1", nome:"Teoria da Empresa"},
  {dia:"2026-11-04", hora:"12:30", cod:"21A1", nome:"Direitos Humanos"},
  {dia:"2026-11-04", hora:"14:00", cod:"D55B", nome:"Psicologia Jurídica"},
  {dia:"2026-11-04", hora:"14:45", cod:"18A7", nome:"Procedimento Comum"},
  {dia:"2026-11-04", hora:"15:30", cod:"D982", nome:"Tópicos Especiais de Direito Privado (optativa)"}
];

const mem = {};
const store = {
  get(k, d){ try{ const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; }catch(e){ return k in mem ? mem[k] : d; } },
  set(k, v){ try{ localStorage.setItem(k, JSON.stringify(v)); }catch(e){ mem[k] = v; } }
};
const prog = cod => Object.assign({rev:[], q:[], cards:{}}, store.get("p:" + cod, {}));
const saveProg = (cod, p) => store.set("p:" + cod, p);

const $ = s => document.querySelector(s);
const D = cod => (window.DADOS || {})[cod];
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const norm = s => s.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
const plain = h => h.replace(/<[^>]+>/g, " ");
const dias = ["domingo","segunda","terça","quarta","quinta","sexta","sábado"];
const meses = ["janeiro","fevereiro","março","abril","maio","junho","julho","agosto","setembro","outubro","novembro","dezembro"];
const ts = p => new Date(p.dia + "T" + p.hora + ":00-03:00");
const fmtDia = iso => { const d = new Date(iso + "T12:00:00-03:00"), n = dias[d.getDay()];
  return `${n[0].toUpperCase() + n.slice(1)}${d.getDay() % 6 === 0 ? "" : "-feira"}, ${d.getDate()} de ${meses[d.getMonth()]}`; };

function pct(cod){
  const d = D(cod); if(!d) return 0;
  const p = prog(cod), total = d.revisao.length + d.questoes.length + d.cards.length;
  const feito = p.rev.length + p.q.length + Object.values(p.cards).filter(v => v === 1).length;
  return total ? Math.round(feito / total * 100) : 0;
}
const blocoLongo = b => b.replace(/^MÓDULO/, "Módulo").replace(/^UNIDADE (I+) — QUESTIONÁRIO/, "Unidade $1, questionário").replace(/^UNIDADE (I+) — ATIVIDADE TELEAULA/, "Unidade $1, teleaula");
const blocoCurto = b => { const m = b.match(/^MÓDULO (\d+)/); return m ? "Módulo " + m[1] : blocoLongo(b); };
const notasDe = (d, esc_, ref) => d.notas.filter(n => n.esc === esc_ && n.ref === ref);
const conferirHtml = ns => ns.map(n => `<div class="conferir"><b>Conferir: ${esc(n.titulo)}</b>${esc(n.texto)}</div>`).join("");

let S = {cod:null, tab:"revisao", filtro:"todos", bloco:"todos", soRepete:false, busca:"", open:new Set(), fila:null, flip:false};

/* ───────── home ───────── */
function countdown(){
  const agora = new Date();
  const prox = PROVAS.map(p => ({p, t:ts(p)})).filter(x => x.t > agora).sort((a, b) => a.t - b.t)[0];
  if(!prox) return `<div class="next"><span><b>Todas as provas foram realizadas.</b> Bom trabalho.</span></div>`;
  const ms = prox.t - agora, h = Math.floor(ms / 36e5), m = Math.floor(ms % 36e5 / 6e4);
  const txt = h >= 48 ? `${Math.floor(h / 24)} dias` : `${h} h ${String(m).padStart(2, "0")} min`;
  return `<div class="next"><span>Próxima prova: <b>${esc(prox.p.nome)}</b>, às ${prox.p.hora}</span><span class="cd">em ${txt}</span></div>`;
}
function home(){
  const grupos = {};
  PROVAS.forEach(p => (grupos[p.dia] = grupos[p.dia] || []).push(p));
  let h = `<h1>Provas de 3 e 4 de novembro</h1>
  <p class="lede">As disciplinas na ordem em que você vai fazê-las. Abra uma para ver a revisão de véspera, as questões comentadas e os flashcards.</p>${countdown()}`;
  for(const dia in grupos){
    h += `<section class="day"><h2>${fmtDia(dia)}</h2><ol class="slots">`;
    grupos[dia].forEach(p => {
      const d = D(p.cod), x = pct(p.cod);
      h += `<li class="slot"><span class="slot-time">${p.hora}</span>
      <${d ? "a" : "div"} class="slot-card ${d ? "ready" : ""}" ${d ? `href="#${p.cod.toLowerCase()}-revisao"` : ""}>
        <span><span class="slot-name">${esc(p.nome)}</span><br><span class="slot-code">${p.cod}${d ? `, ${d.revisao.length} tópicos, ${d.questoes.length} questões, ${d.cards.length} flashcards` : ""}</span></span>
        <span class="slot-side">${d ? `<span class="chip pronto">Material recebido</span>` : `<span class="chip wait">Aguardando material</span>`}</span>
        ${d ? `<span class="bar" role="progressbar" aria-valuenow="${x}" aria-valuemin="0" aria-valuemax="100" aria-label="Seu progresso"><i style="width:${x}%"></i></span>` : ""}
      </${d ? "a" : "div"}></li>`;
    });
    h += `</ol></section>`;
  }
  h += `<p class="foot-note">Material de apoio montado a partir dos arquivos extraídos do AVA. Não substitui as aulas nem garante o que cairá na prova. Onde o material tem pontos duvidosos, eles aparecem em azul com o título “Conferir”.</p>`;
  $("#app").innerHTML = h;
}

/* ───────── disciplina ───────── */
function disciplina(slug, tab){
  const p = PROVAS.find(x => x.cod.toLowerCase() === slug), d = D(p.cod);
  const nConf = d.notas.length;
  $("#app").innerHTML = `<a class="voltar" href="#home"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>Todas as provas</a>
  <h1>${esc(p.nome)}</h1>
  <div class="meta"><span>${p.cod}</span><span>${fmtDia(p.dia)}, ${p.hora}</span><span class="chip wait" title="O material ainda não passou por conferência automática nem por auditoria independente.">Conferência pendente</span></div>
  <div class="panels">
    <details class="panel info"><summary>Pontos para conferir (${nConf})</summary><div class="panel-b"><ul>${
      nConf ? d.notas.map(n => `<li><b>${esc(n.titulo)}.</b> ${esc(n.texto)}</li>`).join("") : "<li>Nenhum ponto marcado.</li>"}</ul></div></details>
    <details class="panel"><summary>O que este material cobre e o que não cobre</summary><div class="panel-b"><ul>${d.cobertura.map(c => `<li>${esc(c)}</li>`).join("")}</ul></div></details>
  </div>
  <div class="tabs" role="tablist">${[["revisao","Revisão de véspera",d.revisao.length],["questoes","Questões comentadas",d.questoes.length],["flashcards","Flashcards",d.cards.length]]
    .map(([k, l, n]) => `<button role="tab" class="tab" aria-selected="${tab === k}" data-tab="${k}">${l}<span>${n}</span></button>`).join("")}</div>
  <div id="pane"></div>`;
  document.querySelectorAll(".tab").forEach(b => b.onclick = () => { location.hash = `${slug}-${b.dataset.tab}`; });
  ({revisao: () => revisao(p.cod), questoes: () => questoes(p.cod), flashcards: () => flashcards(p.cod)})[tab]();
}

/* ───────── revisão ───────── */
function revisao(cod){
  const d = D(cod), pr = prog(cod), q = norm(S.busca.trim());
  const lista = d.revisao.filter(t => (S.filtro === "todos" || t.prob === S.filtro) && (!q || norm(t.titulo + " " + plain(t.html)).includes(q)));
  let h = d.top5.length ? `<div class="top5"><h3>Temas que mais caem, segundo o resumo</h3><ol>${d.top5.map(t => `<li>${t}</li>`).join("")}</ol></div>` : "";
  h += `<div class="toolbar">${[["todos","Todos"],["alta","Prioridade alta"],["media","Prioridade média"]]
    .map(([k, l]) => `<button class="fbtn" data-f="${k}" aria-pressed="${S.filtro === k}">${l}</button>`).join("")}
    <input class="search" id="busca" type="search" placeholder="Buscar na revisão" value="${esc(S.busca)}" aria-label="Buscar na revisão">
    <span class="spacer"></span><span class="count">${pr.rev.length} de ${d.revisao.length} revisados</span></div>`;
  if(!lista.length) h += `<div class="empty">Nenhum tópico encontrado.</div>`;
  lista.forEach(t => {
    const feito = pr.rev.includes(t.id);
    h += `<details class="topic ${feito ? "done" : ""}" data-p="${t.prob}" data-id="${t.id}" ${(S.open.has(t.id) || q) ? "open" : ""}>
      <summary><span class="chip ${t.prob}">${t.prob === "alta" ? "Alta" : "Média"}</span><span class="topic-t">${esc(t.titulo)}</span></summary>
      <div class="topic-body"><div class="rev">${t.html}</div>${conferirHtml(notasDe(d, "revisao", t.id))}
        <label class="check"><input type="checkbox" data-rev="${t.id}" ${feito ? "checked" : ""}>Marcar como revisado</label></div></details>`;
  });
  $("#pane").innerHTML = h;
  document.querySelectorAll(".fbtn[data-f]").forEach(b => b.onclick = () => { S.filtro = b.dataset.f; revisao(cod); });
  $("#busca").oninput = e => { S.busca = e.target.value; const pos = e.target.selectionStart; revisao(cod); const i = $("#busca"); i.focus(); i.setSelectionRange(pos, pos); };
  document.querySelectorAll("details.topic").forEach(el => el.addEventListener("toggle", () => { el.open ? S.open.add(el.dataset.id) : S.open.delete(el.dataset.id); }));
  document.querySelectorAll("[data-rev]").forEach(c => c.onchange = () => {
    const p = prog(cod), id = c.dataset.rev;
    p.rev = c.checked ? [...new Set([...p.rev, id])] : p.rev.filter(x => x !== id);
    saveProg(cod, p); S.open.add(id); revisao(cod);
  });
}

/* ───────── questões ───────── */
function questoes(cod){
  const d = D(cod), pr = prog(cod), q = norm(S.busca.trim());
  const blocos = [...new Set(d.questoes.map(x => x.bloco))];
  const lista = d.questoes.filter(x => (S.bloco === "todos" || x.bloco === S.bloco) && (!S.soRepete || x.repete) &&
    (!q || norm([x.num, x.tema, x.enun, x.html, x.coment.join(" "), x.gab].join(" ").replace(/<[^>]+>/g, " ")).includes(q)));
  let h = `<div class="chips-scroll"><button class="fbtn" data-b="todos" aria-pressed="${S.bloco === "todos"}">Todos os blocos</button>${
    blocos.map(b => `<button class="fbtn" data-b="${esc(b)}" aria-pressed="${S.bloco === b}">${esc(blocoCurto(b))}</button>`).join("")}</div>
  <div class="toolbar"><button class="fbtn" id="repete" aria-pressed="${S.soRepete}" title="Questões que repetem um conceito já cobrado">Só as que se repetem</button>
    <input class="search" id="busca" type="search" placeholder="Buscar nas questões" value="${esc(S.busca)}" aria-label="Buscar nas questões">
    <span class="spacer"></span><span class="count">${lista.length} de ${d.questoes.length} questões, ${pr.q.length} revisadas</span></div>`;
  let atual = null;
  lista.forEach(x => {
    if(x.bloco !== atual){ atual = x.bloco; h += `<h3 class="gh">${esc(blocoLongo(atual))}</h3>`; }
    const ns = notasDe(d, "questao", x.id);
    h += `<article class="qrow"><div class="qrow-h"><span class="qn">${esc(x.num)}</span>${x.tema ? `<span class="qtema">${esc(x.tema)}</span>` : `<span class="qtema"></span>`}
      ${x.repete ? `<span class="chip media" title="${esc(x.repeteRef || "Repete um conceito já cobrado")}">Repete</span>` : ""}
      <span class="gab" aria-label="Gabarito ${x.gab}"><b>${x.gab}</b>${x.gabLabel ? `<span>${esc(x.gabLabel)}</span>` : ""}</span></div>
      ${x.enun ? `<p class="qenun">${x.enun}</p>` : ""}${x.html ? `<p class="qtxt">${x.html}</p>` : ""}
      ${x.coment.map(c => `<p class="qcom">${c}</p>`).join("")}${x.repeteRef ? `<p class="qcom">Repete: ${esc(x.repeteRef)}</p>` : ""}${conferirHtml(ns)}
      <label class="check"><input type="checkbox" data-q="${x.id}" ${pr.q.includes(x.id) ? "checked" : ""}>Revisei</label></article>`;
  });
  if(!lista.length) h += `<div class="empty">Nenhuma questão encontrada.</div>`;
  if(d.sinteses.length && S.bloco === "todos" && !S.soRepete && !q){
    h += `<h3 class="gh">Síntese dos módulos sem questões detalhadas</h3>` + d.sinteses.map(s => `<div class="sint"><h3>${esc(s.titulo)}</h3><p>${s.html}</p></div>`).join("");
  }
  $("#pane").innerHTML = h;
  document.querySelectorAll("[data-b]").forEach(b => b.onclick = () => { S.bloco = b.dataset.b; questoes(cod); });
  $("#repete").onclick = () => { S.soRepete = !S.soRepete; questoes(cod); };
  $("#busca").oninput = e => { S.busca = e.target.value; const pos = e.target.selectionStart; questoes(cod); const i = $("#busca"); i.focus(); i.setSelectionRange(pos, pos); };
  document.querySelectorAll("[data-q]").forEach(c => c.onchange = () => {
    const p = prog(cod), id = c.dataset.q; const y = window.scrollY;
    p.q = c.checked ? [...new Set([...p.q, id])] : p.q.filter(z => z !== id); saveProg(cod, p);
    document.querySelector(".count").textContent = `${lista.length} de ${d.questoes.length} questões, ${p.q.length} revisadas`;
  });
}

/* ───────── flashcards ───────── */
function flashcards(cod){
  const d = D(cod), pr = prog(cod);
  if(!S.fila) S.fila = d.cards.filter(c => pr.cards[c.id] !== 1).map(c => c.id);
  const total = d.cards.length, sabidos = d.cards.filter(c => pr.cards[c.id] === 1).length;
  if(!S.fila.length){
    $("#pane").innerHTML = `<div class="fc-done"><h3>Baralho concluído</h3><p class="lede" style="margin:0 auto 16px">Você marcou ${sabidos} de ${total} cards como sabidos.</p><button class="btn main" id="reinicia">Recomeçar baralho</button></div>`;
    $("#reinicia").onclick = () => { const p = prog(cod); p.cards = {}; saveProg(cod, p); S.fila = null; S.flip = false; flashcards(cod); };
    return;
  }
  const c = d.cards.find(x => x.id === S.fila[0]), ns = notasDe(d, "card", c.id);
  $("#pane").innerHTML = `<div class="fc-top"><span>${sabidos} de ${total} sabidos, ${S.fila.length} na fila</span><span class="kbd">Espaço vira, seta esquerda errei, seta direita acertei</span></div>
  <div class="fc-scene"><button class="fc ${S.flip ? "flip" : ""}" id="fc" aria-label="Virar o card">
    <span class="face"><span class="lab">Pergunta</span><span class="txt">${c.f}</span><span class="hint">Toque para ver a resposta</span></span>
    <span class="face back"><span class="lab">Resposta</span><span class="txt">${c.v}</span><span class="hint">Você acertou?</span></span></button></div>
  <div class="fc-note" id="fcnote" ${S.flip ? "" : "hidden"}>${conferirHtml(ns)}</div>
  <div class="fc-actions"><button class="btn wrong" id="errei">Errei, repetir depois</button><button class="btn right" id="acertei">Acertei</button></div>`;
  $("#fc").onclick = () => { S.flip = !S.flip; $("#fc").classList.toggle("flip", S.flip); $("#fcnote").hidden = !S.flip; };
  $("#errei").onclick = () => marca(cod, 0);
  $("#acertei").onclick = () => marca(cod, 1);
}
function marca(cod, v){
  const p = prog(cod), id = S.fila.shift(); p.cards[id] = v; saveProg(cod, p);
  if(v === 0) S.fila.push(id);
  S.flip = false; flashcards(cod);
}

/* ───────── rotas, tema, teclado ───────── */
function route(){
  const h = location.hash.slice(1) || "home";
  const m = h.match(/^([a-z0-9]{4})-(revisao|questoes|flashcards)$/);
  if(m && D(m[1].toUpperCase())){
    if(S.cod !== m[1]){ S = Object.assign(S, {cod:m[1], filtro:"todos", bloco:"todos", soRepete:false, busca:"", fila:null, flip:false, open:new Set([D(m[1].toUpperCase()).revisao[0].id])}); }
    if(S.tab !== m[2]){ S.busca = ""; S.fila = null; S.flip = false; }
    S.tab = m[2]; disciplina(m[1], m[2]);
  } else { S.cod = null; home(); }
  window.scrollTo(0, 0);
}
window.addEventListener("hashchange", route);
window.addEventListener("beforeprint", () => document.querySelectorAll("details").forEach(x => x.open = true));
document.addEventListener("keydown", e => {
  if(/INPUT|TEXTAREA/.test(e.target.tagName) || S.tab !== "flashcards" || !$("#fc")) return;
  if(e.key === " "){ e.preventDefault(); $("#fc").click(); }
  if(e.key === "ArrowLeft") $("#errei").click();
  if(e.key === "ArrowRight") $("#acertei").click();
});
$("#theme").onclick = () => {
  const r = document.documentElement, dark = r.dataset.theme === "dark" || (!r.dataset.theme && matchMedia("(prefers-color-scheme: dark)").matches);
  r.dataset.theme = dark ? "light" : "dark";
};
setInterval(() => { if(!S.cod) home(); }, 60000);
route();
