// core/config.c
#include "server_config.h"
#include "vhost.h"

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <ctype.h>

/* =========================
   Main config loader
   ========================= */

int load_main_config(server_config_t* cfg, const char* path, char* out_listen_ip, size_t ip_len) {
    FILE* f = fopen(path, "r");
    if (!f) {
        perror("fopen sandhydra.conf");
        return -1;
    }

    // Set defaults
    strncpy(cfg->server_name, "SandHydra", sizeof(cfg->server_name) - 1);
    strncpy(cfg->server_version, "1.0", sizeof(cfg->server_version) - 1);
    strncpy(cfg->log_level, "normal", sizeof(cfg->log_level) - 1);
    cfg->listen_port = 8080;
    strncpy(out_listen_ip, "0.0.0.0", ip_len - 1);

    char line[512];
    while (fgets(line, sizeof(line), f)) {
        char* comment = strchr(line, '#');
        if (comment) *comment = '\0';

        char* key = strtok(line, "=\r\n");
        char* value = strtok(NULL, "\r\n");

        if (!key || !value)
            continue;

        // Trim leading whitespace
        while (isspace((unsigned char)*key)) key++;
        while (isspace((unsigned char)*value)) value++;

        if (strcmp(key, "server_name") == 0) {
            strncpy(cfg->server_name, value, sizeof(cfg->server_name) - 1);
        }
        else if (strcmp(key, "server_version") == 0) {
            strncpy(cfg->server_version, value, sizeof(cfg->server_version) - 1);
        }
        else if (strcmp(key, "listen_port") == 0) {
            cfg->listen_port = (unsigned short)atoi(value);
        }
        else if (strcmp(key, "listen_ip") == 0) {
            strncpy(out_listen_ip, value, ip_len - 1);
        }
        else if (strcmp(key, "log_level") == 0) {
            strncpy(cfg->log_level, value, sizeof(cfg->log_level) - 1);
        }
        else if (strcmp(key, "enable_keepalive") == 0) {
            cfg->enable_keepalive = atoi(value);
        }
        else if (strcmp(key, "max_keepalive_requests") == 0) {
            cfg->max_keepalive_requests = atoi(value);
        }
    }

    fclose(f);
    return 0;
}

/* =========================
   VHost config loader
   ========================= */

vhost_context_t* load_vhosts(const char* path) {
    FILE* f = fopen(path, "r");
    if (!f) {
        perror("fopen vhosts.conf");
        return NULL;
    }

    char line[512];
    vhost_context_t* head = NULL;
    vhost_context_t* current = NULL;

    while (fgets(line, sizeof(line), f)) {
        char* s = line;

        while (*s && isspace((unsigned char)*s)) s++;

        if (*s == '#' || *s == '\0' || *s == '\n') continue;

        if (strncmp(s, "[vhost:", 7) == 0) {
            char* end = strchr(s, ']');
            if (!end) continue;
            *end = '\0';

            vhost_context_t* v = calloc(1, sizeof(vhost_context_t));
            if (!v) continue;

            strncpy(v->hostname, s + 7, MAX_HOSTNAME_LEN - 1);
            strncpy(v->log_level, "normal", sizeof(v->log_level) - 1);
            v->enable_keepalive = 1;

            v->next = head;
            head = v;
            current = v;
            continue;
        }

        if (current) {
            char* key = strtok(s, "=\r\n");
            char* val = strtok(NULL, "\r\n");
            if (!key || !val) continue;

            while (*key && isspace((unsigned char)*key)) key++;
            while (*val && isspace((unsigned char)*val)) val++;

            if (strcmp(key, "docroot") == 0) {
                strncpy(current->docroot, val, MAX_PATH_LEN - 1);
            }
            else if (strcmp(key, "log_level") == 0) {
                strncpy(current->log_level, val, sizeof(current->log_level) - 1);
            }
            else if (strcmp(key, "python2_enabled") == 0) {
                current->python2_enabled = atoi(val);
            }
            else if (strcmp(key, "python3_enabled") == 0) {
                current->python3_enabled = atoi(val);
            }
            else if (strcmp(key, "enable_keepalive") == 0) {
                current->enable_keepalive = atoi(val);
            }
        }
    }

    fclose(f);
    return head;
}
