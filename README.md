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
├── autenticacao.py         # Tela de cadastro e integração do login
├── usuarios.py             # Contas locais e proteção das senhas
├── dados/usuarios.sqlite3  # Banco local de contas (não publicar)
├── servicos.py             # Geração de textos com Gemini
├── fonetica.py             # Atividade Aprendendo Palavras
├── missoes.py              # Histórias prontas e avaliação de decisões
├── style.css               # Estilos da interface
├── login.css               # Estilos da tela de entrada
├── requirements.txt        # Dependências Python
├── .gitignore
├── .env                    # Chave de API local (não publicar)
├── .env.example            # Modelo de configuração sem credenciais reais
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
O projeto usa Gradio 6, integrado ao FastAPI para servir o cadastro e as atividades no mesmo endereço.
O requirements.txt limita o PyAV a uma versão compatível com o faster-whisper. Se aparecer o erro `open() got an unexpected keyword argument 'metadata_errors'`, pare a aplicação e execute `python -m pip install -r requirements.txt` no ambiente virtual antes de reiniciar. A incompatibilidade está registrada no [repositório do faster-whisper](https://github.com/SYSTRAN/faster-whisper/issues/1589).
4. Configurar a API Gemini e criar uma conta
Para as atividades com Gemini, copie .env.example para .env na pasta do projeto e preencha:

```dotenv
GEMINI_API_KEY=SUA_CHAVE_AQUI
```

Para testar o cadastro e o login, não é necessário configurar uma chave Gemini:

1. Inicie o aplicativo e abra http://127.0.0.1:7860.
2. Clique em **Criar conta** na tela de entrada.
3. Escolha um usuário e uma senha, confirme a senha e clique em **Criar minha conta**.
4. Na confirmação, clique em **Entrar na minha conta** e faça o login.
5. Use **Sair** para encerrar a sessão neste navegador.

O usuário deve ter de 3 a 30 caracteres: letras sem acento, números, ponto, traço ou sublinhado. Maiúsculas e minúsculas são equivalentes no usuário. A senha deve ter entre 8 e 128 caracteres e diferencia maiúsculas e minúsculas.

O banco SQLite é criado automaticamente em dados/usuarios.sqlite3. Cada conta é persistida localmente com um salt aleatório e um hash PBKDF2-SHA256; as senhas não são armazenadas em texto puro. Essa pasta é ignorada pelo Git e bloqueada no servidor de arquivos da aplicação. Reiniciar o aplicativo mantém as contas. Ao mover o projeto para outro computador, as contas não são transferidas pelo Git.

O login usa as sessões nativas do Gradio para restringir também os endpoints das atividades. O histórico de leitura continua temporário, por sessão; o cadastro não salva o progresso das atividades.

Este MVP tem cadastro, login e saída. Não inclui confirmação por e-mail, recuperação de senha, perfis de professor/aluno nem gestão de contas. O cadastro fica disponível a quem acessa a aplicação. Para publicação fora do ambiente de demonstração, será necessário revisar os controles de acesso.

As variáveis ECOLEITURA_USUARIO e ECOLEITURA_SENHA da versão anterior não são mais usadas: os acessos são criados pela tela de cadastro. O arquivo .env continua reservado à configuração dos serviços, como a chave Gemini. Preserve uma chave existente ao editar esse arquivo.

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

Para executar os testes do login, na pasta do projeto:

```powershell
python -m unittest discover -s tests -v
```

Referência da autenticação: [documentação oficial do Gradio](https://www.gradio.app/guides/sharing-your-app#authentication).

Observações importantes
- Na primeira execução, o faster-whisper pode baixar o modelo de reconhecimento de fala.
- A avaliação de leitura compara o texto esperado com a transcrição automática. Não é uma medição fonética precisa, nem uma avaliação clínica ou diagnóstico.
- O reconhecimento de fala pode falhar com vozes infantis, gravações curtas, sotaques e ruídos.
- As classificações das decisões ambientais são produzidas por IA e podem apresentar erros. Recomenda-se acompanhamento de um adulto ou educador.
- O gTTS precisa de conexão com a internet para gerar o áudio das palavras.
- O projeto é uma prova de conceito educacional; antes de utilizá-lo com crianças em produção, revise privacidade, consentimento e tratamento de dados e áudios.
