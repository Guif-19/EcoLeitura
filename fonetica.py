"""Aba de palavras ambientais para o EcoLeitura (Gradio 6).

Dependências: gradio, gTTS; recebe a função de transcrição do projeto.py.
Imagens PNG/JPG devem estar em imagens_palavras/ com os nomes definidos abaixo.
"""
from pathlib import Path
import random
import tempfile
import unicodedata
import re

import gradio as gr
from gtts import gTTS
from falhas import mensagem_falha

PASTA_IMAGENS = Path(__file__).resolve().parent / "imagens_palavras"
PASTA_MASCOTES = Path(__file__).resolve().parent / "mascotes"

PALAVRAS = [
    "AQUECIMENTO",
    "ENERGIA",
    "DESPERDÍCIO",
    "PÁSSAROS",
    "OCEANO",
    "DESMATAMENTO",
    "QUEIMADAS",
    "REFLORESTAMENTO",
    "COMPOSTAGEM",
    "ÁRVORE",
    "FOLHA",
    "PLANTA",
    "CHUVA",
    "TERRA",
    "PEIXE",
    "FLORESTA",
    "NATUREZA",
    "RECICLAGEM",
    "SEMENTE",
    "POLUIÇÃO",
    "AMBIENTE"
]

# Nome da imagem (sem extensão) de cada palavra.
ARQUIVOS = {
    "AQUECIMENTO": "aquecimento", "PÁSSAROS": "passaros", "OCEANO": "oceano",
    "ENERGIA": "energia",
    "DESPERDÍCIO": "desperdicio", "ÁRVORE": "arvore",
    "FOLHA": "folha", "PLANTA": "planta", "CHUVA": "chuva",
    "TERRA": "terra", "PEIXE": "peixe", "FLORESTA": "floresta",
    "NATUREZA": "natureza", "RECICLAGEM": "reciclagem",
    "SEMENTE": "semente", "POLUIÇÃO": "poluicao", "AMBIENTE": "ambiente",
    "DESMATAMENTO": "desmatamento","QUEIMADAS": "queimadas",
    "REFLORESTAMENTO": "reflorestamento","COMPOSTAGEM": "compostagem"
}


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", (texto or "").lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^a-z\s]", " ", texto).strip()


def caminho_imagem(palavra):
    nome = ARQUIVOS[palavra]
    for extensao in (".png", ".jpg", ".jpeg", ".webp"):
        caminho = PASTA_IMAGENS / (nome + extensao)
        if caminho.is_file():
            return str(caminho)
    return None


def nova_palavra(usadas):
    disponiveis = [p for p in PALAVRAS if caminho_imagem(p)]

    if len(disponiveis) < 4:
        raise gr.Error(
            f"Adicione pelo menos 4 imagens na pasta imagens_palavras."
        )

    usadas = [p for p in (usadas or []) if p in disponiveis]

    restantes = [p for p in disponiveis if p not in usadas]

    if not restantes:
        usadas = []
        restantes = disponiveis
    palavra = random.choice(restantes)
    usadas = usadas + [palavra]

    alternativas = [palavra] + random.sample(
        [p for p in disponiveis if p != palavra], 3
    )
    random.shuffle(alternativas)
    imagens = [(caminho_imagem(p), "Imagem " + str(i + 1))
               for i, p in enumerate(alternativas)]
    estado = {"palavra": palavra, "alternativas": alternativas,
              "pronuncia_ok": False, "imagem_ok": False}
    return (
        estado, usadas, palavra, None, "Grave sua leitura da palavra.",
        gr.update(visible=False, value=None),
        gr.update(visible=True, interactive=True),
        gr.update(value=imagens, visible=False),
        gr.update(value="", visible=False),
        ""
    )


def feedback_mascote_fonetica(nome_mascote, acertou):
    if not nome_mascote:
        return ""

    arquivo = f"{nome_mascote.lower()}.png"

    pasta = "mascote_feliz" if acertou else "mascote_triste"
    caminho = PASTA_MASCOTES / pasta / arquivo

    if not caminho.is_file():
        return ""

    from urllib.parse import quote
    from html import escape

    url = "/gradio_api/file=" + quote(str(caminho.resolve()), safe="/:")

    classe = "mascote-pulando" if acertou else "mascote-triste"

    mensagem = (
        "Identificamos a palavra na sua gravação!"
        if acertou else
        "Vamos tentar novamente!"
    )

    return f"""
    <div class="feedback-fonetica-mascote">
        <img src="{url}"
             class="{classe}"
             alt="{escape(nome_mascote, quote=True)}">
        <p>{mensagem}</p>
    </div>
    """

def avaliar_pronuncia(audio, estado, transcrever_audio, nome_mascote):
    if not estado:
        raise gr.Error("Clique em 'Nova palavra' primeiro.")

    if not audio:
        raise gr.Error("Grave a palavra antes de avaliar.")

    reconhecido = transcrever_audio(audio)
    esperado = normalizar(estado["palavra"])
    obtido = normalizar(reconhecido)

    # Correspondência textual, não análise fonética de sons isolados.
    correto = obtido == esperado

    novo_estado = dict(estado)
    novo_estado["pronuncia_ok"] = correto


    mensagem = (
        f"Palavra reconhecida: **{reconhecido}**. Muito bem! Agora escolha a imagem relacionada a essa palavra."
        if correto else
        f"O reconhecimento identificou **{reconhecido}**. "
        "Vamos ouvir a palavra e tentar novamente. "
        "O reconhecimento automático também pode errar."
    )

    reacao = feedback_mascote_fonetica(nome_mascote, correto)

    return (
        novo_estado, mensagem,
        gr.update(visible=True, interactive=True),
        gr.update(value=[
                (caminho_imagem(p), f"Imagem {i + 1}")
                for i, p in enumerate(novo_estado["alternativas"])
            ] if correto else None,
            visible=correto),
        reacao,
    )


