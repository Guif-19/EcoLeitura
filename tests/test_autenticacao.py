"""Verifica cadastro, persistência e proteção das senhas sem acessar serviços externos."""

from pathlib import Path
import sqlite3
import tempfile
import unittest

from usuarios import BancoUsuarios


class AutenticacaoTests(unittest.TestCase):
    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.caminho = Path(pasta.name) / "usuarios.sqlite3"
        self.banco = BancoUsuarios(self.caminho)

    def test_aceita_apenas_credenciais_corretas(self):
        self.banco.cadastrar("aluno", "Senha-de-teste!", "Senha-de-teste!")
        self.assertTrue(self.banco.autenticar("aluno", "Senha-de-teste!"))
        self.assertFalse(self.banco.autenticar("outro", "Senha-de-teste!"))
        self.assertFalse(self.banco.autenticar("aluno", "senha-de-teste!"))
        self.assertFalse(self.banco.autenticar("aluno", "Senha-de-teste! "))
        self.assertFalse(self.banco.autenticar(None, None))

    def test_conta_continua_disponivel_apos_reabrir_banco(self):
        self.banco.cadastrar("Aluno", "Árvore-segura!", "Árvore-segura!")
        reaberto = BancoUsuarios(self.caminho)
        self.assertTrue(reaberto.autenticar(" ALUNO ", "Árvore-segura!"))
        self.assertFalse(reaberto.autenticar("aluno", "Arvore-segura!"))

    def test_usuario_repetido_nao_substitui_senha(self):
        self.banco.cadastrar("aluno", "senha-original", "senha-original")
        with self.assertRaisesRegex(ValueError, "já está em uso"):
            self.banco.cadastrar(" ALUNO ", "senha-diferente", "senha-diferente")
        self.assertTrue(self.banco.autenticar("aluno", "senha-original"))
        self.assertFalse(self.banco.autenticar("aluno", "senha-diferente"))

    def test_recusa_campos_invalidos_sem_criar_conta(self):
        casos = [
            ("ab", "senha-valida", "senha-valida"),
            ("nome com espaco", "senha-valida", "senha-valida"),
            ("<script>", "senha-valida", "senha-valida"),
            ("aluno", "curta", "curta"),
            ("aluno", " " * 8, " " * 8),
            ("aluno", "s" * 129, "s" * 129),
            ("aluno", "senha-valida", "outra-senha"),
        ]
        for usuario, senha, confirmacao in casos:
            with self.subTest(usuario=usuario, tamanho_senha=len(senha)):
                with self.assertRaises(ValueError):
                    self.banco.cadastrar(usuario, senha, confirmacao)
                self.assertFalse(self.banco.autenticar(usuario, senha))

    def test_senhas_iguais_recebem_hashes_distintos_sem_texto_puro(self):
        senha = "senha-para-teste"
        self.banco.cadastrar("aluno1", senha, senha)
        self.banco.cadastrar("aluno2", senha, senha)
        conexao = sqlite3.connect(self.caminho)
        try:
            registros = conexao.execute("SELECT salt, senha_hash FROM usuarios").fetchall()
        finally:
            conexao.close()
        self.assertNotEqual(registros[0], registros[1])
        self.assertNotIn(senha.encode(), self.caminho.read_bytes())


if __name__ == "__main__":
    unittest.main()
