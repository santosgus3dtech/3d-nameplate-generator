import os
import re
import uuid
import zipfile
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

import segno
import trimesh


# =========================
# CONFIGURAÇÕES GERAIS
# =========================

BASE_DIR = Path(__file__).resolve().parent

OPENSCAD_PATH = os.getenv(
    "OPENSCAD_PATH",
    r"C:\Program Files (x86)\OpenSCAD\openscad.exe",
)

ARQUIVO_BASE_SCAD = BASE_DIR / "modelo_base.scad"
ARQUIVO_NOME_SCAD = BASE_DIR / "modelo_nome.scad"

PASTA_SAIDA = BASE_DIR / "saida_3mf"
PASTA_TEMP = BASE_DIR / "temp"
PASTA_QR_SCADS = PASTA_TEMP / "qr_scads"
PASTA_STLS = PASTA_TEMP / "stls"


# =========================
# MEDIDAS PADRÃO
# =========================

ALTURA_PLACA = 105
ESPESSURA_BASE = 3

LARGURA_MINIMA_PLACA = 80

TAMANHO_TEXTO = 10
MARGEM_LATERAL_TEXTO = 30

QR_TAMANHO_PADRAO = 58
QR_POS_Y = 16
ALTURA_QR = 1.0

BORDA_BRANCA = 4


# =========================
# CORES PADRÃO
# =========================

COR_PLACA_PADRAO = "#FFFFFFFF"
COR_DETALHE_PADRAO = "#111111FF"


# =========================
# FUNÇÕES AUXILIARES
# =========================

def preparar_pastas():
    PASTA_SAIDA.mkdir(exist_ok=True)
    PASTA_TEMP.mkdir(exist_ok=True)
    PASTA_QR_SCADS.mkdir(exist_ok=True)
    PASTA_STLS.mkdir(exist_ok=True)


def validar_openscad():
    caminho = Path(OPENSCAD_PATH)

    if not caminho.exists():
        raise FileNotFoundError(
            f"OpenSCAD não encontrado em: {OPENSCAD_PATH}"
        )

    return str(caminho)


def limpar_nome_arquivo(texto: str) -> str:
    texto = texto.strip()
    texto = re.sub(r'[\\/*?:"<>|]', "_", texto)
    texto = texto.replace(" ", "_")
    return texto or "placa"


def escapar_scad_string(texto: str) -> str:
    return texto.replace("\\", "\\\\").replace('"', '\\"')


def normalizar_cor(cor: str, padrao: str) -> str:
    if not cor:
        return padrao

    cor = cor.strip()

    if not cor.startswith("#"):
        cor = "#" + cor

    if len(cor) == 7:
        cor = cor + "FF"

    if len(cor) != 9:
        return padrao

    return cor.upper()


def calcular_largura_texto(nome: str) -> float:
    largura_total = 0

    for caractere in nome:
        if caractere == " ":
            fator = 0.38
        elif caractere in "ilI.,:;!|":
            fator = 0.34
        elif caractere in "mwMW":
            fator = 1.00
        elif caractere in "ABCDEFGHJKLMNOPQRSTUVWXYZ":
            fator = 0.82
        elif caractere in "0123456789":
            fator = 0.72
        else:
            fator = 0.66

        largura_total += fator * TAMANHO_TEXTO

    return largura_total


def calcular_largura_placa(nome: str, qr_tamanho: float) -> float:
    largura_texto = calcular_largura_texto(nome)

    largura_por_texto = largura_texto + (MARGEM_LATERAL_TEXTO * 2)
    largura_por_qr = qr_tamanho + 32

    return max(
        LARGURA_MINIMA_PLACA,
        largura_por_texto,
        largura_por_qr
    )


def rodar_openscad(comando: list[str], descricao: str):
    resultado = subprocess.run(
        comando,
        capture_output=True,
        text=True
    )

    if resultado.returncode != 0:
        raise RuntimeError(
            f"Erro ao gerar {descricao}:\n{resultado.stderr}"
        )


# =========================
# QR EM BLOCOS 3D
# =========================

