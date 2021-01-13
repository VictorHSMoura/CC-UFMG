#include "common.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <sys/types.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <pthread.h>

#include <unistd.h>

#define BUFSZ 1024

void usage(int argc, char **argv) {
    printf("usage: %s <server IP> <server port>\n", argv[0]);
    printf("example: %s 127.0.0.1 51511\n", argv[0]);
    exit(EXIT_FAILURE);
}

struct client_data_listen {
    int sock;
};

void *client_listen_thread(void *data) {
    struct client_data_listen *cdata = (struct client_data_listen *)data;
    int sock = cdata->sock;

    while(1) {
        char buf[BUFSZ];
        memset(buf, 0, BUFSZ);
        unsigned total = 0;
        while(1) {
            int count = recv(sock, buf + total, BUFSZ - total, 0);
            total += count;
            if (count == 0 || buf[strlen(buf) - 1] == '\n') {
                // Connection terminated
                break;
            }
            
        }
        if (total == 0) {
            close(sock);
            pthread_exit(EXIT_SUCCESS);
        }

        // printf("received %u bytes\n", total);
        printf("%s", buf);
    }
    pthread_exit(EXIT_SUCCESS);
}

int main(int argc, char **argv) {
    if(argc < 3) {
        usage(argc, argv);
    }

    char *ip = argv[1];
    char *port = argv[2];

    struct sockaddr_storage storage;
    if(0 != addrparse(ip, port, &storage)) {
        usage(argc, argv);
    }

    int s;
    s = socket(storage.ss_family, SOCK_STREAM, 0);
    if(s == -1) {
        logexit("socket");
    }

    struct sockaddr *addr = (struct sockaddr *)(&storage);
    if(0 != connect(s, addr, sizeof(storage))) {
        logexit("connect");
    }

    char addrstr[BUFSZ];
    addrtostr(addr, addrstr, BUFSZ);
    
    printf("connected to %s\n", addrstr);

    struct client_data_listen *cdata = malloc(sizeof(*cdata));
    cdata->sock = s;

    pthread_t client_listen_thread_id;
    pthread_create(&client_listen_thread_id, NULL, client_listen_thread, cdata);

    while(1) {
        char buf[BUFSZ];
        memset(buf, 0, BUFSZ);
        
        // printf("mensagem> ");
        fgets(buf, BUFSZ-1, stdin);
        
        int count = send(s, buf, strlen(buf) + 1, 0);
        if (count != strlen(buf) + 1) {
            close(s);
            logexit("send");
        }
    }
    // close(s);
    
    exit(EXIT_SUCCESS);
}
