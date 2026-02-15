// core/static_serve.c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")
#include "vhost.h"

// Determine content type by file extension (basic)
const char* get_mime_type(const char* path) {
    const char* ext = strrchr(path, '.');
    if (!ext) return "application/octet-stream";

    if (strcmp(ext, ".html") == 0) return "text/html";
    if (strcmp(ext, ".css") == 0) return "text/css";
    if (strcmp(ext, ".js") == 0) return "application/javascript";
    if (strcmp(ext, ".json") == 0) return "application/json";
    if (strcmp(ext, ".png") == 0) return "image/png";
    if (strcmp(ext, ".jpg") == 0 || strcmp(ext, ".jpeg") == 0) return "image/jpeg";
    if (strcmp(ext, ".gif") == 0) return "image/gif";
    return "application/octet-stream";
}

// Serve a static file to client_fd
void serve_static_file(int client_fd, const char* full_path, vhost_context_t* vhost) {
    FILE* fp = fopen(full_path, "rb");
    if (!fp) {
        const char* notfound = "HTTP/1.1 404 Not Found\r\n\r\n404 Not Found";
        send(client_fd, notfound, strlen(notfound), 0);
        return;
    }

    struct stat st;
    stat(full_path, &st);
    size_t filesize = st.st_size;

    char headers[512];
    snprintf(headers, sizeof(headers),
             "HTTP/1.1 200 OK\r\n"
             "Content-Length: %zu\r\n"
             "Content-Type: %s\r\n"
             "%s" // CORS header placeholder
             "\r\n",
             filesize, get_mime_type(full_path),
             vhost->enable_cors ? "Access-Control-Allow-Origin: *\r\n" : "");
    send(client_fd, headers, strlen(headers), 0);

    char buffer[4096];
    size_t n;
    while ((n = fread(buffer, 1, sizeof(buffer), fp)) > 0) {
        send(client_fd, buffer, n, 0);
    }
    fclose(fp);

    if (strcmp(vhost->log_level, "verbose") == 0) {
        printf("[LOG] Served static file %s for vhost %s\n", full_path, vhost->hostname);
    }
}

