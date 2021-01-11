#pragma once

#include <stdlib.h>
#include <arpa/inet.h>

void logexit(const char *msg);
int addrparse(const char *addrstr, const char *portstr, struct sockaddr_storage *storage);
void addrtostr(const struct sockaddr *addr, char *str, ssize_t strsize);
int server_sockaddr_init(const char *proto, const char *portstr, struct sockaddr_storage *storage);