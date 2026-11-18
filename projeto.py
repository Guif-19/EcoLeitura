"""
EcoLeitura — PoC de alfabetização e educação ambiental
Arquivo único: projeto.py

Funcionalidades:
1) Geração de texto ambiental com Gemini.
2) Gravação/envio de áudio e transcrição em português (faster-whisper).
3) Comparação entre texto esperado e transcrição, com feedback estimado.
4) Relatório da atividade na própria página.

IMPORTANTE:
- A comparação textual NÃO mede fonemas com precisão. O resultado é uma estimativa
  de correspondência entre o que foi proposto e o que o reconhecedor transcreveu.
- Para uso com crianças, faça testes supervisionados, evite guardar áudios e não
  trate a pontuação como nota ou diagnóstico.
"""

import os
import re
import unicodedata
import html 
import difflib
from datetime import datetime

import gradio as gr
import uvicorn
from faster_whisper import WhisperModel
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).with_name(".env"))
from servicos import gerar_texto
from fonetica import criar_aba_fonetica
from missoes import criar_aba_missoes
from autenticacao import criar_app
from falhas import mensagem_falha


# ----------------------------- CONFIGURAÇÕES -----------------------------

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "small")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

TEMAS = [
    "Reciclagem e separação do lixo",
    "Mudanças climáticas",
    "Desmatamento e queimadas",
    "Extinção de espécies",
    "Água e uso consciente",
    "Ciclo da vida e as plantas",
    "Animais e seus lares",
    "Economia de energia",
    "Consumo consciente e reaproveitamento",
    "Poluição e cuidado com a natureza",
]




PASTA_MASCOTES = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "mascotes"
)

NIVEIS = ["Iniciante", "Intermediário", "Avançado"]

MASCOTES = {
    "Boitatá": "a Serpente de Fogo",
    "Boto Cor de Rosa": "o Boto-cor-de-rosa",
    "Caipora": "o Guardião dos Animais",
    "Curupira": "o Protetor das Florestas",
    "Iara": "a Guardiã das Águas",
    "Mãe do Ouro": "a Protetora das Riquezas Naturais",
    "Mapinguari": "o Guardião da Floresta",
    "Saci": "o Travesso da Floresta"
}

HISTORIAS_MASCOTES = {
    "Boitatá": "Uma serpente de fogo que protege os campos e as florestas contra quem provoca queimadas.",

    "Boto Cor de Rosa": "Nas lendas amazônicas, o boto pode se transformar em um homem e participar das festas às margens dos rios.",

    "Caipora": "Um ser encantado que vive nas matas e protege os animais contra caçadores que desrespeitam a natureza.",

    "Curupira": "Guardião das florestas, tem os pés virados para trás e confunde quem tenta prejudicar as árvores e os animais.",

    "Iara": "Uma sereia encantada dos rios brasileiros, conhecida por sua beleza e seu canto misterioso.",

    "Mãe do Ouro": "Uma luz dourada e misteriosa que aparece nas matas e montanhas, associada à proteção dos tesouros da terra.",

    "Mapinguari": "Uma criatura gigante e misteriosa que vive nas florestas amazônicas e aparece em histórias sobre os perigos da mata.",

    "Saci": "Um menino travesso de uma perna só, com gorro vermelho, que cria redemoinhos e faz brincadeiras pelas matas."
}


IMAGENS_MASCOTES = [
    (
        os.path.join(
            PASTA_MASCOTES,
            ( f"{nome.lower()}.png"
            )
        ),
        nome
    )
    for nome in MASCOTES
]

# Modelos carregados sob demanda para a primeira abertura da aplicação ser mais rápida.
_whisper_model = None


# ----------------------------- FUNÇÕES AUXILIARES -----------------------------

def normalizar(texto: str) -> str:
    """Padroniza texto para comparação simples, sem diferenciar acentos ou caixa."""
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^\w\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()

def obter_modelo_whisper():
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = WhisperModel(
            WHISPER_MODEL_SIZE,
            device=WHISPER_DEVICE,
            compute_type=WHISPER_COMPUTE_TYPE,
        )
    return _whisper_model


