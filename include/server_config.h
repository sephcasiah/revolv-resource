// include/server_config.h
#ifndef SERVER_CONFIG_H
#define SERVER_CONFIG_H

#include "vhost.h"
#include <stdbool.h>
#include <string.h>
#include <stddef.h>  // for size_t

#define MAX_NAME_LEN 128
#define MAX_PATH_LEN 512
#define MAX_LOGFILE_LEN 256

typedef struct server_config {
    // Server identity
    char server_name[MAX_NAME_LEN];       // "SandHydra"
    char server_version[MAX_NAME_LEN];    // optional version string

    // Logging
    char log_level[16];                   // "quiet", "normal", "verbose"
    char log_file[MAX_LOGFILE_LEN];       // global log file path

    // Python runtimes
    bool python2_enabled;
    bool python3_enabled;
    char python2_path[MAX_PATH_LEN];      // optional
    char python3_path[MAX_PATH_LEN];      // optional

    // HTTP / behavior
    unsigned int max_connections;
    char listen_address[64];              // legacy field, optional
    unsigned short listen_port;
    char default_vhost[MAX_NAME_LEN];     // fallback vhost
    unsigned int timeout_request;         // seconds
    unsigned int timeout_response;        // seconds
    unsigned int max_request_size;        // MB
    bool enable_keepalive;
    unsigned int max_keepalive_requests;
    char mime_types[MAX_PATH_LEN];        // path to mime.types file
    bool server_advertise;                // append Server: header?

    // Optional / future
    char SSL_path[MAX_PATH_LEN];          // global SSL path if enabled
    char TLS_path[MAX_PATH_LEN];          // global TLS path if enabled
    unsigned int vhost_reload_interval;   // seconds, 0 = disabled
    bool enable_cors;

} server_config_t;

// Main config loader
// out_listen_ip: buffer to receive the listen IP (default "0.0.0.0" if not set)
// ip_len: size of the buffer
int load_main_config(server_config_t* cfg, const char* path, char* out_listen_ip, size_t ip_len);

#endif // SERVER_CONFIG_H
