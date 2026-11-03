# Estudo UNIP

Portal de revisão para as provas de 3 e 4 de novembro. Sem build no servidor: é HTML, CSS e JS puros.

## Publicar no GitHub Pages
1. Crie um repositório e envie o conteúdo desta pasta (`index.html`, `assets/`, `data/`; `conteudo/` e `build.py` são opcionais).
2. Em Settings > Pages, escolha a branch `main` e a pasta `/ (root)`.
3. O endereço sai em `https://SEU-USUARIO.github.io/NOME-DO-REPO/`.

## Adicionar ou atualizar uma disciplina
1. Coloque `revisao_vespera.md`, `questoes_comentadas.md` e `flashcards.md` em `conteudo/COD/`.
2. Cadastre o código em `CFG`, `EXPECT`, `COBERTURA` e `NOTAS` no `build.py`.
3. Rode `python3 build.py` (precisa do pacote `markdown`). Ele confere as contagens e gera `data/COD.js`.
4. Adicione `<script src="data/COD.js"></script>` no `index.html`.

`python3 build.py --single` gera `dist/portal.html`, um arquivo único que abre direto no navegador.

## Aviso
O material foi gerado a partir dos arquivos do AVA e não passou por auditoria independente.
Os avisos em azul ("Conferir") marcam pontos duvidosos achados na leitura.
