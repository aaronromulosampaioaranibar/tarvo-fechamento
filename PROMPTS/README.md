# Historico das sessoes de IA

O case pede o historico de **todas** as sessoes, de construcao e de preparacao, sem edicao
alem de remover chaves de API e dados pessoais.

| Arquivo | Quem | Ferramenta | Quando | Cobertura |
|---|---|---|---|---|
| `MOMENTOS.md` | time | — | — | os quatro momentos que mudaram a direcao do trabalho |
| `sessao-01-claude-aaron.md` | Aaron Romulo | Claude (Opus 5) | 17/10 | log da sessao exportado por maquina, **16h38 as 18h13**, com os comandos executados |
| `sessao-01-claude-aaron-chat-completo.pdf` | Aaron Romulo | Claude (Opus 5) | 17/10 | a conversa inteira como ela aparece na tela, **08h42 as 19h** |
| `sessao-02-gemini-guilherme-barros.md` | Guilherme Barros | Gemini | 16 e 17/10 | sessao completa |

Sobre a sessao do Claude, em duas partes: o log de maquina (`.md`) registra tambem **cada
comando que foi efetivamente executado** e o resultado, coisa que a tela do chat nao mostra,
mas so existe a partir das 16h38. O PDF cobre o dia inteiro, do primeiro prompt ao ultimo,
do jeito que a conversa aconteceu. Nenhum dos dois foi editado.

O link desta sessao do Claude tambem esta em **todos os commits** do repositorio, na linha
`Claude-Session:` da mensagem. `git log` mostra a sequencia inteira do trabalho com horario.