def transcrever_audio(caminho_audio):
    if not caminho_audio:
        raise gr.Error("Grave sua leitura ou envie um arquivo de áudio. Caso tenha gravado, verifique se apertou o botão PARAR")


    try:
        modelo = obter_modelo_whisper()
        segmentos, info = modelo.transcribe(
            caminho_audio, language="pt", beam_size=5, vad_filter=True,
        )
        transcricao = " ".join(segmento.text.strip() for segmento in segmentos).strip()
    except Exception as erro:
        raise gr.Error(mensagem_falha("abrir a gravação", erro)) from erro

    if not transcricao:
        raise gr.Error(
            "Não foi possível reconhecer a fala. Tente gravar novamente em um "
            "ambiente silencioso e fale em um ritmo natural."
        )

    return transcricao


def avaliar_leitura(texto_original, transcricao):
    """
    Faz comparação aproximada por palavras.
    Não é uma avaliação fonética/fonêmica nem um diagnóstico de fala.
    """
    palavras_originais = normalizar(texto_original).split()
    palavras_lidas = normalizar(transcricao).split()

    if not palavras_originais:
        raise gr.Error("Gere um texto antes de avaliar a leitura.")

    # Alinhamento simples para identificar palavras iguais, omitidas e substituídas.
    import difflib

    comparador = difflib.SequenceMatcher(
        a=palavras_originais,
        b=palavras_lidas,
        autojunk=False,
    )

    corretas = []
    diferentes = []
    faltantes = []
    adicionadas = []

    for operacao, i1, i2, j1, j2 in comparador.get_opcodes():
        if operacao == "equal":
            corretas.extend(palavras_originais[i1:i2])
        elif operacao == "replace":
            pares = min(i2 - i1, j2 - j1)
            for indice in range(pares):
                diferentes.append(
                    (palavras_originais[i1 + indice], palavras_lidas[j1 + indice])
                )
            faltantes.extend(palavras_originais[i1 + pares:i2])
            adicionadas.extend(palavras_lidas[j1 + pares:j2])
        elif operacao == "delete":
            faltantes.extend(palavras_originais[i1:i2])
        elif operacao == "insert":
            adicionadas.extend(palavras_lidas[j1:j2])

    total = len(palavras_originais)
    percentual = round((len(corretas) / total) * 100) if total else 0

    if percentual >= 90:
        mensagem = "Ótimo trabalho! A transcrição ficou bem próxima do texto."
    elif percentual >= 70:
        mensagem = "Muito bem! Você está aprendendo. Vamos praticar mais algumas palavras."
    else:
        mensagem = "Continue tentando! Leia devagar e grave novamente com calma."

    linhas = []
    if diferentes:
        linhas.extend([f"{esperada} → reconhecido como {reconhecida}"
                       for esperada, reconhecida in diferentes])
    if faltantes:
        linhas.append("Possivelmente não identificadas: " + ", ".join(faltantes))
    if adicionadas:
        linhas.append("Palavras extras reconhecidas: " + ", ".join(adicionadas))

    detalhes = (
        "\n".join(f"- {linha}" for linha in linhas)
        if linhas
        else "Nenhuma diferença de palavras foi identificada."
    )

    palavras_revisao = (
    [palavra for palavra, _ in diferentes] + faltantes
    )

    return percentual, mensagem, detalhes, palavras_revisao

def colorir_transcricao(texto_original, transcricao):
    palavras_originais = normalizar(texto_original).split()
    palavras_lidas = transcricao.split()
    palavras_comparacao = normalizar(transcricao).split()

    comparador = difflib.SequenceMatcher(
        a=palavras_originais,
        b=palavras_comparacao,
        autojunk=False
    )

    cores = ["errada"] * len(palavras_lidas)

    for operacao, i1, i2, j1, j2 in comparador.get_opcodes():
        if operacao == "equal":
            for i in range(j1, j2):
                cores[i] = "correta"

    resultado = []

    for palavra, cor in zip(palavras_lidas, cores):
        palavra_segura = html.escape(palavra)

        resultado.append(
            f'<span class="palavra-{cor}">{palavra_segura}</span>'
        )

    return " ".join(resultado)


# ----------------------------- EVENTOS DA INTERFACE -----------------------------

def gerar_e_atualizar(tema, nivel, historico, progress=gr.Progress()):
    progress(None, desc="Preparando sua leitura…")
    texto = gerar_texto(tema, nivel, historico)
    return texto, "Texto gerado! Agora leia em voz alta e grave sua leitura."


