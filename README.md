# Gerador Web de Plaquinhas 3D

Aplicacao FastAPI para gerar plaquinhas 3D personalizadas com nome, QR Code real, preview em Three.js e exportacao `.3mf` para fluxo multicolor em slicers como Bambu Studio e OrcaSlicer.

## O que o projeto mostra

- Backend Python/FastAPI retornando arquivos gerados sob demanda.
- Geracao parametrica com OpenSCAD.
- QR Code convertido em blocos 3D reais com `segno`.
- Montagem manual de pacote `.3mf` com partes e cores separadas.
- Frontend com preview 3D interativo em Three.js.
- Projeto pensado para uso real em um pequeno fluxo de personalizacao/3D printing.

## Stack

- Python, FastAPI, Uvicorn, Jinja2
- OpenSCAD
- segno, trimesh, numpy
- HTML, CSS, JavaScript, Three.js

## Rodando localmente

Instale o OpenSCAD e, se ele estiver fora do caminho padrao no Windows, defina:

```powershell
$env:OPENSCAD_PATH = "C:\Program Files\OpenSCAD\openscad.exe"
```

Depois:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m uvicorn app:app --reload
```

Acesse `http://127.0.0.1:8000`.

## Estrutura

```text
app.py              # Rotas web e download do .3mf
gerador_3mf.py      # Geracao de STL temporario e pacote .3mf
modelo_base.scad    # Base parametrica
modelo_nome.scad    # Texto em relevo
static/             # Preview 3D e estilos
templates/          # Tela principal
```

`saida_3mf/` e `temp/` sao gerados em runtime e ficam fora do Git.

## Portfolio

Este projeto e uma boa vitrine porque junta backend, geometria 3D, empacotamento de arquivo tecnico e UI interativa em um produto pequeno, claro e demonstravel. Veja [docs/portfolio-case-study.md](docs/portfolio-case-study.md).
