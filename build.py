#!/usr/bin/env python3
"""Converte conteudo/<COD>/*.md em data/<COD>.js e confere contagens.
Uso:  python3 build.py            (gera data/*.js)
      python3 build.py --single   (gera dist/portal.html, arquivo único)"""
import re, json, html, sys, pathlib
import markdown

ROOT = pathlib.Path(__file__).parent
SRC, OUT = ROOT/'conteudo', ROOT/'data'
OUT.mkdir(exist_ok=True)
AVISOS = []

def esc(s): return html.escape(s, quote=False)

def inline(s):
    s = esc(s.strip())
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?!\*)', r'<i>\1</i>', s)
    s = re.sub(r'`(.+?)`', r'<code>\1</code>', s)
    return s

def prep_md(t):
    out, prev = [], ''
    for ln in t.split('\n'):
        starts = bool(re.match(r'\s*([-*] |\d+\. |\|)', ln))
        prev_is = bool(re.match(r'\s*([-*] |\d+\. |\|)', prev))
        if starts and prev.strip() and not prev_is:
            out.append('')
        out.append(ln); prev = ln
    return '\n'.join(out)

def md_html(t):
    h = markdown.markdown(prep_md(t), extensions=['tables', 'sane_lists'])
    h = h.replace('<table>', '<div class="tw"><table>').replace('</table>', '</table></div>')
    h = re.sub(r'<p><strong>(PEGADINHA)', r'<p class="pega"><strong>\1', h)
    return h

def clean_lines(t):
    return '\n'.join(l for l in t.split('\n') if l.strip() != '---').strip()

def sections(text):
    parts = re.split(r'(?m)^## ', text)
    return [(p.partition('\n')[0].strip(), p.partition('\n')[2]) for p in parts[1:]]

def split_commas(s):
    return [x.strip() for x in re.split(r',\s*(?![^()]*\))', s) if x.strip()]

# ───────── revisão ─────────
def parse_revisao(cod, cfg):
    text = (SRC/cod/'revisao_vespera.md').read_text(encoding='utf-8')
    top5, items, n = [], [], 0
    for title, body in sections(text):
        body = clean_lines(body)
        if title.upper().startswith('TOP 5'):
            top5 = [inline(m.group(1)) for m in re.finditer(r'(?m)^\d+\.\s*(.+)$', body)]
            continue
        if title.upper().startswith('ARQUIVOS'):
            continue
        m = re.search(r'(?m)^> \*\*Temas ALTA probabilidade:\*\*\s*(.+)$', body)
        if m:
            raw = m.group(1)
            top5 = [inline(x) for x in (raw.split('|') if '|' in raw else split_commas(raw))]
        body = '\n'.join(l for l in body.split('\n') if not l.startswith('>') and not l.startswith('*Arquivos')).strip()
        n += 1
        titulo = cfg['titulos'][n-1] if cfg.get('titulos') else re.sub(r'^\d+\.\s*', '', title)
        items.append({'id': f'r{n}', 'titulo': titulo, 'prob': cfg['prob'][n], 'html': md_html(body)})
    return items, top5

# ───────── flashcards ─────────
def parse_cards(cod):
    text = (SRC/cod/'flashcards.md').read_text(encoding='utf-8')
    cards = []
    if cod == '18A1':
        for m in re.finditer(r'(?ms)^\*\*(\d+)\.\s*(.*?)\*\*\n(.*?)(?=^\*\*\d+\.|\Z)', text):
            cards.append((m.group(2), m.group(3)))
    else:
        for blk in re.split(r'\n---\n', text):
            m = re.search(r'(?s)P:\s*(.*?)\nR:\s*(.*)', blk)
            if m: cards.append((m.group(1), re.sub(r'\n>.*', '', m.group(2))))
    return [{'id': f'c{i+1}', 'f': inline(a), 'v': inline(b)} for i, (a, b) in enumerate(cards)]

# ───────── questões ─────────
def tag_repete(s):
    m = re.search(r'\[REPETE([^\]]*)\]', s)
    ref = m.group(1).strip(' —-') if m else ''
    return re.sub(r'\s*\[REPETE[^\]]*\]', '', s).strip(), bool(m), ref

def bloco_nome(h):
    return re.sub(r'\(\d+ questões\)', '', h).strip()

