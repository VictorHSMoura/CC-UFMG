# Script de teste

Para executar os testes, você precisa estar executando o programa `tmux`
no terminal. O `tmux` será utilizado para abrir o servidor em uma janela
secundária paralelamente ao cliente.

Para executar o teste de exemplo, basta executar `./run-test.sh 1` após
colocar o binário `servidor` no diretório. O resultado do teste será
impresso na tela (`failed` em caso de falha e `passed` em caso de
sucesso).

O comando `!connect` serve para conectar clientes ao servidor e o
comando `!speel` serve para processar mensagens recebidas do servidor. O
comando `!sX` servem para enviar uma mensagem a partir do cliente X. O
comando `!jX` serve para empilhar, mas não enviar, uma mensagem pelo
cliente X. A próxima mensagem do cliente X (p.ex., enviada com `!sX`)
será precedida pela mensagem empilhada. O comando `!tX` envia uma
mensagem em dois pacotes de rede (induzindo recebimento parcial da
mensagem pelo `recv`).
