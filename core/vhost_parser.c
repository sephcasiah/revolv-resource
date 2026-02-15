// core/vhost_parser.c
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "vhost.h"

vhost_context_t* parse_vhosts(const char *filename) {
    FILE *file = fopen(filename, "r");
    if (!file) {
        perror("Failed to open vhosts.conf");
        return NULL;
    }

    vhost_context_t *head = NULL;
    vhost_context_t *current = NULL;
    char line[1024];

    while (fgets(line, sizeof(line), file)) {
        // Remove newline
        line[strcspn(line, "\r\n")] = 0;

        // Skip empty lines and comments
        if (line[0] == '\0' || line[0] == '#')
            continue;

        if (strncmp(line, "[vhost:", 7) == 0) {
            // Start new vhost block
            vhost_context_t *v = calloc(1, sizeof(vhost_context_t));
            // Extract hostname inside brackets
            char *end = strchr(line, ']');
            if (end) {
                size_t len = end - (line + 7);
                strncpy(v->hostname, line + 7, len);
                v->hostname[len] = '\0';
            }
            // Add to linked list
            if (!head)
                head = v;
            else
                current->next = v;
            current = v;
        } else if (current) {
            // Key-value parsing: key = value
            char *eq = strchr(line, '=');
            if (!eq) continue;
            *eq = '\0';
            char *key = line;
            char *value = eq + 1;
            while (*value == ' ') value++; // trim leading space

            if (strcmp(key, "docroot") == 0) {
                strncpy(current->docroot, value, MAX_PATH_LEN - 1);
            } else if (strcmp(key, "python2_enabled") == 0) {
                current->python2_enabled = (strcmp(value, "true") == 0);
            } else if (strcmp(key, "python3_enabled") == 0) {
                current->python3_enabled = (strcmp(value, "true") == 0);
            } else if (strcmp(key, "log_level") == 0) {
                strncpy(current->log_level, value, sizeof(current->log_level) - 1);
            } else if (strcmp(key, "vhost_log") == 0) {
                strncpy(current->vhost_log, value, MAX_LOGFILE_LEN - 1);
            } else if (strcmp(key, "enable_cors") == 0) {
                current->enable_cors = (strcmp(value, "true") == 0);
            } else if (strcmp(key, "enable_SSL_TLS") == 0) {
                current->enable_ssl_tls = (strcmp(value, "true") == 0);
            } else if (strcmp(key, "SSL_path") == 0) {
                strncpy(current->ssl_path, value, MAX_PATH_LEN - 1);
            } else if (strcmp(key, "TLS_path") == 0) {
                strncpy(current->tls_path, value, MAX_PATH_LEN - 1);
            }
        }
    }

    fclose(file);
    return head;
}