def ouvir_palavra(estado):
    if not estado:
        raise gr.Error("Escolha uma palavra primeiro.")
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as arquivo:
            destino = arquivo.name
        gTTS(text=estado["palavra"].lower(), lang="pt", tld="com.br", timeout=15).save(destino)
        return gr.update(value=destino, visible=True)
    except Exception as erro:
        raise gr.Error(mensagem_falha("ouvir a palavra", erro)) from erro


def verificar_imagem(estado, evt: gr.SelectData):
    if not estado or not estado.get("pronuncia_ok"):
        return gr.update(
            value="Primeiro, conclua a leitura da palavra.",
            visible=True
        )

    indice = evt.index


    if not isinstance(indice, int) or not 0 <= indice < len(estado["alternativas"]):
        return gr.update(
            value="Selecione uma das imagens.",
            visible=True
        )


    if estado["alternativas"][indice] == estado["palavra"]:
        return gr.update(
            value=(
                '<div class="resultado-correto">'
                '<h2>Muito Bem!</h2>'
                '<p>Você escolheu a imagem correta! '
                'Clique em Nova palavra para continuar.</p>'
                '</div>'
            ),
            visible=True
        )
    return gr.update(
        value=(
            '<div class="resultado-errado">'
            '<h2>Vamos tentar outra imagem?</h2>'
            '<p>Observe as opções e escolha novamente.</p>'
            '</div>'
        ),
        visible=True
    )


def criar_aba_fonetica(transcrever_audio, mascote_state):
    gr.Markdown("## Aprendendo palavras\nEscolha uma palavra, grave sua tentativa e encontre a imagem.")
    estado = gr.State(None)
    usadas = gr.State([])
    proxima = gr.Button("Nova palavra", variant="primary")
    with gr.Column(visible=False) as area_palavra:
        palavra = gr.Markdown(elem_id="palavra-fonetica")
        ouvir = gr.Button("Ouvir um exemplo", interactive=False)
        audio_modelo = gr.Audio(label="Exemplo da palavra", visible=False, interactive=False, autoplay=False)
        gr.Markdown("Você pode ouvir o exemplo para praticar. Depois, toque em **Gravar**, diga a palavra e toque em **Parar**.")
        audio = gr.Audio(sources=["microphone", "upload"], type="filepath", label="Sua tentativa", elem_classes="audio-jogo")
        status = gr.Markdown("Grave a palavra para continuar.")
        avaliar = gr.Button("Conferir minha leitura", variant="primary", interactive=False)
        reacao_fonetica = gr.HTML()
        feedback = gr.Markdown()
        imagens = gr.Gallery(
            label="Encontre a imagem da palavra", columns=2, height="auto", object_fit="contain",
            allow_preview=False, visible=False, buttons=[], elem_id="galeria-palavras",
        )
        resultado_imagem = gr.HTML(visible=False)
    gr.Markdown("O reconhecimento pode errar. Você pode ouvir, refazer a gravação e tentar novamente.", elem_classes="nota-atividade")

    def atualizar_gravacao(caminho, dados):
        pronto = bool(caminho and dados)
        return gr.update(interactive=pronto), "Gravação pronta. Confira sua leitura ou grave outra tentativa." if pronto else "Grave a palavra e pare a gravação para continuar."

    def conferir(caminho, dados, mascote, progress=gr.Progress()):
        progress(None, desc="Ouvindo sua palavra…")
        return avaliar_pronuncia(caminho, dados, transcrever_audio, mascote)

    saidas_nova = [estado, usadas, palavra, audio, feedback, audio_modelo, ouvir, imagens, resultado_imagem, reacao_fonetica]
    proxima.click(nova_palavra, inputs=[usadas], outputs=saidas_nova).success(
        lambda: (gr.update(visible=True), gr.update(interactive=False), "Ouça um exemplo se precisar e grave sua tentativa."),
        outputs=[area_palavra, avaliar, status], queue=False,
    )
    audio.change(atualizar_gravacao, inputs=[audio, estado], outputs=[avaliar, status], queue=False)
    audio.start_recording(lambda: "Gravando… diga a palavra e toque em Parar.", outputs=[status], queue=False)
    inicio = avaliar.click(
        lambda: (gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False), "Ouvindo sua palavra…"),
        outputs=[avaliar, audio, proxima, status], queue=False,
    )
    avaliacao = inicio.then(
        conferir, inputs=[audio, estado, mascote_state],
        outputs=[estado, feedback, ouvir, imagens, reacao_fonetica],
        concurrency_id="palavras", concurrency_limit=1,
    )
    avaliacao.success(lambda: "Tentativa conferida. Veja a orientação abaixo.", outputs=[status], queue=False)
    avaliacao.failure(lambda: "Não conseguimos conferir o áudio. Grave novamente ou envie outro arquivo.", outputs=[status], queue=False)
    avaliacao.then(
        lambda a, e: (gr.update(interactive=bool(a and e)), gr.update(interactive=True), gr.update(interactive=True)),
        inputs=[audio, estado], outputs=[avaliar, audio, proxima], queue=False,
    )
    inicio_audio = ouvir.click(lambda: gr.update(interactive=False), outputs=[ouvir], queue=False)
    reproducao = inicio_audio.then(ouvir_palavra, inputs=[estado], outputs=[audio_modelo])
    reproducao.then(lambda: gr.update(interactive=True), outputs=[ouvir], queue=False)
    imagens.select(verificar_imagem, inputs=[estado], outputs=[resultado_imagem])
