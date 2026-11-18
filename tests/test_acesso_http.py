"""Testa as rotas reais do Gradio em memória, sem chamar serviços de IA."""

from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from autenticacao import criar_app
from projeto import demo
from usuarios import BancoUsuarios


class AcessoHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pasta = tempfile.TemporaryDirectory()
        cls.addClassCleanup(pasta.cleanup)
        cls.caminho_banco = Path(pasta.name) / "usuarios.sqlite3"
        banco = BancoUsuarios(cls.caminho_banco)
        banco.cadastrar("apresentacao", "senha-de-teste", "senha-de-teste")
        cls.app = criar_app(demo, caminho_banco=cls.caminho_banco)

    def setUp(self):
        self.cliente = TestClient(self.app)
        self.addCleanup(self.cliente.close)

    def entrar(self, cliente):
        resposta = cliente.post("/login", data={"username": "apresentacao", "password": "senha-de-teste"})
        self.assertEqual(resposta.status_code, 200)

    def test_bloqueia_interface_e_atividades_sem_login(self):
        pagina = self.cliente.get("/")
        self.assertEqual(pagina.status_code, 200)
        self.assertIn("ecoleitura-login", pagina.text)
        self.assertIn("/cadastro", pagina.text)
        self.assertEqual(self.cliente.get("/config").status_code, 401)
        resposta = self.cliente.post("/gradio_api/queue/join", json={"data": [], "session_hash": "sem-login", "fn_index": 0})
        self.assertEqual(resposta.status_code, 401)

    def test_rejeita_senha_incorreta(self):
        resposta = self.cliente.post("/login", data={"username": "apresentacao", "password": "incorreta"})
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(self.cliente.get("/config").status_code, 401)

    def test_login_libera_interface_e_sair_revoga_sessao(self):
        self.entrar(self.cliente)
        self.assertEqual(self.cliente.get("/config").status_code, 200)
        self.cliente.get("/logout?all_session=false")
        self.assertEqual(self.cliente.get("/config").status_code, 401)

    def test_sair_preserva_outra_sessao(self):
        with TestClient(self.app) as outro:
            self.entrar(self.cliente)
            self.entrar(outro)
            self.cliente.get("/logout?all_session=false")
            self.assertEqual(self.cliente.get("/config").status_code, 401)
            self.assertEqual(outro.get("/config").status_code, 200)

    def test_cadastro_publico_cria_conta_que_pode_fazer_login(self):
        self.assertEqual(self.cliente.get("/cadastro").status_code, 200)
        resposta = self.cliente.post(
            "/cadastro", follow_redirects=False,
            data={"usuario": "nova-conta", "senha": "senha-nova-conta", "confirmacao": "senha-nova-conta"},
        )
        self.assertEqual(resposta.status_code, 303)
        sucesso = self.cliente.get(resposta.headers["location"])
        self.assertIn("Conta criada!", sucesso.text)
        self.assertNotIn("senha-nova-conta", sucesso.text)
        # O cadastro não abre as atividades antes da autenticação.
        self.assertEqual(self.cliente.get("/config").status_code, 401)
        login = self.cliente.post("/login", data={"username": "nova-conta", "password": "senha-nova-conta"})
        self.assertEqual(login.status_code, 200)
        self.assertEqual(self.cliente.get("/config").status_code, 200)

    def test_cadastro_repetido_e_confirmacao_incorreta_mostram_mensagem(self):
        casos = [
            ({"usuario": "apresentacao", "senha": "outra-senha", "confirmacao": "outra-senha"}, "já está em uso"),
            ({"usuario": "confirmacao", "senha": "senha-valida", "confirmacao": "outra-senha"}, "não coincidem"),
        ]
        for dados, mensagem in casos:
            with self.subTest(usuario=dados["usuario"]):
                resposta = self.cliente.post("/cadastro", data=dados)
                self.assertEqual(resposta.status_code, 400)
                self.assertIn(mensagem, resposta.text)
                self.assertNotIn('value="outra-senha"', resposta.text)

    def test_banco_de_usuarios_nao_e_disponibilizado_pelo_servidor(self):
        self.entrar(self.cliente)
        resposta = self.cliente.get("/gradio_api/file=" + self.caminho_banco.as_posix())
        self.assertEqual(resposta.status_code, 403)

    def test_usuario_invalido_e_exibido_com_escape_html(self):
        resposta = self.cliente.post(
            "/cadastro", data={"usuario": '<script>alert(1)</script>', "senha": "senha-valida", "confirmacao": "senha-valida"},
        )
        self.assertEqual(resposta.status_code, 400)
        self.assertNotIn("<script>alert(1)</script>", resposta.text)
        self.assertIn("&lt;script&gt;", resposta.text)


if __name__ == "__main__":
    unittest.main()
