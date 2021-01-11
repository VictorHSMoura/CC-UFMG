#include "common.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <unistd.h>

#include <sys/types.h>
#include <sys/socket.h>


#define BUFSZ 1024

void usage(int argc, char **argv) {
    printf("usage: %s <server port>\n", argv[0]);
    printf("example: %s 51511\n", argv[0]);
    exit(EXIT_FAILURE);
}

struct client_data {
    int csock;
    struct sockaddr_storage storage;
};

int check_text_valid(char *msg) {
    for(int i = 0; i < strlen(msg); i++) {
        if (!(msg[i] >= '0' && msg[i] <= '9') && !(msg[i] >= 'A' && msg[i] <= 'Z') && !(msg[i] >= 'a' && msg[i] <= 'z') && strchr(" ,.?!:;+-*/=@#$%%()[]{}", msg[i]) == NULL) {
                return 0;
        }
    }
    return 1;
}

// TODO: arrumar forma de fechar sock de mensagem quando necessário
int process_msg(int csock, char *msg) {
    int valid_msg = check_text_valid(msg);

    // checking invalid conditions
    if (valid_msg == 0) {
        sprintf(msg, "Conection closed due to invalid character\n");
        return 1;
    }
    
    if (strlen(msg) == 0 ) {
        sprintf(msg, "Conection closed due to blank message\n");
        return 2;
    }

    if (strlen(msg) > 500) {
        sprintf(msg, "Conection closed due to oversized message\n");
        return 3;
    }

    if (strcmp(msg, "##kill") == 0) {
        close(csock);
        return 4;
    }

    // tag subscription
    // TODO: acrescentar tags em lista de tags
    if (msg[0] == '+') {
        char tag[strlen(msg)];
        memcpy(tag, msg + 1, strlen(msg));
        sprintf(msg, "subscribed +%.488s\n", tag);
        return 0;
    } else if (msg[0] == '-') {
        char tag[strlen(msg)];
        memcpy(tag, msg + 1, strlen(msg));
        sprintf(msg, "unsubscribed -%.488s\n", tag);
        return 0;
    } else {
        

    }
    
    return 0;
}

void *client_thread(void *data) {
    struct client_data *cdata = (struct client_data *)data;
    struct sockaddr *caddr = (struct sockaddr *)(&cdata->storage);

    char caddrstr[BUFSZ];
    addrtostr(caddr, caddrstr, BUFSZ);

    printf("[log] connection from %s\n", caddrstr);

    char buf[BUFSZ];
    memset(buf, 0, BUFSZ);
    ssize_t count = recv(cdata->csock, buf, BUFSZ, 0);

    
    if(buf[strlen(buf) - 1] == '\n') {
        buf[strlen(buf) - 1] = '\0';
    }
    
    int status = process_msg(cdata->csock, buf);
    
    if (status == 0) {
        printf("[msg] %s, %d bytes: %s\n", caddrstr, (int)count, buf);

        // sprintf(buf, "remote endpoint: %.1000s\n", caddrstr);
    } else if (status == 1) {
        printf("[log] Client %s disconnected due to invalid character\n", caddrstr);
    } else if (status == 2) {
        printf("[log] Client %s disconnected due to blank message\n", caddrstr);
    } else if (status == 3) {
        printf("[log] Client %s disconnected due to oversized message\n", caddrstr);
    } else if (status == 4) {
        printf("[log] Client %s disconnected due to ##kill\n", caddrstr);
        pthread_exit(EXIT_SUCCESS);
        exit(EXIT_SUCCESS);
    }

    count = send(cdata->csock, buf, strlen(buf) + 1, 0);
    if (count != strlen(buf) + 1) {
        logexit("send");
    }
    close(cdata->csock);

    pthread_exit(EXIT_SUCCESS);
}

int main(int argc, char **argv) {
    if(argc < 2) {
        usage(argc, argv);
    }

    char *ip = "v4";
    char *port = argv[1];

    struct sockaddr_storage storage;
    if(0 != server_sockaddr_init(ip, port, &storage)) {
        usage(argc, argv);
    }

    int s;
    s = socket(storage.ss_family, SOCK_STREAM, 0);
    if(s == -1) {
        logexit("socket");
    }

    int enable = 1;
    if(0 != setsockopt(s, SOL_SOCKET, SO_REUSEADDR, &enable, sizeof(int))) {
        logexit("setsockopt");
    }

    struct sockaddr *addr = (struct sockaddr *)(&storage);
    if(0 != bind(s, addr, sizeof(storage))){
        logexit("bind");
    }

    if(0 != listen(s, 10)) {
        logexit("listen");
    }

    char addrstr[BUFSZ];
    addrtostr(addr, addrstr, BUFSZ);
    
    printf("bound to %s, waiting connections\n", addrstr);

    while(1) {
        struct sockaddr_storage cstorage;
        struct sockaddr *caddr = (struct sockaddr *)(&cstorage);
        socklen_t caddrlen = sizeof(cstorage);

        int csock = accept(s, caddr, &caddrlen);
        if(csock == -1) {
            logexit("accept");
        }

        struct client_data *cdata = malloc(sizeof(*cdata));
        if(!cdata) {
            logexit("malloc");
        }
        cdata->csock = csock;
        memcpy(&(cdata->storage), &storage, sizeof(storage));

        pthread_t tid;
        pthread_create(&tid, NULL, client_thread, cdata);
    }

    exit(EXIT_SUCCESS);
}