# Melhorias de interface do MVP

Implementação da revisão de 17/11/2026. Os identificadores abaixo correspondem aos achados da avaliação por inspeção, baseada nas [heurísticas de Nielsen](https://www.nngroup.com/articles/ten-usability-heuristics/).

| Achado | Alteração aplicada |
| --- | --- |
| A01 — Ações fora de ordem | Etapas Preparar, Gravar e Resultado; avaliação habilitada somente com texto/palavra e áudio. Validações no servidor preservadas. |
| A02 — Reinício apaga histórico | Nova leitura limpa a atividade atual e conserva as leituras anteriores da sessão. |
| A03 — Galeria móvel | Duas colunas no celular, quatro no computador, legendas com quebra de linha e confirmação textual da seleção. |
| A04 — Atividades ocultas | Abas curtas Leitura, Palavras e Missões, com títulos completos dentro de cada atividade. |
| A05 — Excesso na primeira tela | Mascote e ajuda opcionais recolhidos; gravação e resultado aparecem conforme a atividade avança. Detalhes ficam em área expansível para o responsável. |
| A06 — Espera pouco clara | Mensagens específicas de preparação e análise; bloqueio temporário de ações e aviso sobre a primeira análise de áudio. Sem porcentagens de processamento inventadas. |
| A07 — Ajuda de áudio tardia | Ouvir um exemplo disponível assim que a palavra é escolhida. |
| A08 — Erros técnicos | Mensagens curtas com orientação para tentar novamente; detalhes das falhas no servidor. Controles principais em português e rodapé técnico oculto. |
| A09 — Retrabalho no login | Usuário preservado após senha incorreta; mensagem mais simples e opção Mostrar senha no login e cadastro. Senhas não são persistidas pelo script. |
| A10 — Duração do progresso | Usuário conectado no cabeçalho e aviso explícito de que o histórico vale apenas para a sessão. |
| A11 — Rótulos e retorno | Ações mais curtas, incentivo à prática e explicação de que a transcrição não confirma cada som da pronúncia. |
| A12 — Ajuda por descoberta | Instruções próximas ao gravador e descrição em texto do mascote selecionado, sem depender do ponteiro. |

O modo claro/escuro utiliza a mesma paleta no login, cadastro e atividades. A preferência fica no navegador; a troca não reinicia a atividade.

## Conferência

- Testes de regressão para preservação do histórico, validação antes de abrir o reconhecedor e mensagens de falha sem detalhes internos.
- Testes existentes de cadastro, persistência de contas, proteção dos endpoints, saída de sessão e decodificação de áudio.
- Conferência no navegador: login, geração de texto, envio de áudio, análise, histórico após Nova leitura, ajuda de palavras, navegação móvel e aparência clara/escura.
- Visualização móvel em 390 × 844 px: três atividades visíveis e galeria em duas colunas.

Execute os testes com `python -m unittest discover -s tests -v` na pasta do projeto.

## Limites desta etapa

A conferência é técnica e por inspeção; ainda é necessário testar com crianças e educadores. O progresso não é salvo na conta e não foi incluído cancelamento de análises em andamento. Alguns rótulos auxiliares dos componentes nativos do Gradio ainda podem aparecer em inglês. O reconhecedor continua sujeito a erros: não mede a pronúncia de forma clínica ou fonética.
