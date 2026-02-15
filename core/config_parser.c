// core/config_parser.c
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "server_config.h"

server_config_t parse_server_config(const char *filename) {
    server_config_t cfg;
    memset(&cfg, 0, sizeof(cfg));

    FILE *file = fopen(filename, "r");
    if (!file) {
        perror("Failed to open sandhydra.conf");
        return cfg;
    }

    char line[1024];
    while (fgets(line, sizeof(line), file)) {
        // Remove newline
        line[strcspn(line, "\r\n")] = 0;

        // Skip empty lines and comments
        if (line[0] == '\0' || line[0] == '#')
            continue;

        char *eq = strchr(line, '=');
        if (!eq) continue;
        *eq = '\0';
        char *key = line;
        char *value = eq + 1;
        while (*value == ' ') value++; // trim leading space

        if (strcmp(key, "server_name") == 0) {
            strncpy(cfg.server_name, value, MAX_NAME_LEN-1);
        } else if (strcmp(key, "server_version") == 0) {
            strncpy(cfg.server_version, value, MAX_NAME_LEN-1);
        } else if (strcmp(key, "log_level") == 0) {
            strncpy(cfg.log_level, value, sizeof(cfg.log_level)-1);
        } else if (strcmp(key, "log_file") == 0) {
            strncpy(cfg.log_file, value, MAX_LOGFILE_LEN-1);
        } else if (strcmp(key, "python2_enabled") == 0) {
            cfg.python2_enabled = (strcmp(value, "true") == 0);
        } else if (strcmp(key, "python3_enabled") == 0) {
            cfg.python3_enabled = (strcmp(value, "true") == 0);
        } else if (strcmp(key, "python2_path") == 0) {
            strncpy(cfg.python2_path, value, MAX_PATH_LEN-1);
        } else if (strcmp(key, "python3_path") == 0) {
            strncpy(cfg.python3_path, value, MAX_PATH_LEN-1);
        } else if (strcmp(key, "max_connections") == 0) {
            cfg.max_connections = atoi(value);
        } else if (strcmp(key, "listen_address") == 0) {
            strncpy(cfg.listen_address, value, sizeof(cfg.listen_address)-1);
        } else if (strcmp(key, "listen_port") == 0) {
            cfg.listen_port = (unsigned short)atoi(value);
        } else if (strcmp(key, "default_vhost") == 0) {
            strncpy(cfg.default_vhost, value, MAX_NAME_LEN-1);
        } else if (strcmp(key, "timeout_request") == 0) {
            cfg.timeout_request = atoi(value);
        } else if (strcmp(key, "timeout_response") == 0) {
            cfg.timeout_response = atoi(value);
        } else if (strcmp(key, "max_request_size") == 0) {
            cfg.max_request_size = atoi(value);
        } else if (strcmp(key, "enable_keepalive") == 0) {
            cfg.enable_keepalive = (strcmp(value, "true") == 0);
        } else if (strcmp(key, "max_keepalive_requests") == 0) {
            cfg.max_keepalive_requests = atoi(value);
        } else if (strcmp(key, "mime_types") == 0) {
            strncpy(cfg.mime_types, value, MAX_PATH_LEN-1);
        } else if (strcmp(key, "server_advertise") == 0) {
            cfg.server_advertise = (strcmp(value, "true") == 0);
        } else if (strcmp(key, "SSL_path") == 0) {
            strncpy(cfg.SSL_path, value, MAX_PATH_LEN-1);
        } else if (strcmp(key, "TLS_path") == 0) {
            strncpy(cfg.TLS_path, value, MAX_PATH_LEN-1);
        } else if (strcmp(key, "vhost_reload_interval") == 0) {
            cfg.vhost_reload_interval = atoi(value);
        } else if (strcmp(key, "enable_cors") == 0) {
            cfg.enable_cors = (strcmp(value, "true") == 0);
        }
    }

    fclose(file);
    return cfg;
}
