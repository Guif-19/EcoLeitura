"""Cadastro público e login do MVP, com sessões gerenciadas pelo Gradio."""

from html import escape
from pathlib import Path

import gradio as gr
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from usuarios import BancoUsuarios, CAMINHO_BANCO
from tema import instalar_tema


# O Gradio não envia o CSS da aplicação antes da autenticação.
# O CSS desta página acompanha a mensagem pública de entrada.
CSS_LOGIN = Path(__file__).with_name("login.css").read_text(encoding="utf-8")
MENSAGEM_LOGIN = "<style>" + CSS_LOGIN + "</style>" + """
<span id="ecoleitura-login">
    <span class="login-simbolo" aria-hidden="true">🌱</span>
    <span class="login-marca" role="heading" aria-level="1">EcoLeitura</span>
    <span class="login-slogan">Melhorando a leitura, cuidando do planeta!</span>
    <span class="login-boas-vindas">Sua aventura começa aqui</span>
    <span class="login-instrucao">
        Entre para começar sua aventura de leitura.
    </span>
    <span class="login-cadastro">Primeiro acesso? <a href="/cadastro">Criar conta</a></span>
</span>
"""


def pagina_cadastro(erro="", usuario="", criado=False):
    """HTML simples, sem serviços externos, para criar uma conta."""
    if criado:
        conteudo = """
            <h1>Conta criada!</h1>
            <p class="cadastro-descricao" role="status">
                Tudo pronto. Agora entre com seu usuário e sua senha.
            </p>
            <a class="cadastro-primario" href="/">Entrar na minha conta</a>
        """
    else:
        aviso = f'<p class="cadastro-erro" role="alert">{escape(erro)}</p>' if erro else ""
        conteudo = f"""
            <h1>Crie sua conta</h1>
            <p class="cadastro-descricao">Vamos começar sua aventura de leitura?</p>
            {aviso}
            <form method="post" action="/cadastro">
                <label for="usuario">Nome de usuário</label>
                <input id="usuario" name="usuario" type="text" autocomplete="username"
                    value="{escape(usuario[:30], quote=True)}" required minlength="3" maxlength="30"
                    pattern="[a-zA-Z0-9_.-]{{3,30}}" aria-describedby="dica-usuario">
                <small id="dica-usuario">De 3 a 30 caracteres: letras sem acento, números, ponto, traço ou sublinhado.</small>
                <label for="senha">Senha</label>
                <input id="senha" name="senha" type="password" autocomplete="new-password"
                    required minlength="8" maxlength="128" aria-describedby="dica-senha">
                <small id="dica-senha">Use pelo menos 8 caracteres.</small>
                <label for="confirmacao">Confirmar senha</label>
                <input id="confirmacao" name="confirmacao" type="password" autocomplete="new-password"
                    required minlength="8" maxlength="128">
                <button class="cadastro-primario" type="submit">Criar minha conta</button>
            </form>
            <p class="cadastro-voltar">Já tem uma conta? <a href="/">Entrar</a></p>
        """
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Criar conta — EcoLeitura</title>
    <style>{CSS_LOGIN}</style>
</head>
<body class="pagina-cadastro">
    <main class="cartao-cadastro">
        <div class="cadastro-marca"><span aria-hidden="true">🌱</span> EcoLeitura</div>
        {conteudo}
    </main>
</body>
</html>"""


def criar_app(demo, caminho_banco=CAMINHO_BANCO, **configuracao_gradio):
    banco = BancoUsuarios(caminho_banco)
    app = FastAPI()
    instalar_tema(app)

    @app.get("/cadastro", response_class=HTMLResponse)
    def mostrar_cadastro(criado: bool = False):
        return HTMLResponse(pagina_cadastro(criado=criado), headers={"Cache-Control": "no-store"})

    @app.post("/cadastro", response_class=HTMLResponse)
    def cadastrar(
        usuario: str = Form(default=""),
        senha: str = Form(default=""),
        confirmacao: str = Form(default=""),
    ):
        try:
            banco.cadastrar(usuario, senha, confirmacao)
        except ValueError as erro:
            return HTMLResponse(
                pagina_cadastro(erro=str(erro), usuario=usuario), status_code=400,
                headers={"Cache-Control": "no-store"},
            )
        # Evita repetir o cadastro ao atualizar a página após o envio.
        return RedirectResponse("/cadastro?criado=true", status_code=303)

    return gr.mount_gradio_app(
        app, demo, path="", auth=banco.autenticar,
        auth_message=MENSAGEM_LOGIN,
        blocked_paths=[str(banco.caminho.resolve().parent), str(Path(__file__).with_name(".env"))],
        **configuracao_gradio,
    )
