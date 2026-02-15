#define _WINSOCK_DEPRECATED_NO_WARNINGS
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")
#include <signal.h>
#include "server_config.h"
#include "vhost.h"
#include "request_handler.h"

// Graceful shutdown flag
volatile sig_atomic_t running = 1;

// Signal handler
void handle_sigint(int sig) {
    running = 0;
}

// Load configs
int server_init(server_config_t* cfg, vhost_context_t** vhosts, char* listen_ip, size_t ip_len) {
    int main_ok = load_main_config(cfg, "config/sandhydra.conf", listen_ip, ip_len);
    int vhost_ok = 0;

    if (main_ok != 0) {
        fprintf(stderr, "Failed to load main config: config/sandhydra.conf\n");
        return -1;
    }

    *vhosts = load_vhosts("config/vhosts.conf");
    if (*vhosts != NULL) {
        vhost_ok = 1;
    }
    else {
        fprintf(stderr, "Failed to load vhosts config: config/vhosts.conf\n");
        return -1;
    }

    printf("====================================\n");
    printf("SandHydra v%s starting...\n", cfg->server_version[0] ? cfg->server_version : "0.1");
    printf("Main config: %s\n", main_ok == 0 ? "loaded" : "NOT FOUND");
    printf("Vhosts config: %s\n", vhost_ok == 1 ? "loaded" : "NOT FOUND");
    printf("Listening on %s:%d\n",
        listen_ip && strlen(listen_ip) > 0 ? listen_ip : "0.0.0.0",
        cfg->listen_port);
    printf("====================================\n");

    return 0;
}

int main() {
    server_config_t cfg;
    vhost_context_t* vhosts = NULL;
    char listen_ip[64];

    WSADATA wsa;
    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) {
        fprintf(stderr, "WSAStartup failed\n");
        return 1;
    }

    signal(SIGINT, handle_sigint);

    if (server_init(&cfg, &vhosts, listen_ip, sizeof(listen_ip)) != 0) {
        WSACleanup();
        return 1;
    }

    int listen_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (listen_fd < 0) { perror("socket"); WSACleanup(); return 1; }

    int opt = 1;
    setsockopt(listen_fd, SOL_SOCKET, SO_REUSEADDR, (const char*)&opt, sizeof(opt));

    struct sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_port = htons(cfg.listen_port);
    addr.sin_addr.s_addr = (listen_ip && strlen(listen_ip) > 0)
        ? inet_addr(listen_ip)
        : INADDR_ANY;

    if (bind(listen_fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        perror("bind"); closesocket(listen_fd); WSACleanup(); return 1;
    }

    if (listen(listen_fd, cfg.max_connections) < 0) {
        perror("listen"); closesocket(listen_fd); WSACleanup(); return 1;
    }

    while (running) {
        struct sockaddr_in client_addr;
        int client_len = sizeof(client_addr);
        int client_fd = accept(listen_fd, (struct sockaddr*)&client_addr, &client_len);
        if (client_fd < 0) { perror("accept"); continue; }

        handle_client(client_fd, &cfg, vhosts);
    }

    printf("\nShutting down server...\n");
    closesocket(listen_fd);
    WSACleanup();
    return 0;
}
