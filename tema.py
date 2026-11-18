"""Inclui o seletor de tema em todas as páginas, inclusive antes do login."""

from pathlib import Path

from fastapi.responses import FileResponse, Response


PASTA = Path(__file__).resolve().parent
CABECALHO_TEMA = '<link rel="stylesheet" href="/tema.css"><script src="/tema.js"></script><script src="/interface.js" defer></script>'


def instalar_tema(app):
    @app.get("/interface.js", include_in_schema=False)
    def script_interface():
        return FileResponse(PASTA / "interface.js", media_type="text/javascript", headers={"Cache-Control": "no-cache"})

    @app.get("/tema.css", include_in_schema=False)
    def estilos_tema():
        return FileResponse(PASTA / "tema.css", media_type="text/css", headers={"Cache-Control": "no-cache"})

    @app.get("/tema.js", include_in_schema=False)
    def script_tema():
        return FileResponse(PASTA / "tema.js", media_type="text/javascript", headers={"Cache-Control": "no-cache"})

    @app.middleware("http")
    async def incluir_tema(request, proxima):
        resposta = await proxima(request)
        if request.url.path not in {"/", "/cadastro"} or "text/html" not in resposta.headers.get("content-type", ""):
            return resposta

        # O Gradio não inclui seu parâmetro `head` na tela anterior ao login.
        # Incluímos os mesmos recursos nas páginas HTML públicas e autenticadas.
        corpo = b"".join([parte async for parte in resposta.body_iterator])
        corpo = corpo.replace(b"</head>", CABECALHO_TEMA.encode("utf-8") + b"</head>", 1)
        cabecalhos = dict(resposta.headers)
        cabecalhos.pop("content-length", None)
        return Response(corpo, status_code=resposta.status_code, headers=cabecalhos)
