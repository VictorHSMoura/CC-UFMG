#include <inttypes.h>
#include <stdlib.h>
#include <stdio.h>
#include <stddef.h>
#include <string.h>

#include <arpa/inet.h>

void logexit(const char *msg) {
    perror(msg);
    exit(EXIT_FAILURE);
}

int addrparse(const char *addrstr, const char *portstr, struct sockaddr_storage *storage) {
    if(addrstr == NULL || portstr == NULL) {
        return -1;
    }

    u_int16_t port = (u_int16_t)atoi(portstr); // unsigned short
    if (port == 0) {
        return -1;
    }
    port = htons(port); // host to network short

    // parse do endereço para IPv4
    struct in_addr inaddr4; // 32-bit IP address
    if (inet_pton(AF_INET, addrstr, &inaddr4)) {
        struct sockaddr_in *addr4 = (struct sockaddr_in *)storage;
        addr4->sin_family = AF_INET;
        addr4->sin_port = port;
        addr4->sin_addr = inaddr4;
        return 0;
    }

    // se o parse falhar, retorna -1
    return -1;
}

void addrtostr(const struct sockaddr *addr, char *str, ssize_t strsize) {
    int version;
    char addrstr[INET6_ADDRSTRLEN + 1] = "";
    uint16_t port;

    if (addr->sa_family == AF_INET) {
        version = 4;
        struct sockaddr_in *addr4 = (struct sockaddr_in *)addr;
        if(!inet_ntop(AF_INET, &(addr4->sin_addr), addrstr, INET6_ADDRSTRLEN + 1)) {
            logexit("ntop");
        }
        port = ntohs(addr4->sin_port); // network to host short
    } else {
        // no caso do protocolo não ser IPv4
        logexit("unknown protocol family.");
    }
    if(str) {
        snprintf(str, strsize, "IPv%d %s %hu", version, addrstr, port);
    }
}

int server_sockaddr_init(const char *proto, const char *portstr, struct sockaddr_storage *storage) {
    u_int16_t port = (u_int16_t)atoi(portstr); // unsigned short
    if (port == 0) {
        return -1;
    }
    port = htons(port); // host to network short

    memset(storage, 0, sizeof(*storage));
    if(0 == strcmp(proto, "v4")) {
        struct sockaddr_in *addr4 = (struct sockaddr_in *)storage;
        addr4->sin_family = AF_INET;
        addr4->sin_addr.s_addr = INADDR_ANY;
        addr4->sin_port = port;
        return 0;
    } else {
        // retorna -1 caso protocolo não seja IPv4
        return -1;
    }
}