def processar_leitura(audio, texto_original, tema, nivel, historico, nome_mascote, progress=gr.Progress()):
    if not texto_original or not texto_original.strip():
        raise gr.Error("Primeiro, gere um texto ambiental.")

    progress(None, desc="Ouvindo a gravação e conferindo as palavras…")
    transcricao = transcrever_audio(audio)
    transcricao_colorida = colorir_transcricao(
        texto_original,
        transcricao
    )

    transcricao_formatada = f"""
    <div class="resultado-transcricao">
        <strong>O que foi reconhecido na sua leitura</strong>
        <p>{transcricao_colorida}</p>
    </div>
    """
    percentual, mensagem, detalhes, palavras_revisao = avaliar_leitura(
    texto_original, transcricao
    )

    registro = {
        "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "tema": tema,
        "nivel": nivel,
        "resultado": f"{percentual}%",
        "mensagem": mensagem,
        "transcricao": transcricao,
        "palavras_revisao": palavras_revisao,
    }

    historico = (historico or []) + [registro]

    relatorio = (
        "## Relatório de leitura\n\n"
        f"**Tema:** {tema}\n\n"
        f"**Nível:** {nivel}\n\n"
        f"**Correspondência estimada:** {percentual}%\n\n"
        f"**Feedback:** {mensagem}\n\n"
        "### Palavras para revisar\n\n"
        f"{detalhes}\n\n"
        "---\n\n"
        "*Esta porcentagem representa a correspondência aproximada "
        "entre as palavras do texto e a transcrição automática. "
        "Ela não comprova a pronúncia correta de cada som.*"
    )
    tabela = [
        [
            item["data"],
            item["tema"],
            item["nivel"],
            item["resultado"],
            item["mensagem"],
        ]
        for item in historico
    ]
    imagem_mascote, mensagem_mascote = reacao_mascote(
        nome_mascote,
        percentual
    )

    return ( transcricao_formatada, relatorio, tabela, historico,
        gr.update(
            value=imagem_mascote,
            visible=imagem_mascote is not None
        ),
        mensagem_mascote
    )


def limpar_atividade(historico=None):
    """Começa outra leitura, preservando as conquistas desta sessão."""
    historico = list(historico or [])
    tabela = [[item["data"], item["tema"], item["nivel"], item["resultado"], item["mensagem"]] for item in historico]
    return "", None, "", "", tabela, historico, gr.update(value=None, visible=False), ""


def estado_gravacao(texto, audio):
    pronto = bool((texto or "").strip() and audio)
    mensagem = "Gravação pronta. Você pode ouvir, refazer ou conferir sua leitura." if pronto else "Toque em Gravar, leia o texto e pare a gravação. Depois, confira sua leitura."
    return gr.update(interactive=pronto), mensagem


def etapas_leitura(etapa):
    nomes = ["Preparar", "Gravar", "Resultado"]
    return '<ol class="etapas-leitura" aria-label="Etapas da leitura">' + "".join(
        f'<li class="{"ativa" if i == etapa else ""}" {"aria-current=step" if i == etapa else ""}><span>{i + 1}</span>{nome}</li>'
        for i, nome in enumerate(nomes)
    ) + "</ol>"


def mostrar_usuario(request: gr.Request):
    usuario = html.escape(request.username or "visitante")
    return f'<p class="conta-conectada">Conectado como <strong>{usuario}</strong></p>'

def escolher_mascote(selecao):
    if not isinstance(selecao, int) or not 0 <= selecao < len(MASCOTES):
        raise gr.Error("Escolha um amigo da natureza para continuar.")

    nome = list(MASCOTES.keys())[selecao]
    animal = MASCOTES[nome]

    mensagem = (
        f"### Olá! Eu sou {nome}!\n\n"
        f"Sou {animal.lower()} e vou acompanhar você "
        "nas suas aventuras de leitura!"
    )

    caminho_imagem = os.path.join(
        PASTA_MASCOTES,
        f"{nome.lower()}.png"
    )

    return (
        nome,
        mensagem,
        gr.update(visible=False),
        gr.update(visible=True),
        gr.update(value=caminho_imagem, visible=True),
        gr.update(visible=True)
    )

