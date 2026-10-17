# Historico das sessoes de IA

O case pede o historico de **todas** as sessoes, de construcao e de preparacao, sem edicao
alem de remover chaves de API e dados pessoais.

| Arquivo | Quem | Ferramenta | Quando | Cobertura |
|---|---|---|---|---|
| `MOMENTOS.md` | time | — | — | os quatro momentos que mudaram a direcao do trabalho |
| `sessao-01-claude-aaron.md` | Aaron Romulo | Claude (Opus 5) | 17/10 | log da sessao exportado por maquina, **16h38 as 18h13**, com os comandos executados |
| `sessao-01-claude-aaron-chat-completo.md` | Aaron Romulo | Claude (Opus 5) | 17/10 | a conversa inteira, **08h42 as 18h34**: 64 mensagens de Aaron e 64 respostas |
| `sessao-02-gemini-guilherme-barros.pdf` | Guilherme Barros | Gemini | 16 e 17/10 | sessao completa, exportada da tela |

A sessao do Claude esta em dois arquivos, que se complementam e nenhum dos dois foi editado:

- `sessao-01-claude-aaron-chat-completo.md` e a **conversa inteira**, do primeiro prompt as
  08h42 ao ultimo as 18h34, exportada pela API do claude.ai. Os prints de tela que Aaron
  mandou ao longo do dia aparecem marcados no ponto em que foram enviados. O raciocinio
  interno do modelo ficou de fora: e interno, nao e um prompt.
- `sessao-01-claude-aaron.md` e o **log de maquina** do trecho final (16h38 as 18h13) e
  registra, alem das mensagens, **cada comando que foi efetivamente executado** e o seu
  resultado - o que a tela do chat nao mostra.

O link desta sessao do Claude tambem esta em **todos os commits** do repositorio, na linha
`Claude-Session:` da mensagem. `git log` mostra a sequencia inteira do trabalho com horario.
