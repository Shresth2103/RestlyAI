#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include <errno.h>
#include <time.h>
#include "command_queue.h"
#include "config.h"

#define MAX_LINE_LENGTH 1024

static char* get_queue_file_path() {
    static char path[512];
    const char* home = getenv("HOME");
    if (!home) {
        return NULL;
    }
    snprintf(path, sizeof(path), "%s/.config/restly/commands/queue.jsonl", home);
    return path;
}

static void ensure_queue_dir() {
    const char* home = getenv("HOME");
    if (!home) return;
    
    char dir_path[512];
    snprintf(dir_path, sizeof(dir_path), "%s/.config/restly/commands", home);
    
    // Create directory recursively
    char *p = dir_path;
    while (*p) {
        if (*p == '/' && p != dir_path) {
            *p = '\0';
            mkdir(dir_path, 0755);
            *p = '/';
        }
        p++;
    }
    mkdir(dir_path, 0755);
}

CommandAction parse_command_line(const char* line) {
    CommandAction action = {0};
    action.type = CMD_UNKNOWN;
    
    if (!line || strlen(line) == 0) {
        return action;
    }
    
    // Simple JSON parsing for our specific format
    if (strstr(line, "set_session")) {
        action.type = CMD_SET_SESSION;
        
        // Extract duration_minutes from params object
        char* duration_str = strstr(line, "\"duration_minutes\":");
        if (duration_str) {
            duration_str += strlen("\"duration_minutes\":");
            action.params.session.duration_minutes = atoi(duration_str);
        } else {
            action.params.session.duration_minutes = 45; // default
        }
        
        // Extract type from params object
        if (strstr(line, "\"type\":\"deep_work\"")) {
            strncpy(action.params.session.type, "deep_work", sizeof(action.params.session.type) - 1);
        } else {
            strncpy(action.params.session.type, "work", sizeof(action.params.session.type) - 1);
        }
    }
    else if (strstr(line, "toggle_pause")) {
        action.type = CMD_TOGGLE_PAUSE;
    }
    else if (strstr(line, "summarize_day")) {
        action.type = CMD_SUMMARIZE_DAY;
    }
    else if (strstr(line, "reschedule_break")) {
        action.type = CMD_RESCHEDULE_BREAK;
        
        // Extract delay_minutes if present
        char* delay_str = strstr(line, "\"delay_minutes\":");
        if (delay_str) {
            delay_str += strlen("\"delay_minutes\":");
            action.params.reschedule.delay_minutes = atoi(delay_str);
        } else {
            action.params.reschedule.delay_minutes = 15; // default
        }
    }
    else if (strstr(line, "nl_command")) {
        action.type = CMD_NL_COMMAND;
        
        // Extract the text field - simple extraction between quotes
        // Handle both "text":"value" and "text": "value" (with space)
        char* text_start = strstr(line, "\"text\":");
        if (text_start) {
            text_start += strlen("\"text\":");
            // Skip any whitespace after the colon
            while (*text_start == ' ' || *text_start == '\t') {
                text_start++;
            }
            // Skip the opening quote
            if (*text_start == '"') {
                text_start++;
            } else {
                text_start = NULL; // Invalid format
            }
        }
        if (text_start) {
            char* text_end = strchr(text_start, '"');
            if (text_end && (text_end - text_start) < sizeof(action.params.nl_command.text) - 1) {
                size_t text_len = text_end - text_start;
                strncpy(action.params.nl_command.text, text_start, text_len);
                action.params.nl_command.text[text_len] = '\0';
                // Initialize the rest of the buffer to be safe
                memset(action.params.nl_command.text + text_len + 1, 0, sizeof(action.params.nl_command.text) - text_len - 1);
            } else {
                // Failed to extract - clear the text buffer
                memset(action.params.nl_command.text, 0, sizeof(action.params.nl_command.text));
            }
        } else {
            // No text field found - clear the text buffer
            memset(action.params.nl_command.text, 0, sizeof(action.params.nl_command.text));
        }
    }
    
    return action;
}

int process_command_queue() {
    const char* queue_file = get_queue_file_path();
    if (!queue_file) {
        return 0;
    }
    
    FILE* file = fopen(queue_file, "r");
    if (!file) {
        // No queue file yet, that's fine
        return 0;
    }
    
    char line[MAX_LINE_LENGTH];
    int commands_processed = 0;
    
    // Read all commands
    while (fgets(line, sizeof(line), file)) {
        // Remove newline
        line[strcspn(line, "\n")] = 0;
        
        if (strlen(line) == 0) continue;
        
        printf("DEBUG: Processing line: %s\n", line);
        CommandAction action = parse_command_line(line);
        printf("DEBUG: Parsed command type: %d\n", action.type);
        if (action.type != CMD_UNKNOWN) {
            // Process the command
            printf("DEBUG: Executing command\n");
            execute_command(&action);
            commands_processed++;
        }
    }
    
    fclose(file);
    
    // Clear the queue file after processing
    if (commands_processed > 0) {
        truncate(queue_file, 0);
    }
    
    return commands_processed;
}