def reescolher_mascote():
    return (
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(value=None, visible=False),
        gr.update(visible=False),
        None,
        "",
        None
    )

def reacao_mascote(nome_mascote, percentual):
    if not nome_mascote:
        return None, "Escolha um amigo da natureza para acompanhar sua aventura!"

    if percentual >= 80:
        mensagem = (
            f"### {nome_mascote} está muito feliz!\n\n"
            "Parabéns! Você arrasou na leitura! "
            "Estou muito feliz com seu desempenho!"
        )

    elif percentual <= 50:
        mensagem = (
            f"### {nome_mascote} vai praticar com você!\n\n"
            "Vamos ouvir a gravação e tentar com calma. "
            "O reconhecimento também pode errar."
        )

    else:
        mensagem = (
            f"### {nome_mascote} está torcendo por você!\n\n"
            "Você está indo bem! Continue praticando "
            "para melhorar ainda mais!"
        )

    caminho_imagem = imagem_reacao_mascote(nome_mascote, percentual)

    return caminho_imagem, mensagem

def imagem_reacao_mascote(nome_mascote, percentual):
    # Usa o mesmo nome de arquivo definido para cada mascote
    arquivos = {
        "Boitatá": "boitatá.png",
        "Boto Cor de Rosa": "boto cor de rosa.png",
        "Caipora": "caipora.png",
        "Curupira": "curupira.png",
        "Iara": "iara.png",
        "Mãe do Ouro": "mãe do ouro.png",
        "Mapinguari": "mapinguari.png",
        "Saci": "saci.png"
    }

    arquivo = arquivos.get(nome_mascote)

    if not arquivo:
        return None

    if percentual >= 80:
        pasta = os.path.join(PASTA_MASCOTES, "mascote_feliz")
    elif percentual <= 50:
        pasta = os.path.join(PASTA_MASCOTES, "mascote_triste")
    else:
        pasta = PASTA_MASCOTES

    return os.path.join(pasta, arquivo)

def registrar_selecao(evt: gr.SelectData):
    return evt.index


# ----------------------------- INTERFACE: UMA ÚNICA PÁGINA -----------------------------

CAMINHO_CSS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "style.css"
)

with open(CAMINHO_CSS, "r", encoding="utf-8") as arquivo:
    CSS = arquivo.read()
    


