from pathlib import Path

from fastapi import FastAPI, Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from gerador_3mf import gerar_placa_3mf


BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Gerador de Plaquinhas 3D")

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)

templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {"request": request}
    )


@app.post("/gerar")
def gerar(
    nome: str = Form(...),
    qr: str = Form(...),
    cor_placa: str = Form("#FFFFFF"),
    cor_detalhe: str = Form("#111111"),
    qr_tamanho: float = Form(65)
):
    caminho_3mf = gerar_placa_3mf(
        nome=nome,
        conteudo_qr=qr,
        cor_placa=cor_placa,
        cor_detalhe=cor_detalhe,
        qr_tamanho=qr_tamanho
    )

    return FileResponse(
        path=str(caminho_3mf),
        filename=Path(caminho_3mf).name,
        media_type="model/3mf"
    )