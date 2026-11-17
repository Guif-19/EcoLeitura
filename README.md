EcoLeitura — Alfabetização e Educação Ambiental com IA
O EcoLeitura é um protótipo educacional desenvolvido em Python e Gradio para apoiar atividades de leitura e conscientização ambiental. A aplicação combina geração de textos com inteligência artificial, reconhecimento automático de fala, atividades de associação entre palavras e imagens e desafios de tomada de decisão.
Funcionalidades
1. Leitura Ambiental
- A criança escolhe um mascote, um tema ambiental e um nível de leitura.
- O Gemini gera um texto informativo curto sobre o tema selecionado.
- A criança lê o texto em voz alta e grava sua leitura.
- O faster-whisper transcreve o áudio localmente; o aplicativo compara o texto reconhecido com o texto apresentado e exibe um relatório e feedback.
2. Aprendendo Palavras
- Apresenta palavras relacionadas à natureza e ao meio ambiente.
- A criança grava a leitura de uma palavra.
- O reconhecimento de fala verifica se a palavra foi identificada corretamente.
- Quando a palavra não é reconhecida como esperado, a criança pode ouvir sua pronúncia por meio do gTTS e tentar novamente.
- Quando a palavra é reconhecida, a criança identifica a imagem correspondente entre quatro opções.
3. Missão: Salve o Meio Ambiente
- A criança escolhe uma história pronta com um desafio ambiental.
- Escreve uma solução para o problema apresentado.
- O Gemini avalia a proposta e a classifica como Bom Caminho, Caminho Intermediário ou Caminho Ruim.
- A atividade apresenta uma explicação educativa e uma sugestão para melhorar a resposta.
- A criança pode revisar sua decisão e tentar novamente.
Tecnologias utilizadas
Tecnologia	Uso
Python	Linguagem principal
Gradio	Interface web local
Google Gemini (google-genai)	Geração de textos e avaliação de decisões
faster-whisper	Transcrição local da leitura em português
gTTS	Síntese de voz para as palavras
python-dotenv	Leitura da chave de API a partir do arquivo .env


Atenção: o projeto não é mais totalmente local. O reconhecimento de fala é executado no computador, mas o Gemini e o gTTS dependem de serviços pela internet. O uso da API Gemini pode estar sujeito a limites e cobranças conforme o plano e a configuração da conta. Consulte as condições atuais do serviço.

Estrutura do projeto
EcoLeitura/
├── projeto.py              # Interface principal e integração das abas
├── servicos.py             # Geração de textos com Gemini
├── fonetica.py             # Atividade Aprendendo Palavras
├── missoes.py              # Histórias prontas e avaliação de decisões
├── style.css               # Estilos da interface
├── requirements.txt        # Dependências Python
├── .gitignore
├── .env                    # Chave de API local (não publicar)
├── mascotes/               # Imagens dos mascotes
└── imagens_palavras/       # Imagens usadas na associação de palavras
A estrutura pode incluir outras pastas de imagens e arquivos auxiliares conforme a versão do projeto.
1. Pré-requisitos
- Python instalado (desenvolvido em ambiente com Python 3.12).
- Conexão com a internet para instalar dependências, usar o Gemini e gerar áudio com gTTS.
- Uma chave de API Gemini válida, obtida pelo Google AI Studio.
- Microfone para as atividades de leitura.
2. Baixar e abrir o projeto
Clone o repositório ou baixe seu conteúdo em ZIP. No terminal, entre na pasta em que está o arquivo projeto.py.
3. Criar um ambiente virtual e instalar dependências
No Windows (PowerShell):
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Caso as bibliotecas das novas funcionalidades ainda não estejam incluídas em requirements.txt, instale-as e atualize esse arquivo antes de publicar:
python -m pip install google-genai python-dotenv gTTS gradio faster-whisper
4. Configurar a API Gemini
Crie um arquivo chamado .env na pasta do projeto e adicione:
GEMINI_API_KEY=SUA_CHAVE_AQUI
O arquivo servicos.py utiliza o modelo gemini-3.5-flash-lite na configuração atual. Verifique se o modelo configurado em missoes.py é o mesmo ou outro modelo disponível para sua chave. A disponibilidade de modelos pode mudar.

Nunca publique a chave de API. Confira se o .gitignore contém:
.env
.venv/
__pycache__/
*.pyc
Se a chave já tiver sido incluída em commits antigos, apenas adicionar .env ao .gitignore não a remove do histórico. Revogue ou substitua a chave exposta e limpe o histórico antes de publicar.
5. Preparar as imagens
- Coloque as imagens dos mascotes na pasta esperada pelo projeto.py.
- Coloque as imagens das palavras em imagens_palavras/, usando os nomes previstos em fonetica.py (por exemplo, sol.png, arvore.png e poluicao.png).
- Para a atividade de associação, é necessário haver pelo menos quatro imagens disponíveis no conjunto de palavras utilizado pela atividade.
6. Executar o EcoLeitura
Com o ambiente virtual ativado:
python projeto.py
Abra no navegador o endereço informado pelo Gradio, normalmente:

http://127.0.0.1:7860
Observações importantes
- Na primeira execução, o faster-whisper pode baixar o modelo de reconhecimento de fala.
- A avaliação de leitura compara o texto esperado com a transcrição automática. Não é uma medição fonética precisa, nem uma avaliação clínica ou diagnóstico.
- O reconhecimento de fala pode falhar com vozes infantis, gravações curtas, sotaques e ruídos.
- As classificações das decisões ambientais são produzidas por IA e podem apresentar erros. Recomenda-se acompanhamento de um adulto ou educador.
- O gTTS precisa de conexão com a internet para gerar o áudio das palavras.
- O projeto é uma prova de conceito educacional; antes de utilizá-lo com crianças em produção, revise privacidade, consentimento e tratamento de dados e áudios.