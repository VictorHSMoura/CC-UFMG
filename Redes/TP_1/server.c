#include "common.h"
#include "tag_list.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <signal.h>
#include <unistd.h>

#include <sys/types.h>
#include <sys/socket.h>


#define BUFSZ 1024

// Global reference to all the tags created, all threads and kill process
tag_list all_tags;
user_list all_threads;

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
    int start_index = 0, end_index = 0, hadHash = 0, validHash = 0, tag_count = 0;
    for(int i = 0; i < strlen(msg); i++) {
        if (msg[i] == '#' && (i != strlen(msg) - 1 && msg[i + 1] != ' ') && hadHash == 0) {
            start_index = i;
            hadHash = 1;
        }
        if (hadHash == 1 && ((i != strlen(msg) - 1 && msg[i+1] == ' ') ||  i == strlen(msg) - 1)) {
            validHash = 1;
        }
        if (hadHash == 1 && validHash == 1) {
            end_index = i;
            hadHash = 0;
            validHash = 0;
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
    int count;

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

    char out_msg[BUFSZ];
    memset(out_msg, 0, BUFSZ);

    // tag subscription
    // TODO: acrescentar tags em lista de tags
    if (msg[0] == '+') {
        char tag[strlen(msg)];
        memcpy(tag, msg + 1, strlen(msg));
        tag[strlen(msg) - 1] = '\0';

        tag_cell *user_tag_cell = tag_list_find(&all_tags, tag);
        
        // se a tag não for encontrada na lista, uma nova tag é criada
        if (user_tag_cell == NULL) {
            tag_list_add_item_end(&all_tags, tag);
            user_tag_cell = tag_list_get_last_item(&all_tags);
        } else {
            // pointer correction
            user_tag_cell = user_tag_cell->next;
        }

        if(user_list_find(&user_tag_cell->users, csock) != NULL) {
            sprintf(out_msg, "already subscribed +%.488s\n", tag);
            count = send(csock, out_msg, strlen(out_msg), 0);
        } else {
            user_list_add_item_end(&user_tag_cell->users, csock);
            sprintf(out_msg, "subscribed +%.488s\n", tag);
            count = send(csock, out_msg, strlen(out_msg), 0);
        }
    } else if (msg[0] == '-') {
        char tag[strlen(msg)];
        memcpy(tag, msg + 1, strlen(msg));

        tag_cell *user_tag_cell = tag_list_find(&all_tags, tag);
        if (user_tag_cell == NULL) {
            sprintf(msg, "not subscribed -%.488s\n", tag);
        } else {
            // pointer correction
            user_tag_cell = user_tag_cell->next;
            user_cell *user = user_list_find(&user_tag_cell->users, csock);
            if(user != NULL) {
                user_list_remove_by_pointer(&user_tag_cell->users, user);
                sprintf(out_msg, "unsubscribed -%.488s\n", tag);
                count = send(csock, out_msg, strlen(out_msg), 0);
            } else {
                sprintf(out_msg, "not subscribed -%.488s\n", tag);
                count = send(csock, out_msg, strlen(out_msg), 0);
            }
        }
        // sprintf(msg, "unsubscribed -%.488s\n", tag);
    } else {
        tag_list list;
        tag_list_make_empty_list(&list);
        user_list sent_users;
        user_list_make_empty_list(&sent_users);

        int count_tags = extract_tags(msg, &list);
        for(int i = 0; i < count_tags; i++) {
            char *tag = tag_list_get_first_item(&list)->tag;
            
            // checa usuarios inscritos na tag e distribui mensagem
            tag_cell *tag_in_list = tag_list_find(&all_tags, tag);
            if (tag_in_list != NULL) {
                user_list users = tag_in_list->next->users;
                user_cell *info = users.start->next;

                while(info != NULL) {
                    if(user_list_find(&sent_users, info->user_id) == NULL && info->user_id != csock) {
                        sprintf(out_msg, "%s\n", msg);
                        count = send(info->user_id, out_msg, strlen(out_msg), 0);
                        if (count != strlen(out_msg)) {
                            logexit("send");
                        }
                        user_list_add_item_end(&sent_users, info->user_id);
                    }
                    info = info->next;
                }
            }
            // remove tag da lista temporária
            tag_list_remove_item_start(&list);
        }
        user_list_free_list(&sent_users);
        tag_list_free_list(&list);
    }

    printf("[msg] %s\n", out_msg);
    return 0;
}

void clean_user_tags(int csock) {
    for(tag_cell* tag_in_list = tag_list_get_first_item(&all_tags); tag_in_list != NULL; tag_in_list = tag_in_list->next) {
        user_list user = tag_in_list->users;
        
        user_cell *user_in_list = user_list_find(&user, csock);
        if (user_in_list != NULL) {
            user_list_remove_by_pointer(&user, user_in_list);
        }
    }
}

void *client_thread(void *data) {
    struct client_data *cdata = (struct client_data *)data;
    struct sockaddr *caddr = (struct sockaddr *)(&cdata->storage);

    char caddrstr[BUFSZ];
    addrtostr(caddr, caddrstr, BUFSZ);
    printf("[log] connection from %s\n", caddrstr);

    while(1) {
        char buf[BUFSZ];
        memset(buf, 0, BUFSZ);

        int total = 0;

        while(1) {
            int count = recv(cdata->csock, buf + total, BUFSZ - total, 0);
            total += count;
            if(count == 0 || buf[strlen(buf) - 1] == '\n')
                break;
        }

        if(total == 0) {
            printf("[log] Connection with %s has been closed on the client side\n", caddrstr);
            break;
        }
        printf("%s", buf);
        char *msg;

        msg = strtok(buf, "\n");
        while (msg != NULL) {
            char formatted_msg[strlen(msg) + 1];
            memcpy(formatted_msg, msg, strlen(msg));
            formatted_msg[strlen(msg)] = '\0';

            int status = process_msg(cdata->csock, formatted_msg);
            
            if (status == 1) {
                printf("[log] Client %s disconnected due to invalid character\n", caddrstr);
                break;
            } else if (status == 2) {
                printf("[log] Client %s disconnected due to blank message\n", caddrstr);
                break;
            } else if (status == 3) {
                printf("[log] Client %s disconnected due to oversized message\n", caddrstr);
                break;
            } else if (status == 4) {
                printf("[log] Client %s disconnected due to ##kill\n", caddrstr);
                
                user_cell *thread = all_threads.start->next;
                for (user_cell *open_thread = thread; open_thread != NULL; open_thread = open_thread->next) {
                    if (open_thread->user_id != (int) pthread_self()) {
                        pthread_cancel(open_thread->user_id);
                        pthread_join(open_thread->user_id, NULL);
                    }
                }
                user_list_free_list(&all_threads);
                tag_list_free_list(&all_tags);
                close(cdata->csock);
                free(cdata);
                exit(EXIT_SUCCESS);
                // break;
            }
            msg = strtok(NULL, "\n");
        }
    }

    close(cdata->csock);

    clean_user_tags(cdata->csock);
    user_list_remove_by_pointer(&all_threads, user_list_find(&all_threads, pthread_self()));

    free(cdata);

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
    user_list_make_empty_list(&all_threads);

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
        memcpy(&(cdata->storage), &cstorage, sizeof(cstorage));

        pthread_t tid;
        pthread_create(&tid, NULL, client_thread, cdata);
        user_list_add_item_end(&all_threads, (int)tid);
    }

    exit(EXIT_SUCCESS);
}