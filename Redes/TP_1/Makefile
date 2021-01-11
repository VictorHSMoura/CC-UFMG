all:
	gcc -Wall -c common.c
	gcc -Wall client.c common.o -o cliente
	gcc -Wall server.c common.o -lpthread -o servidor