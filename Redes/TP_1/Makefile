all:
	gcc -Wall -c common.c
	gcc -Wall -c user_list.c
	gcc -Wall -c tag_list.c
	gcc -Wall -g client.c common.o -o cliente
	gcc -Wall -g server.c common.o user_list.o tag_list.o -lpthread -o servidor