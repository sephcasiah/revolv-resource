// core/python_exec.c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "vhost.h"
#include "server_config.h"

// max body size for POST requests
#define MAX_POST_BODY 8192

void serve_python_module(int client_fd, const char* script_path, vhost_context_t* vhost, server_config_t* cfg,
                         const char* method, const char* query_string, const char* post_body) {
    char cmd[2048];
    const char* python_path = NULL;

    // Determine which interpreter to use
    if (vhost->python3_enabled) {
        python_path = (strlen(cfg->python3_path) > 0) ? cfg->python3_path : "python3";
    } else if (vhost->python2_enabled) {
        python_path = (strlen(cfg->python2_path) > 0) ? cfg->python2_path : "python2";
    } else {
        const char* err = "HTTP/1.1 403 Forbidden\r\n\r\nPython execution not allowed";
        send(client_fd, err, strlen(err), 0);
        return;
    }

    // Set environment variables for the script
    if (query_string) {
        _putenv_s("QUERY_STRING", query_string);
    } else {
        _putenv_s("QUERY_STRING", "");
    }

    if (post_body) {
        _putenv_s("CONTENT_LENGTH", "0");
    }

    // Prepare command: interpreter + script
    snprintf(cmd, sizeof(cmd), "%s %s", python_path, script_path);

    // Open subprocess
    FILE* fp = _popen(cmd, "w+"); // allow writing POST body if needed
    if (!fp) {
        const char* err = "HTTP/1.1 500 Internal Server Error\r\n\r\nFailed to run Python script";
        send(client_fd, err, strlen(err), 0);
        return;
    }

    // If POST, write body to stdin
    if (post_body && strcmp(method, "POST") == 0) {
        fwrite(post_body, 1, strlen(post_body), fp);
        fflush(fp);
    }

    // Read script output
    char output[MAX_POST_BODY];
    size_t n = fread(output, 1, sizeof(output)-1, fp);
    output[n] = '\0';
    _pclose(fp);

    // Send HTTP response
    char headers[256];
    snprintf(headers, sizeof(headers),
             "HTTP/1.1 200 OK\r\n"
             "Content-Length: %zu\r\n"
             "Content-Type: text/plain\r\n"
			 "%s" // CORS header
             "\r\n",
             n);

    send(client_fd, headers, strlen(headers), 0);
    send(client_fd, output, n, 0);

    // Logging
    if (strcmp(vhost->log_level, "verbose") == 0) {
        printf("[LOG] Served Python script %s using %s (method=%s, query=%s)\n",
               script_path, python_path, method, query_string ? query_string : "");
    }
}
