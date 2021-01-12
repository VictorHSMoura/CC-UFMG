#include "common.h"
#include "tag_list.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <unistd.h>

#include <sys/types.h>
#include <sys/socket.h>


#define BUFSZ 1024

// Global reference to all the tags created
tag_list all_tags;

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

int extract_tags(char *msg, tag_list *list) {
    int start_index = 0, end_index = 0, hadHash = 0, tag_count = 0;
    for(int i = 0; i < strlen(msg); i++) {
        if (msg[i] == '#' && (i != strlen(msg) - 1 && msg[i + 1] != ' ') && hadHash == 0) {
            start_index = i;
            hadHash = 1;
        } else if(msg[i] == '#' && hadHash == 1) {
            hadHash = 0;
        }
        if ((msg[i] == ' ' || i == strlen(msg) - 1) && hadHash == 1) {
            end_index = i;
            hadHash = 0;
            tag_count++;
            int tag_size = end_index - start_index + 1;
            char tag[tag_size];
            memcpy(tag, msg + start_index + 1, tag_size);
            tag[tag_size - 1] = '\0';
            tag_list_add_item_end(list, tag);
        }
    }
    return tag_count;
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

        tag_cell *user_tag_cell = tag_list_find(&all_tags, tag);
        
        
        // se a tag não for encontrada na lista, uma nova tag é criada
        if (user_tag_cell == NULL) {
            tag_list_add_item_start(&all_tags, tag);
            user_tag_cell = tag_list_get_first_item(&all_tags);
            user_list_add_item_end(&user_tag_cell->users, csock);
        }

        if(user_list_find(&user_tag_cell->users, csock) != NULL) {
            sprintf(msg, "already subscribed +%.488s\n", tag);
        } else {
            user_list_add_item_end(&user_tag_cell->users, csock);
            sprintf(msg, "subscribed +%.488s\n", tag);
        }
        return 0;
    } else if (msg[0] == '-') {
        char tag[strlen(msg)];
        memcpy(tag, msg + 1, strlen(msg));
        sprintf(msg, "unsubscribed -%.488s\n", tag);
        return 0;
    } else {
        tag_list list;
        tag_list_make_empty_list(&list);

        int count = extract_tags(msg, &list);
        if (count > 0) {
            for(int i = 0; i < count; i++) {
                char *tag = tag_list_get_first_item(&list)->tag;
                
                // TODO: checa usuarios inscritos na tag e distribui mensagem

                // remove tag da lista temporária
                tag_list_remove_item_start(&list);
            }
        }
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

    tag_list_print_list(&all_tags);

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

    tag_list_make_empty_list(&all_tags);

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