with gr.Blocks(title="EcoLeitura — Alfabetização e Meio Ambiente") as demo:
    historico_state = gr.State([])
    mascote_state = gr.State(None)
    indice_mascote_state = gr.State(None)

    with gr.Row(elem_id="cabecalho-ecoleitura"):
        with gr.Column(scale=1):
            gr.Markdown("# 🌱 EcoLeitura")
            conta = gr.HTML()
        gr.Button("Sair", link="/logout?all_session=false", size="sm", min_width=80, scale=0)
    demo.load(mostrar_usuario, outputs=[conta])

    with gr.Accordion("Como usar o EcoLeitura", open=False, elem_classes="ajuda-contextual"):
        gr.Markdown(
            "**Leitura:** escolha seu amigo, prepare um texto, grave a leitura e confira o retorno.\n\n"
            "**Palavras:** escolha uma palavra, ouça um exemplo se precisar e grave sua tentativa.\n\n"
            "**Missões:** leia uma história e escreva sua ideia para ajudar a natureza.\n\n"
            "Se o microfone não estiver disponível, você pode enviar um arquivo de áudio. "
            "Peça ajuda a um adulto para permitir o uso do microfone."
        )

    with gr.Tabs(elem_id="atividades-ecoleitura"):
        with gr.Tab("Leitura"):
            gr.Markdown("## Leitura ambiental\nEscolha um amigo para acompanhar sua leitura e pratique com a gente.")

            with gr.Group(elem_id="amigos-ecoleitura"):
                with gr.Column() as area_selecao_mascote:
                    gr.Markdown(
                        "### 🌿 Escolha seu amigo da natureza\n"
                        "Ele vai acompanhar você nesta aventura! Toque em um personagem e depois em **Escolher amigo**."
                    )
                    mascote = gr.Gallery(
                        value=IMAGENS_MASCOTES, label="Amigos da natureza", columns=4,
                        height="auto", object_fit="contain", allow_preview=False,
                        interactive=False, buttons=[], elem_id="galeria-mascotes",
                    )
                    selecao_mascote = gr.Markdown("Nenhum amigo selecionado ainda.")
                    confirmar_mascote = gr.Button("Escolher amigo", variant="primary", interactive=False)
                with gr.Column(visible=False) as area_mascote_escolhido:
                    with gr.Row(elem_id="amigo-escolhido"):
                        imagem_mascote_escolhido = gr.Image(show_label=False, height=160, width=160, min_width=140, scale=0, interactive=False, container=False, buttons=[])
                        with gr.Column():
                            mensagem_mascote = gr.Markdown()
                            reescolher_btn = gr.Button("Trocar amigo", visible=False)

            etapas = gr.HTML(etapas_leitura(0))
            with gr.Row():
                tema = gr.Dropdown(choices=TEMAS, value=TEMAS[0], label="Assunto")
                nivel = gr.Radio(choices=NIVEIS, value="Iniciante", label="Nível de leitura")
            gerar_btn = gr.Button("Preparar leitura", variant="primary")
            status_geracao = gr.Markdown("Escolha o assunto e toque em **Preparar leitura**.")

            with gr.Column(visible=False) as area_gravacao:
                gr.Markdown("### 2. Grave sua leitura")
                texto_original = gr.Textbox(
                    label="Seu texto", lines=4, interactive=False,
                    elem_id="texto-leitura",
                )
                gr.Markdown("Toque em **Gravar**, leia o texto e toque em **Parar**. Você pode ouvir e refazer antes de conferir.")
                audio = gr.Audio(sources=["microphone", "upload"], type="filepath", label="Sua gravação", elem_classes="audio-jogo")
                status_gravacao = gr.Markdown()
                gr.Markdown("A primeira análise pode levar mais tempo para preparar o reconhecedor.", elem_classes="nota-atividade")
                avaliar_btn = gr.Button("Conferir minha leitura", variant="primary", interactive=False)

            with gr.Column(visible=False) as area_conquistas:
                gr.Markdown("### 3. Veja seu resultado")
                with gr.Row(elem_classes="area-mascote"):
                    imagem_resultado_mascote = gr.Image(show_label=False, height=150, interactive=False, visible=False, container=False, buttons=[], elem_classes="imagem-mascote")
                    mensagem_resultado_mascote = gr.Markdown(elem_classes="balao-mascote")
                transcricao = gr.HTML()
                with gr.Accordion("Detalhes da leitura para o responsável", open=False):
                    relatorio = gr.Markdown()
                limpar_btn = gr.Button("Nova leitura")

            with gr.Accordion("Histórico desta sessão", open=False):
                gr.Markdown("Estas atividades ficam disponíveis nesta sessão. O progresso ainda não é salvo na conta.", elem_classes="nota-atividade")
                tabela_historico = gr.Dataframe(
                    headers=["Data", "Assunto", "Nível", "Resultado", "Retorno"],
                    datatype=["str", "str", "str", "str", "str"],
                    column_widths=[150, 240, 150, 110, 360],
                    interactive=False, wrap=True, label="Leituras desta sessão",
                )
            gr.Markdown("O reconhecimento automático pode errar. Use o retorno para praticar com um adulto; ele não confirma cada som da pronúncia.", elem_classes="nota-atividade")

            def selecionar_amigo(evt: gr.SelectData):
                indice = evt.index
                nome = list(MASCOTES)[indice]
                return indice, f"**{nome}:** {HISTORIAS_MASCOTES[nome]}", gr.update(interactive=True)

            mascote.select(selecionar_amigo, outputs=[indice_mascote_state, selecao_mascote, confirmar_mascote])
            confirmar_mascote.click(
                escolher_mascote, inputs=[indice_mascote_state],
                outputs=[mascote_state, mensagem_mascote, area_selecao_mascote, area_mascote_escolhido, imagem_mascote_escolhido, reescolher_btn],
            )
            reescolher_btn.click(
                reescolher_mascote,
                outputs=[area_selecao_mascote, area_mascote_escolhido, imagem_mascote_escolhido, reescolher_btn, mascote_state, mensagem_mascote, indice_mascote_state],
            ).then(lambda: ("Escolha outro amigo.", gr.update(interactive=False)), outputs=[selecao_mascote, confirmar_mascote], queue=False)

            inicio_geracao = gerar_btn.click(
                lambda: (gr.update(interactive=False), "Preparando sua leitura…", gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False)),
                outputs=[gerar_btn, status_geracao, avaliar_btn, audio, tema, nivel], queue=False,
            )
            geracao = inicio_geracao.then(
                gerar_e_atualizar, inputs=[tema, nivel, historico_state],
                outputs=[texto_original, status_geracao], concurrency_id="leitura", concurrency_limit=1,
            )
            geracao.success(
                lambda: (gr.update(visible=True), gr.update(value=None, interactive=True), gr.update(interactive=False), gr.update(visible=False), etapas_leitura(1), "Grave sua leitura para continuar."),
                outputs=[area_gravacao, audio, avaliar_btn, area_conquistas, etapas, status_gravacao],
            )
            geracao.failure(lambda: "Não foi possível preparar o texto. Tente novamente ou peça ajuda ao responsável.", outputs=[status_geracao], queue=False)
            geracao.failure(lambda t, a: (gr.update(interactive=bool(t and a)), gr.update(interactive=not bool(t)), gr.update(interactive=not bool(t))), inputs=[texto_original, audio], outputs=[avaliar_btn, tema, nivel], queue=False)
            geracao.then(lambda: (gr.update(interactive=True), gr.update(interactive=True)), outputs=[gerar_btn, audio], queue=False)

            audio.change(estado_gravacao, inputs=[texto_original, audio], outputs=[avaliar_btn, status_gravacao], queue=False)
            audio.start_recording(lambda: "Gravando… leia com calma e toque em Parar quando terminar.", outputs=[status_gravacao], queue=False)

            inicio_avaliacao = avaliar_btn.click(
                lambda: (gr.update(interactive=False), gr.update(interactive=False), "Ouvindo sua gravação…", gr.update(interactive=False)),
                outputs=[avaliar_btn, audio, status_gravacao, gerar_btn], queue=False,
            )
            avaliacao = inicio_avaliacao.then(
                processar_leitura,
                inputs=[audio, texto_original, tema, nivel, historico_state, mascote_state],
                outputs=[transcricao, relatorio, tabela_historico, historico_state, imagem_resultado_mascote, mensagem_resultado_mascote],
                concurrency_id="leitura", concurrency_limit=1,
            )
            avaliacao.success(
                lambda: (gr.update(visible=True), etapas_leitura(2), "Leitura conferida. Veja seu resultado abaixo."),
                outputs=[area_conquistas, etapas, status_gravacao],
            )
            avaliacao.failure(lambda: "Não conseguimos conferir esta gravação. Você pode ouvir, refazer ou enviar outro arquivo.", outputs=[status_gravacao], queue=False)
            avaliacao.then(
                lambda t, a: (gr.update(interactive=bool(t and a)), gr.update(interactive=True), gr.update(interactive=True)),
                inputs=[texto_original, audio], outputs=[avaliar_btn, audio, gerar_btn], queue=False,
            )
            limpar_btn.click(
                limpar_atividade, inputs=[historico_state],
                outputs=[texto_original, audio, transcricao, relatorio, tabela_historico, historico_state, imagem_resultado_mascote, mensagem_resultado_mascote],
            ).then(
                lambda: (gr.update(visible=False), gr.update(visible=False), gr.update(interactive=False), etapas_leitura(0), "Seu histórico foi mantido. Prepare outra leitura.", gr.update(interactive=True), gr.update(interactive=True)),
                outputs=[area_gravacao, area_conquistas, avaliar_btn, etapas, status_geracao, tema, nivel], queue=False,
            )

        with gr.Tab("Palavras"):
            criar_aba_fonetica(transcrever_audio, mascote_state)
        with gr.Tab("Missões"):
            criar_aba_missoes(mascote_state)


if __name__ == "__main__":
    app = criar_app(
        demo, theme=gr.themes.Soft(primary_hue="green", secondary_hue="green"), css=CSS,
        footer_links=[],
        allowed_paths=[str(Path(__file__).parent / "imagens"), str(Path(__file__).parent / "imagens_palavras"), PASTA_MASCOTES],
    )
    uvicorn.run(app, host=os.getenv("GRADIO_SERVER_NAME", "127.0.0.1"), port=int(os.getenv("GRADIO_SERVER_PORT", "7860")))
