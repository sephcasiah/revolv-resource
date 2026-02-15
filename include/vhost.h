// include/vhost.h
#ifndef VHOST_H
#define VHOST_H

#include <stdbool.h>

#define MAX_HOSTNAME_LEN 256
#define MAX_PATH_LEN 512
#define MAX_LOGFILE_LEN 256

typedef struct vhost_context {
    char hostname[MAX_HOSTNAME_LEN];   // e.g., "crest.eveonline.com"
    char docroot[MAX_PATH_LEN];        // filesystem path
    bool python2_enabled;
    bool python3_enabled;
    char log_level[16];                // "quiet", "normal", "verbose"
    char vhost_log[MAX_LOGFILE_LEN];   // per-vhost log file, e.g., "{vhost}.log"
    bool enable_cors;
    bool enable_ssl_tls;
    char ssl_path[MAX_PATH_LEN];       // optional
    char tls_path[MAX_PATH_LEN];       // optional
    int enable_keepalive;
    struct vhost_context *next;        // linked list of vhosts
} vhost_context_t;

#endif // VHOST_H
