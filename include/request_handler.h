#pragma once
#ifndef REQUEST_HANDLER_H
#define REQUEST_HANDLER_H

#include "server_config.h"
#include "vhost.h"

void handle_client(int client_fd, struct server_config_t* cfg, struct vhost_context_t* vhosts);

#endif