def parse_q_d05e(text):
    qs, bloco, cur = [], None, None
    for ln in text.split('\n'):
        if ln.startswith('## '):
            if cur: qs.append(cur); cur = None
            bloco = bloco_nome(ln[3:]); continue
        if ln.startswith('### '):
            if cur: qs.append(cur)
            cur = {'bloco': bloco, 'title': ln[4:].strip(), 'body': []}; continue
        if cur is not None: cur['body'].append(ln)
    if cur: qs.append(cur)
    out = []
    for q in qs:
        if q['bloco'].upper().startswith(('TOP 5', 'ARQUIVOS')): continue
        title, rep, ref = tag_repete(q['title'])
        m = re.match(r'(AT|Q)(\d+)-(I+) — (.*)$', title)
        pref, num, un, tema = m.groups()
        body = clean_lines('\n'.join(q['body']))
        gi = body.find('**Gabarito:')
        enun = body[:gi].strip(); rest = body[gi:]
        g = re.match(r'\*\*Gabarito: ([A-E])\*\*\s*(?:\((.*?)\))?\s*\n?(.*)', rest, re.S)
        out.append({'id': f'{pref}{num}-{un}', 'bloco': q['bloco'], 'num': f'{pref}{num}',
                    'tema': tema, 'enun': inline(enun), 'gab': g.group(1), 'gabLabel': g.group(2) or '',
                    'html': inline(g.group(3)) if g.group(3).strip() else '', 'repete': rep, 'repeteRef': ref, 'coment': []})
    return out

def parse_q_803x(text):
    out, sint, bloco = [], [], None
    for ln in text.split('\n'):
        if ln.startswith('## '):
            bloco = ln[3:].strip(); continue
        m = re.match(r'\*\*Q(\d+) → ([A-E])\*\* — (.*)$', ln)
        if m:
            t, rep, ref = tag_repete(m.group(3))
            mod = re.match(r'MÓDULO (\d+)', bloco).group(1)
            out.append({'id': f'M{mod}-Q{m.group(1)}', 'bloco': bloco, 'num': f'Q{m.group(1)}', 'tema': '',
                        'enun': '', 'gab': m.group(2), 'gabLabel': '', 'html': inline(t), 'repete': rep, 'repeteRef': ref, 'coment': []})
            continue
        m = re.match(r'\*\*Mod\. (\d+)\*\* — ([^:]+): (.*)$', ln)
        if m:
            sint.append({'titulo': f'Módulo {m.group(1)} — {m.group(2)}', 'html': inline(m.group(3))})
    return out, sint

def parse_q_883x(text):
    out, bloco, cur = [], None, None
    for ln in text.split('\n'):
        if ln.startswith('## '):
            bloco = ln[3:].strip(); cur = None; continue
        m = re.match(r'\*\*Q(\d+) — \[([A-E])\]\*\* (.*)$', ln)
        if m:
            mod = re.match(r'MÓDULO (\d+)', bloco).group(1)
            cur = {'id': f'M{mod}-Q{m.group(1)}', 'bloco': bloco, 'num': f'Q{m.group(1)}', 'tema': '', 'enun': '',
                   'gab': m.group(2), 'gabLabel': '', 'html': inline(m.group(3)), 'repete': False, 'repeteRef': '', 'coment': []}
            out.append(cur); continue
        if cur is not None and ln.startswith('>'):
            c = ln[1:].strip()
            if c.startswith('[REPETE'):
                cur['repete'] = True
                cur['repeteRef'] = re.sub(r'^\[REPETE\]\s*—?\s*', '', c).strip()
            elif c:
                cur['coment'].append(inline(c))
    return out

def parse_q_18a1(text):
    out = []
    for title, body in sections(text):
        mm = re.match(r'MÓDULO (\d+)', title)
        if not mm: continue
        mod = mm.group(1)
        gm = re.search(r'\(Gabarito: ([A-E ]+)\)', body)
        header = gm.group(1).split() if gm else []
        letters = []
        for m in re.finditer(r'(?m)^\*\*Q(\d+) → ([A-E])\*\*\s*(\[REPETE[^\]]*\])?\s*\|\s*(.*)$', body):
            t = m.group(4); rep = bool(m.group(3)); ref = ''
            if m.group(3): ref = re.sub(r'\[REPETE|\]', '', m.group(3)).strip()
            t, r2, ref2 = tag_repete(t)
            if r2: rep, ref = True, ref2
            tema = ''
            tm = re.match(r'Tema: (.*?)\. (.*)$', t)
            if tm: tema, t = tm.group(1), tm.group(2)
            letters.append(m.group(2))
            out.append({'id': f'M{mod}-Q{m.group(1)}', 'bloco': title, 'num': f'Q{m.group(1)}', 'tema': tema, 'enun': '',
                        'gab': m.group(2), 'gabLabel': '', 'html': inline(t), 'repete': rep, 'repeteRef': ref, 'coment': []})
        if header and header != letters:
            AVISOS.append(f'18A1 Módulo {mod}: letras do cabeçalho diferem das letras por questão: {header} vs {letters}')
        elif header:
            print(f'   18A1 M{mod}: cabeçalho de gabarito confere com as {len(letters)} questões')
    return out

