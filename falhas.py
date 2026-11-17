"""Mensagens compreensíveis para falhas das atividades do MVP."""

import logging


def mensagem_falha(acao, erro):
    logging.getLogger("ecoleitura").error("Falha ao %s: %s", acao, type(erro).__name__, exc_info=True)
    codigo = getattr(erro, "code", None)
    if codigo == 429:
        return "Há muitas solicitações agora. Aguarde um pouco e tente novamente."
    if acao == "abrir a gravação":
        return "Não conseguimos abrir esta gravação. Grave novamente ou envie outro arquivo de áudio."
    if acao == "ouvir a palavra":
        return "Não conseguimos tocar o exemplo agora. Confira a conexão e tente novamente."
    return "Não conseguimos concluir esta etapa agora. Tente novamente em instantes ou peça ajuda ao responsável."
