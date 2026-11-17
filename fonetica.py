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

PASTA_IMAGENS = Path(__file__).resolve().parent / "imagens_palavras"
PASTA_MASCOTES = Path(__file__).resolve().parent / "mascotes"

PALAVRAS = [
    "AQUECIMENTO",
    "ENERGIA",
    "DESPERDÍCIO",
    "PASSAROS",
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
    "AQUECIMENTO": "aquecimento", "PASSAROS": "passaros", "OCEANO": "oceano", 
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


def nova_palavra(nivel, usadas):
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
        gr.update(visible=False),
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
        "Muito Bem! Você leu corretamente!"
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
        gr.update(visible=not correto),
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
        gTTS(text=estado["palavra"].lower(), lang="pt", tld="com.br").save(destino)
        return gr.update(value=destino, visible=True)
    except Exception as erro:
        raise gr.Error(f"Não foi possível gerar o áudio: {erro}")


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
            '<h2>Você errou!</h2>'
            '<p>Observe as imagens e tente novamente.</p>'
            '</div>'
        ), 
        visible=True
    )


def criar_aba_fonetica(transcrever_audio, mascote_state):
    """Constrói a aba dentro de um contexto gr.Tab ou gr.Blocks já aberto."""
    gr.Markdown("## Aprendendo Palavras")
    gr.Markdown(
        "Leia palavras relacionadas ao meio ambiente. "
        "Se precisar, escute a pronúncia e tente novamente."
    )
    estado = gr.State(None)
    usadas = gr.State([])
    proxima = gr.Button("Nova palavra", variant="primary")
    palavra = gr.Markdown("### Clique em nova palavra para começar", elem_id="palavra-fonetica")
    audio = gr.Audio(sources=["microphone", "upload"], type="filepath",
                     label="Grave sua leitura", elem_classes="audio-jogo")
    avaliar = gr.Button("Verificar minha leitura")
    reacao_fonetica = gr.HTML()
    feedback = gr.Markdown()
    
    ouvir = gr.Button("Ouvir a palavra", visible=False)
    audio_modelo = gr.Audio(label="Pronúncia da palavra", visible=False,
                            interactive=False, autoplay=False)
    imagens = gr.Gallery(
    label="Escolha a imagem correspondente",
    columns=2,
    rows=2,
    height=500,
    object_fit="contain",
    allow_preview=False,
    visible=False,
    elem_id="galeria-palavras"
    )

    resultado_imagem = gr.HTML(visible=False)

    saidas_nova = [estado, usadas, palavra, audio, feedback,
                   audio_modelo, ouvir, imagens, resultado_imagem,
                   reacao_fonetica]
    
    proxima.click(nova_palavra, inputs=[usadas], outputs=saidas_nova)
    
    avaliar.click(
    lambda a, e, m: avaliar_pronuncia(a, e, transcrever_audio, m),
    inputs=[audio, estado, mascote_state],
    outputs=[estado, feedback, ouvir, imagens, reacao_fonetica]
    )   
    
    ouvir.click(ouvir_palavra, inputs=[estado], outputs=[audio_modelo])
    
    imagens.select(verificar_imagem, inputs=[estado], outputs=[resultado_imagem])
    return None