D05E_T = ['Gênero discursivo jurídico','Formações imaginárias (Pêcheux)','Tese primária e teses secundárias',
 'Estrutura do texto argumentativo','Convencer, persuadir e dissuadir','Lugares da argumentação (Perelman)',
 'Hierarquia de valores','Heterogeneidade discursiva','Estratégias argumentativas','Lógica jurídica e dialética',
 'Artigos de lei citados','Pegadinhas e erros clássicos']
A883_T = ['Princípios da Administração (LIMPE)','Poderes administrativos','Atos administrativos','Organização administrativa',
 'Licitação (Lei 14.133/2021)','Contratos administrativos','Servidor público']

CFG = {
 'D05E': {'titulos': D05E_T, 'prob': {1:'media',2:'alta',3:'alta',4:'media',5:'alta',6:'alta',7:'alta',8:'media',9:'media',10:'media',11:'media',12:'alta'}},
 '803X': {'titulos': None, 'prob': {1:'alta',2:'alta',3:'alta',4:'alta',5:'media',6:'media',7:'media',8:'alta'}},
 '883X': {'titulos': A883_T, 'prob': {1:'alta',2:'alta',3:'alta',4:'alta',5:'media',6:'media',7:'alta'}},
 '18A1': {'titulos': None, 'prob': {1:'media',2:'alta',3:'media',4:'alta',5:'media',6:'alta',7:'alta',8:'alta'}},
}
EXPECT = {'D05E': (12, 28, 20), '803X': (8, 54, 20), '883X': (7, 96, 20), '18A1': (8, 144, 20)}

COBERTURA = {
 'D05E': ['As videoaulas 3 e 4 de cada unidade não foram lidas uma a uma. O resumo presume que repetem o que já está nos slides e livros.',
          'Os arquivos de questões trazem tema, gabarito e comentário. Enunciados e alternativas completas não vieram.'],
 '803X': ['As questões comentadas vêm só dos Módulos 1 a 3. Dos Módulos 4 a 8 há apenas uma síntese, sem as questões.',
          'Os arquivos trazem gabarito e comentário. Enunciados e alternativas completas não vieram.'],
 '883X': ['São 96 questões (8 módulos de 12), com gabarito e comentário. Enunciados e alternativas completas não vieram.',
          'A revisão usa a Lei 14.133/2021, mas várias questões do AVA ainda se baseiam na Lei 8.666/1993.'],
 '18A1': ['O próprio arquivo avisa: onde o texto completo da questão não foi extraído, o comentário se baseia no gabarito e no conteúdo do módulo. Parte dos comentários, portanto, é dedução e não texto do AVA.',
          'Os arquivos trazem gabarito e comentário. Enunciados e alternativas completas não vieram.'],
}
COMUM = 'Este material não passou por conferência automática nem por auditoria independente. As frases não trazem citação literal da fonte.'

