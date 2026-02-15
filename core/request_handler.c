// core/request_handler.c
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "server_config.h"
#include "vhost.h"
#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")
#ifdef _WIN32
#define strncasecmp _strnicmp
#endif

// Forward declarations
void serve_static_file(int client_fd, const char* full_path, vhost_context_t* vhost);
void serve_python_module(int client_fd, const char* script_path, vhost_context_t* vhost, server_config_t* cfg,
                         const char* method, const char* query_string, const char* post_body);

#define MAX_REQUEST 8192
#define MAX_POST_BODY 8192

// Find vhost by hostname
vhost_context_t* find_vhost(vhost_context_t* head, const char* host) {
    vhost_context_t* current = head;
    while (current) {
        if (strcmp(current->hostname, host) == 0) {
            return current;
        }
        current = current->next;
    }
    // fallback to default
    current = head;
    while (current) {
        if (strcmp(current->hostname, "default") == 0) return current;
        current = current->next;
    }
    return NULL; // should not happen if default exists
}

void handle_client(int client_fd, server_config_t* cfg, vhost_context_t* vhosts) {
    int keepalive = cfg->enable_keepalive; // global default
    int requests_served = 0;

    while (keepalive) {
        char buffer[MAX_REQUEST];
        int n = recv(client_fd, buffer, sizeof(buffer)-1, 0);
        if (n <= 0) break;
        buffer[n] = '\0';

        char method[16], path[512], protocol[16];
        char host_header[256] = "";
        char query_string[512] = "";
        char post_body[MAX_POST_BODY] = "";

        // Parse request line
        sscanf(buffer, "%15s %511s %15s", method, path, protocol);

        // Parse query string
        char* qmark = strchr(path, '?');
        if (qmark) {
            strncpy(query_string, qmark + 1, sizeof(query_string)-1);
            *qmark = '\0';
        }

        // Extract Host header
        char* host_ptr = strstr(buffer, "\nHost:");
        if (!host_ptr) host_ptr = strstr(buffer, "\r\nHost:");
        if (host_ptr) {
            host_ptr += 6;
            while (*host_ptr == ' ') host_ptr++;
            char* end = strpbrk(host_ptr, "\r\n");
            if (end) {
                size_t len = end - host_ptr;
                if (len < sizeof(host_header)) strncpy(host_header, host_ptr, len);
                host_header[len] = '\0';
            }
        }

        // Find vhost
        vhost_context_t* vhost = find_vhost(vhosts, host_header);
        if (!vhost) break;

        // Update keepalive based on vhost settings and request headers
        if (!vhost->enable_keepalive) keepalive = 0;

        // Check Connection header for "close"
        char* conn_ptr = strstr(buffer, "\nConnection:");
        if (!conn_ptr) conn_ptr = strstr(buffer, "\r\nConnection:");
        if (conn_ptr) {
            conn_ptr += 11;
            while (*conn_ptr == ' ') conn_ptr++;
            if (strncasecmp(conn_ptr, "close", 5) == 0) keepalive = 0;
        }

        // Extract POST body
        if (strcmp(method, "POST") == 0) {
            char* body = strstr(buffer, "\r\n\r\n");
            if (body) {
                body += 4;
                strncpy(post_body, body, sizeof(post_body)-1);
            }
        }

        // Build full path
        char full_path[1024];
        snprintf(full_path, sizeof(full_path), "%s%s", vhost->docroot, path);
        if (full_path[strlen(full_path)-1] == '/') 
            strncat(full_path, "index.html", sizeof(full_path) - strlen(full_path) - 1);

        // Serve content
        const char* ext = strrchr(full_path, '.');
        if (ext && strcmp(ext, ".py") == 0) {
            serve_python_module(client_fd, full_path, vhost, cfg, method, query_string, post_body);
        } else {
            serve_static_file(client_fd, full_path, vhost);
        }

        // Logging per request (inside loop)
        if (strcmp(cfg->log_level, "verbose") == 0 || strcmp(vhost->log_level, "verbose") == 0) {
            printf("[LOG] %s %s %s -> vhost=%s, path=%s\n",
                   method, path, protocol, vhost->hostname, full_path);
        }

        requests_served++;
        if (requests_served >= cfg->max_keepalive_requests) break;
    }

    closesocket(client_fd);

}
