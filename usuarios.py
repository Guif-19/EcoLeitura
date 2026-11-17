"""Contas locais do MVP, armazenadas em SQLite com senhas protegidas por hash."""

from contextlib import closing
from hashlib import pbkdf2_hmac
from hmac import compare_digest
from pathlib import Path
import re
import secrets
import sqlite3


CAMINHO_BANCO = Path(__file__).resolve().parent / "dados" / "usuarios.sqlite3"
ITERACOES = 600_000


def normalizar_usuario(usuario):
    return (usuario or "").strip().lower()


class BancoUsuarios:
    def __init__(self, caminho=CAMINHO_BANCO):
        self.caminho = Path(caminho)
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.caminho)) as conexao, conexao:
            conexao.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    usuario TEXT PRIMARY KEY,
                    salt BLOB NOT NULL,
                    senha_hash BLOB NOT NULL,
                    iteracoes INTEGER NOT NULL,
                    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def cadastrar(self, usuario, senha, confirmacao):
        usuario = normalizar_usuario(usuario)
        if not re.fullmatch(r"[a-z0-9_.-]{3,30}", usuario):
            raise ValueError(
                "Use de 3 a 30 caracteres no usuário: letras sem acento, "
                "números, ponto, traço ou sublinhado."
            )
        if not isinstance(senha, str) or not 8 <= len(senha) <= 128 or not senha.strip():
            raise ValueError("A senha deve ter entre 8 e 128 caracteres.")
        if senha != confirmacao:
            raise ValueError("As senhas não coincidem. Digite novamente.")

        salt = secrets.token_bytes(16)
        senha_hash = pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, ITERACOES)
        try:
            with closing(sqlite3.connect(self.caminho)) as conexao, conexao:
                conexao.execute(
                    "INSERT INTO usuarios (usuario, salt, senha_hash, iteracoes) VALUES (?, ?, ?, ?)",
                    (usuario, salt, senha_hash, ITERACOES),
                )
        except sqlite3.IntegrityError as erro:
            raise ValueError("Este usuário já está em uso. Escolha outro.") from erro
        return usuario

    def autenticar(self, usuario, senha):
        if not isinstance(senha, str) or not 8 <= len(senha) <= 128:
            return False
        with closing(sqlite3.connect(self.caminho)) as conexao:
            registro = conexao.execute(
                "SELECT salt, senha_hash, iteracoes FROM usuarios WHERE usuario = ?",
                (normalizar_usuario(usuario),),
            ).fetchone()
        if registro is None:
            return False
        salt, senha_esperada, iteracoes = registro
        senha_hash = pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, iteracoes)
        return compare_digest(senha_hash, senha_esperada)