NOTAS = {
 'D05E': [
  dict(esc='questao', ref='AT3-I', titulo='Gabarito possivelmente trocado', texto='O comentário diz que a Q3 do Questionário I tem gabarito D, mas a Q3-I está registrada como C neste mesmo material. Uma das duas informações está errada. Confira no AVA.'),
  dict(esc='questao', ref='Q3-I', titulo='Gabarito possivelmente trocado', texto='A Q3-I está como C aqui, mas o comentário da AT3-I a cita como D. Confira no AVA.'),
 ],
 '803X': [
  dict(esc='revisao', ref='r7', titulo='Ponto em que a doutrina diverge', texto='O material trata legitimidade e interesse como “pressupostos processuais” e diz que o CPC abandonou a teoria eclética. Muitos autores veem legitimidade e interesse como requisitos de admissibilidade do mérito (art. 17 e art. 485, VI, do CPC), e a possibilidade jurídica do pedido deixou de ser condição. Em prova objetiva, siga a formulação do AVA.'),
  dict(esc='card', ref='c16', titulo='Ponto em que a doutrina diverge', texto='Mesmo ponto do Módulo 7: classificar legitimidade e interesse como “pressupostos processuais” é uma leitura do material. Siga o AVA.'),
  dict(esc='revisao', ref='r8', titulo='Artigo citado fora do lugar', texto='Na lista de competência absoluta aparece “territorial art. 47, §1º”. O §1º trata da opção do autor em certos casos. A competência absoluta da possessória imobiliária está no §2º, como no flashcard.'),
 ],
 '883X': [
  dict(esc='card', ref='c20', titulo='Artigo da Lei 8.112 provavelmente errado', texto='A regra de que a absolvição criminal por inexistência do fato ou negativa de autoria afasta a responsabilidade administrativa está no art. 126 da Lei 8.112/90. O art. 125 trata da independência das instâncias.'),
  dict(esc='card', ref='c17', titulo='Regra de aposentadoria que mudou', texto='A EC 103/2019 passou a chamar a invalidez de incapacidade permanente e alterou o cálculo dos proventos (integrais, em regra, só em acidente de trabalho, doença profissional e doença do trabalho). A versão “proporcionais, salvo doença grave” é a regra antiga. Veja qual versão o AVA cobra.'),
  dict(esc='revisao', ref='r7', titulo='Regra de aposentadoria que mudou', texto='Mesma observação do flashcard sobre aposentadoria por invalidez: a EC 103/2019 mudou a regra. Veja qual versão o AVA cobra.'),
  dict(esc='revisao', ref='r5', titulo='Valores de dispensa desatualizados', texto='Os valores de R$ 100 mil e R$ 50 mil são os originais da lei. Desde 1º/01/2026, pelo Decreto 12.807/2025, são R$ 130.984,20 (obras e engenharia) e R$ 65.492,11 (demais serviços e compras). Para a prova, vale o que o AVA disser.'),
  dict(esc='questao', ref='M1-Q2', titulo='Gabarito do AVA diverge do comentário', texto='O arquivo diz que a plataforma marcava E, mas adota A pela doutrina. Se a prova seguir o gabarito do AVA, a resposta esperada pode ser outra. Confira qual vale.'),
  dict(esc='questao', ref='M6-Q1', titulo='Questão baseada na Lei 8.666/93', texto='A Lei 8.666/93 foi revogada pela Lei 14.133/21. O comentário usa a lei antiga. Siga o gabarito do AVA.'),
  dict(esc='questao', ref='M6-Q6', titulo='Questão baseada na Lei 8.666/93', texto='Cita o art. 24, X, da Lei 8.666. Na lei nova, a dispensa está no art. 75. Siga o gabarito do AVA.'),
  dict(esc='questao', ref='M6-Q9', titulo='Questão baseada na Lei 8.666/93', texto='Lista modalidades da lei antiga (convite etc.). A Lei 14.133 extinguiu convite e tomada de preços. Siga o gabarito do AVA.'),
  dict(esc='questao', ref='M6-Q11', titulo='Questão baseada na Lei 8.666/93', texto='O valor de R$ 1,5 milhão é da lei antiga. Siga o gabarito do AVA.'),
 ],
 '18A1': [
  dict(esc='revisao', ref='r7', titulo='Contradiz os flashcards', texto='O resumo diz que mudança de objeto, fusão e dissolução na Ltda exigem unanimidade. O flashcard 20 e a Q16 do Módulo 7 dizem 3/4 do capital, que é o que consta nos arts. 1.071 e 1.076 do CC. Confira no AVA.'),
  dict(esc='card', ref='c13', titulo='Cessão de quotas: regra mais precisa', texto='O art. 1.057 do CC permite a cessão a outro sócio sem consulta, e a estranho se não houver oposição de titulares de mais de 1/4 do capital. “Aprovação de 3/4” é uma simplificação. Veja como o AVA formula.'),
  dict(esc='questao', ref='M7-Q2', titulo='Cessão de quotas: regra mais precisa', texto='Mesma observação do flashcard 13 (art. 1.057 do CC).'),
  dict(esc='card', ref='c20', titulo='Erro de digitação e mesma observação', texto='“Cessar de quotas” deve ser cessão de quotas. Para o quórum, veja a observação do flashcard 13.'),
  dict(esc='card', ref='c2', titulo='Limite do MEI', texto='O teto de R$ 81 mil segue vigente em 2026. Há notícia de lei sancionada que o eleva a R$ 110 mil em 2027 e R$ 140 mil em 2028. Para a prova de 2026, vale o R$ 81 mil.'),
  dict(esc='questao', ref='M2-Q3', titulo='EIRELI foi extinta', texto='A Lei 14.195/21 extinguiu a EIRELI e a transformou em sociedade limitada unipessoal (como diz a Q18 do Módulo 6). Questão histórica do AVA. Siga o gabarito.'),
  dict(esc='questao', ref='M2-Q4', titulo='EIRELI foi extinta', texto='As regras de nome e capital citadas valiam para a EIRELI, extinta pela Lei 14.195/21. Siga o gabarito do AVA.'),
  dict(esc='questao', ref='M4-Q12', titulo='Lei citada provavelmente errada', texto='A topografia de circuito integrado tem lei própria (Lei 11.484/2007), não o art. 25 da LPI. Tema de baixa prioridade.'),
  dict(esc='questao', ref='M8-Q15', titulo='Frase confusa', texto='A regra é: a companhia precisa de pelo menos dois acionistas, salvo a subsidiária integral, cujo único acionista é sociedade brasileira (art. 251 da LSA). O comentário está mal redigido.'),
 ],
}