def gerar_scad_qr(
    nome_arquivo: str,
    conteudo_qr: str,
    largura_placa: float,
    qr_tamanho: float
) -> Path:
    arquivo_scad = PASTA_QR_SCADS / f"{nome_arquivo}_qr.scad"

    qr = segno.make(conteudo_qr, error="L", micro=False)

    matriz = list(qr.matrix)
    qtd_modulos = len(matriz)

    total_com_borda = qtd_modulos + (BORDA_BRANCA * 2)
    tamanho_modulo = qr_tamanho / total_com_borda

    qr_pos_x = (largura_placa - qr_tamanho) / 2

    linhas = []
    linhas.append("$fn = 12;")
    linhas.append("union() {")

    for y, linha in enumerate(matriz):
        x = 0

        while x < qtd_modulos:
            if not linha[x]:
                x += 1
                continue

            inicio = x

            while x < qtd_modulos and linha[x]:
                x += 1

            comprimento = x - inicio

            pos_x = qr_pos_x + (inicio + BORDA_BRANCA) * tamanho_modulo
            pos_y = QR_POS_Y + (qtd_modulos - y - 1 + BORDA_BRANCA) * tamanho_modulo

            largura_bloco = comprimento * tamanho_modulo

            linhas.append(
                f"    translate([{pos_x:.6f}, {pos_y:.6f}, {ESPESSURA_BASE:.6f}]) "
                f"cube([{largura_bloco:.6f}, {tamanho_modulo:.6f}, {ALTURA_QR:.6f}]);"
            )

    linhas.append("}")

    arquivo_scad.write_text("\n".join(linhas), encoding="utf-8")
    return arquivo_scad


# =========================
# 3MF
# =========================

def carregar_malha_stl(caminho_stl: Path) -> trimesh.Trimesh:
    malha = trimesh.load_mesh(str(caminho_stl), force="mesh")

    if isinstance(malha, trimesh.Scene):
        geometrias = list(malha.geometry.values())

        if not geometrias:
            raise ValueError(f"STL vazio: {caminho_stl}")

        malha = trimesh.util.concatenate(geometrias)

    if malha.is_empty:
        raise ValueError(f"STL vazio: {caminho_stl}")

    malha.merge_vertices()

    return malha


def malha_para_xml_3mf(
    malha: trimesh.Trimesh,
    object_id: int,
    color_group_id: int,
    color_index: int,
    object_name: str
) -> str:
    linhas = []

    linhas.append(
        f'<object id="{object_id}" type="model" pid="{color_group_id}" pindex="{color_index}">'
    )
    linhas.append(f'<metadata name="Title">{xml_escape(object_name)}</metadata>')
    linhas.append("<mesh>")
    linhas.append("<vertices>")

    for x, y, z in malha.vertices:
        linhas.append(
            f'<vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>'
        )

    linhas.append("</vertices>")
    linhas.append("<triangles>")

    for v1, v2, v3 in malha.faces:
        linhas.append(
            f'<triangle v1="{int(v1)}" v2="{int(v2)}" v3="{int(v3)}" '
            f'pid="{color_group_id}" p1="{color_index}" p2="{color_index}" p3="{color_index}"/>'
        )

    linhas.append("</triangles>")
    linhas.append("</mesh>")
    linhas.append("</object>")

    return "\n".join(linhas)


def criar_3mf(
    caminho_3mf: Path,
    caminho_base_stl: Path,
    caminho_nome_stl: Path,
    caminho_qr_stl: Path,
    cor_placa: str,
    cor_detalhe: str
):
    malha_base = carregar_malha_stl(caminho_base_stl)
    malha_nome = carregar_malha_stl(caminho_nome_stl)
    malha_qr = carregar_malha_stl(caminho_qr_stl)

    color_group_id = 1

    objeto_base_id = 2
    objeto_nome_id = 3
    objeto_qr_id = 4

    xml_base = malha_para_xml_3mf(
        malha_base,
        object_id=objeto_base_id,
        color_group_id=color_group_id,
        color_index=0,
        object_name="Placa"
    )

    xml_nome = malha_para_xml_3mf(
        malha_nome,
        object_id=objeto_nome_id,
        color_group_id=color_group_id,
        color_index=1,
        object_name="Nome"
    )

    xml_qr = malha_para_xml_3mf(
        malha_qr,
        object_id=objeto_qr_id,
        color_group_id=color_group_id,
        color_index=1,
        object_name="QR Code"
    )

    modelo_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter"
       xml:lang="en-US"
       xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
       xmlns:m="http://schemas.microsoft.com/3dmanufacturing/material/2015/02"
       requiredextensions="m">

    <metadata name="Application">Gerador de Placas Imagine3D</metadata>

    <resources>
        <m:colorgroup id="{color_group_id}">
            <m:color color="{cor_placa}"/>
            <m:color color="{cor_detalhe}"/>
        </m:colorgroup>

        {xml_base}

        {xml_nome}

        {xml_qr}
    </resources>

    <build>
        <item objectid="{objeto_base_id}"/>
        <item objectid="{objeto_nome_id}"/>
        <item objectid="{objeto_qr_id}"/>
    </build>
