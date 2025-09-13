#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include "timer.h"
#include "daemon.h"
#include "config.h"
#include "activity_log.h"

// Signal handler for graceful shutdown
void signal_handler(int sig) {
    (void)sig; // Suppress unused parameter warning
    cleanup_activity_logging();
    exit(0);
}


int main(int argc, char *argv[])
{
    AppConfig config = parse_arguments(argc, argv);
    
    // Set up signal handlers for graceful shutdown
    signal(SIGTERM, signal_handler);
    signal(SIGINT, signal_handler);
    
    daemonize();

    start_timer(config);
    if(config.message) {
        free(config.message);
    }
    return 0;
}