def build(cod):
    cfg = CFG[cod]
    print(f'→ {cod}')
    rev, top5 = parse_revisao(cod, cfg)
    cards = parse_cards(cod)
    qtxt = (SRC/cod/'questoes_comentadas.md').read_text(encoding='utf-8')
    sint = []
    if cod == 'D05E': qs = parse_q_d05e(qtxt)
    elif cod == '803X': qs, sint = parse_q_803x(qtxt)
    elif cod == '883X': qs = parse_q_883x(qtxt)
    else: qs = parse_q_18a1(qtxt)
    er, eq, ec = EXPECT[cod]
    for nome, got, exp in (('tópicos', len(rev), er), ('questões', len(qs), eq), ('flashcards', len(cards), ec)):
        flag = '' if got == exp else '   <<< DIFERENTE DO ESPERADO'
        print(f'   {nome}: {got} (esperado {exp}){flag}')
        if got != exp: AVISOS.append(f'{cod}: {nome} = {got}, esperado {exp}')
    ids = [q['id'] for q in qs]
    if len(ids) != len(set(ids)): AVISOS.append(f'{cod}: ids de questão duplicados')
    notas = NOTAS.get(cod, [])
    refs = set(ids) | {r['id'] for r in rev} | {c['id'] for c in cards}
    for n in notas:
        if n['ref'] not in refs: AVISOS.append(f"{cod}: nota aponta para id inexistente {n['ref']}")
    data = {'cod': cod, 'revisao': rev, 'top5': top5, 'questoes': qs, 'sinteses': sint, 'cards': cards,
            'cobertura': COBERTURA[cod] + [COMUM], 'notas': notas}
    (OUT/f'{cod}.js').write_text('window.DADOS=window.DADOS||{};window.DADOS["%s"]=%s;' % (cod, json.dumps(data, ensure_ascii=False)), encoding='utf-8')

if __name__ == '__main__':
    for cod in CFG: build(cod)
    print('\nAVISOS:' if AVISOS else '\nSem avisos de contagem/consistência.')
    for a in AVISOS: print(' !', a)
    if '--single' in sys.argv:
        (ROOT/'dist').mkdir(exist_ok=True)
        page = (ROOT/'index.html').read_text(encoding='utf-8')
        css = (ROOT/'assets/style.css').read_text(encoding='utf-8')
        page = page.replace('<link rel="stylesheet" href="assets/style.css">', f'<style>{css}</style>')
        datas = ''.join(f'<script>{(OUT/f"{c}.js").read_text(encoding="utf-8")}</script>' for c in CFG)
        app = (ROOT/'assets/app.js').read_text(encoding='utf-8')
        page = re.sub(r'<script src="data/[^"]+"></script>\s*', '', page)
        page = page.replace('<script src="assets/app.js"></script>', datas + f'<script>{app}</script>')
        (ROOT/'dist/portal.html').write_text(page, encoding='utf-8')
        print('dist/portal.html gerado')