</model>
'''

    content_types_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
</Types>
'''

    rels_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Target="/3D/3dmodel.model"
                  Id="rel0"
                  Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>
'''

    with zipfile.ZipFile(caminho_3mf, "w", compression=zipfile.ZIP_DEFLATED) as pacote:
        pacote.writestr("[Content_Types].xml", content_types_xml)
        pacote.writestr("_rels/.rels", rels_xml)
        pacote.writestr("3D/3dmodel.model", modelo_xml)


# =========================
# FUNÇÃO PRINCIPAL
# =========================

def gerar_placa_3mf(
    nome: str,
    conteudo_qr: str,
    cor_placa: str = COR_PLACA_PADRAO,
    cor_detalhe: str = COR_DETALHE_PADRAO,
    qr_tamanho: float = QR_TAMANHO_PADRAO
) -> Path:
    preparar_pastas()

    openscad = validar_openscad()

    nome = nome.strip() or "Imagine3D"
    conteudo_qr = conteudo_qr.strip() or "https://instagram.com/imagine3d"

    cor_placa = normalizar_cor(cor_placa, COR_PLACA_PADRAO)
    cor_detalhe = normalizar_cor(cor_detalhe, COR_DETALHE_PADRAO)

    qr_tamanho = float(qr_tamanho)
    qr_tamanho = max(42, min(qr_tamanho, 70))

    largura_placa = calcular_largura_placa(nome, qr_tamanho)

    id_execucao = uuid.uuid4().hex[:8]
    nome_limpo = limpar_nome_arquivo(nome)
    prefixo = f"{nome_limpo}_{id_execucao}"

    caminho_base_stl = PASTA_STLS / f"{prefixo}_base.stl"
    caminho_nome_stl = PASTA_STLS / f"{prefixo}_nome.stl"
    caminho_qr_stl = PASTA_STLS / f"{prefixo}_qr.stl"

    caminho_3mf = PASTA_SAIDA / f"{prefixo}.3mf"

    nome_escapado = escapar_scad_string(nome)

    comando_base = [
        openscad,
        "-o",
        str(caminho_base_stl),
        "-D",
        f"largura={largura_placa:.2f}",
        "-D",
        f"altura={ALTURA_PLACA:.2f}",
        str(ARQUIVO_BASE_SCAD)
    ]

    comando_nome = [
        openscad,
        "-o",
        str(caminho_nome_stl),
        "-D",
        f'nome="{nome_escapado}"',
        "-D",
        f"largura={largura_placa:.2f}",
        "-D",
        f"altura={ALTURA_PLACA:.2f}",
        str(ARQUIVO_NOME_SCAD)
    ]

    scad_qr = gerar_scad_qr(
        nome_arquivo=prefixo,
        conteudo_qr=conteudo_qr,
        largura_placa=largura_placa,
        qr_tamanho=qr_tamanho
    )

    comando_qr = [
        openscad,
        "-o",
        str(caminho_qr_stl),
        str(scad_qr)
    ]

    rodar_openscad(comando_base, "base")
    rodar_openscad(comando_nome, "nome")
    rodar_openscad(comando_qr, "QR Code")

    criar_3mf(
        caminho_3mf=caminho_3mf,
        caminho_base_stl=caminho_base_stl,
        caminho_nome_stl=caminho_nome_stl,
        caminho_qr_stl=caminho_qr_stl,
        cor_placa=cor_placa,
        cor_detalhe=cor_detalhe
    )

    return caminho_3mf
