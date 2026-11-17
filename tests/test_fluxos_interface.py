"""Regressões de perda de histórico e de erros apresentados ao usuário."""

import unittest
from unittest.mock import patch

import gradio as gr

import projeto
import servicos


class FluxosInterfaceTests(unittest.TestCase):
    def test_nova_leitura_preserva_atividades_anteriores(self):
        registro = {"data": "17/11/2026", "tema": "Água", "nivel": "Iniciante", "resultado": "80%", "mensagem": "Vamos praticar."}
        historico = [registro]
        retorno = projeto.limpar_atividade(historico)
        self.assertEqual(retorno[0], "")
        self.assertIsNone(retorno[1])
        self.assertEqual(retorno[5], historico)
        self.assertEqual(retorno[4][0], list(registro.values()))
        self.assertEqual(historico, [registro])

    def test_sem_gravacao_nao_inicializa_reconhecedor(self):
        with patch.object(projeto, "obter_modelo_whisper") as modelo:
            with self.assertRaises(gr.Error):
                projeto.transcrever_audio(None)
            modelo.assert_not_called()

    def test_erro_de_audio_orienta_outra_tentativa_sem_detalhe_interno(self):
        with patch.object(projeto, "obter_modelo_whisper", side_effect=TypeError("detalhe-interno-de-biblioteca")):
            with self.assertLogs("ecoleitura", level="ERROR"):
                with self.assertRaises(gr.Error) as erro:
                    projeto.transcrever_audio("gravacao.wav")
        self.assertIn("Grave novamente", str(erro.exception))
        self.assertNotIn("detalhe-interno", str(erro.exception))

    def test_erro_de_ia_nao_exibe_excecao_tecnica(self):
        with patch.object(servicos.genai, "Client", side_effect=ValueError("detalhe-interno-do-servico")):
            with self.assertLogs("ecoleitura", level="ERROR"):
                with self.assertRaises(gr.Error) as erro:
                    servicos.gerar_texto(projeto.TEMAS[0], "Iniciante", [])
        self.assertIn("Tente novamente", str(erro.exception))
        self.assertNotIn("detalhe-interno", str(erro.exception))


if __name__ == "__main__":
    unittest.main()
