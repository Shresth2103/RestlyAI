#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/stat.h>
#include <unistd.h>
#include <errno.h>
#include "activity_log.h"

// Global variables for activity tracking
static FILE* log_file = NULL;
static char log_file_path[512];
static int daily_break_count = 0;
static int daily_work_minutes = 0;
static time_t session_start_time = 0;

// External variables from timer.c (we'll need to expose these)
extern bool is_paused;
extern bool in_deep_work_session;
extern time_t next_break_time;

void init_activity_logging(void) {
    // Create ~/.config/restly/activity/ directory
    char config_dir[256];
    snprintf(config_dir, sizeof(config_dir), "%s/.config/restly", getenv("HOME"));
    mkdir(config_dir, 0755);
    
    char activity_dir[256];
    snprintf(activity_dir, sizeof(activity_dir), "%s/activity", config_dir);
    mkdir(activity_dir, 0755);
    
    // Create daily log file with current date
    time_t now = time(NULL);
    struct tm* local_time = localtime(&now);
    char date_str[16];
    strftime(date_str, sizeof(date_str), "%Y-%m-%d", local_time);
    
    snprintf(log_file_path, sizeof(log_file_path), 
             "%s/activity_%s.jsonl", activity_dir, date_str);
    
    // Reset daily counters (in case app restarted same day)
    daily_break_count = 0;
    daily_work_minutes = 0;
    session_start_time = now;
    
    log_app_started();
}

const char* get_activity_log_path(void) {
    return log_file_path;
}

const char* event_type_to_string(ActivityEventType type) {
    switch (type) {
        case EVENT_BREAK_SHOWN: return "break_shown";
        case EVENT_BREAK_COMPLETED: return "break_completed";
        case EVENT_SESSION_STARTED: return "session_started";
        case EVENT_SESSION_ENDED: return "session_ended";
        case EVENT_PAUSE_TOGGLED: return "pause_toggled";
        case EVENT_BREAK_RESCHEDULED: return "break_rescheduled";
        case EVENT_COMMAND_RECEIVED: return "command_received";
        case EVENT_APP_STARTED: return "app_started";
        case EVENT_APP_STOPPED: return "app_stopped";
        default: return "unknown";
    }
}

const char* break_type_to_string(BreakType type) {
    switch (type) {
        case BREAK_TYPE_EYE_CARE: return "eye_care";
        case BREAK_TYPE_CUSTOM_MESSAGE: return "custom_message";
        default: return "unknown";
    }
}

const char* session_type_to_string(SessionType type) {
    switch (type) {
        case SESSION_TYPE_DEEP_WORK: return "deep_work";
        case SESSION_TYPE_REGULAR: return "regular";
        default: return "unknown";
    }
}

void get_current_system_state(ActivityEvent* event) {
    time_t current_time = time(NULL);
    
    // Note: These extern variables need to be exposed from timer.c
    event->system_state.is_paused = is_paused;
    event->system_state.in_deep_work_session = in_deep_work_session;
    event->system_state.next_break_in_minutes = (next_break_time - current_time) / 60;
    event->system_state.total_breaks_today = daily_break_count;
    event->system_state.total_work_minutes_today = daily_work_minutes + ((current_time - session_start_time) / 60);
}

void log_activity_event(ActivityEvent* event) {
    FILE* file = fopen(log_file_path, "a");
    if (!file) {
        fprintf(stderr, "Failed to open activity log file: %s\n", strerror(errno));
        return;
    }
    
    // Convert timestamp to ISO 8601 format
    struct tm* utc_time = gmtime(&event->timestamp);
    char timestamp_str[32];
    strftime(timestamp_str, sizeof(timestamp_str), "%Y-%m-%dT%H:%M:%SZ", utc_time);
    
    // Write JSON event
    fprintf(file, "{");
    fprintf(file, "\"timestamp\":\"%s\",", timestamp_str);
    fprintf(file, "\"event_type\":\"%s\",", event_type_to_string(event->event_type));
    
    // Event-specific data
    fprintf(file, "\"event_data\":{");
    switch (event->event_type) {
        case EVENT_BREAK_SHOWN:
        case EVENT_BREAK_COMPLETED:
            fprintf(file, "\"break_type\":\"%s\",", 
                   break_type_to_string(event->event_data.break_event.break_type));
            fprintf(file, "\"duration_seconds\":%d,", 
                   event->event_data.break_event.duration_seconds);
            if (event->event_type == EVENT_BREAK_COMPLETED) {
                fprintf(file, "\"user_dismissed\":%s,", 
                       event->event_data.break_event.user_dismissed ? "true" : "false");
            }
            break;
            
        case EVENT_SESSION_STARTED:
        case EVENT_SESSION_ENDED:
            fprintf(file, "\"session_type\":\"%s\",", 
                   session_type_to_string(event->event_data.session_event.session_type));
            fprintf(file, "\"duration_minutes\":%d,", 
                   event->event_data.session_event.duration_minutes);
            break;
            
        case EVENT_PAUSE_TOGGLED:
            fprintf(file, "\"is_paused\":%s,", 
                   event->event_data.pause_event.is_paused ? "true" : "false");
            break;
            
        case EVENT_BREAK_RESCHEDULED:
            fprintf(file, "\"delay_minutes\":%d,", 
                   event->event_data.reschedule_event.delay_minutes);
            break;
            
        case EVENT_COMMAND_RECEIVED:
            // Escape quotes in command text
            fprintf(file, "\"command_text\":\"");
            for (int i = 0; event->event_data.command_event.command_text[i]; i++) {
                char c = event->event_data.command_event.command_text[i];
                if (c == '"' || c == '\\') {
                    fprintf(file, "\\%c", c);
                } else {
                    fprintf(file, "%c", c);
                }
            }
            fprintf(file, "\",");
            break;
            
        default:
            break;
    }
    
    // Remove trailing comma if any event data was written
    long pos = ftell(file);
    if (pos > 0) {
        fseek(file, -1, SEEK_CUR);
        char last_char;
        fread(&last_char, 1, 1, file);
        if (last_char == ',') {
            fseek(file, -1, SEEK_CUR);
        } else {
            fseek(file, 0, SEEK_END);
        }
    }
    
    fprintf(file, "},");
    
    // System state
    fprintf(file, "\"system_state\":{");
    fprintf(file, "\"is_paused\":%s,", 
           event->system_state.is_paused ? "true" : "false");
    fprintf(file, "\"in_deep_work_session\":%s,", 
           event->system_state.in_deep_work_session ? "true" : "false");
    fprintf(file, "\"next_break_in_minutes\":%d,", 
           event->system_state.next_break_in_minutes);
    fprintf(file, "\"total_breaks_today\":%d,", 
           event->system_state.total_breaks_today);
    fprintf(file, "\"total_work_minutes_today\":%d", 
           event->system_state.total_work_minutes_today);
    fprintf(file, "}");
    
    fprintf(file, "}\n");
    fclose(file);
}

// Convenience functions for logging specific events
void log_break_shown(BreakType break_type, int duration_seconds) {
    ActivityEvent event = {0};
    event.timestamp = time(NULL);
    event.event_type = EVENT_BREAK_SHOWN;
    event.event_data.break_event.break_type = break_type;
    event.event_data.break_event.duration_seconds = duration_seconds;
    event.event_data.break_event.user_dismissed = false;
    
    get_current_system_state(&event);
    log_activity_event(&event);
}

void log_break_completed(BreakType break_type, int duration_seconds, bool user_dismissed) {
    ActivityEvent event = {0};
    event.timestamp = time(NULL);
    event.event_type = EVENT_BREAK_COMPLETED;
    event.event_data.break_event.break_type = break_type;
    event.event_data.break_event.duration_seconds = duration_seconds;
    event.event_data.break_event.user_dismissed = user_dismissed;
    
    daily_break_count++;
    get_current_system_state(&event);
    log_activity_event(&event);
}

void log_session_started(SessionType session_type, int duration_minutes) {
    ActivityEvent event = {0};
    event.timestamp = time(NULL);
    event.event_type = EVENT_SESSION_STARTED;
    event.event_data.session_event.session_type = session_type;
    event.event_data.session_event.duration_minutes = duration_minutes;
    
    get_current_system_state(&event);
    log_activity_event(&event);
}

void log_session_ended(SessionType session_type, int actual_duration_minutes) {
    ActivityEvent event = {0};
    event.timestamp = time(NULL);
    event.event_type = EVENT_SESSION_ENDED;
    event.event_data.session_event.session_type = session_type;
    event.event_data.session_event.duration_minutes = actual_duration_minutes;
    
    daily_work_minutes += actual_duration_minutes;
    get_current_system_state(&event);
    log_activity_event(&event);
}

void log_pause_toggled(bool is_paused) {
    ActivityEvent event = {0};
    event.timestamp = time(NULL);
    event.event_type = EVENT_PAUSE_TOGGLED;
    event.event_data.pause_event.is_paused = is_paused;
    
    get_current_system_state(&event);
    log_activity_event(&event);
}

void log_break_rescheduled(int delay_minutes) {
    ActivityEvent event = {0};
    event.timestamp = time(NULL);
    event.event_type = EVENT_BREAK_RESCHEDULED;
    event.event_data.reschedule_event.delay_minutes = delay_minutes;
    
    get_current_system_state(&event);
    log_activity_event(&event);
}

void log_command_received(const char* command_text) {
    ActivityEvent event = {0};
    event.timestamp = time(NULL);
    event.event_type = EVENT_COMMAND_RECEIVED;
    strncpy(event.event_data.command_event.command_text, command_text, 
            sizeof(event.event_data.command_event.command_text) - 1);
    
    get_current_system_state(&event);
    log_activity_event(&event);
}

void log_app_started(void) {
    ActivityEvent event = {0};
    event.timestamp = time(NULL);
    event.event_type = EVENT_APP_STARTED;
    
    get_current_system_state(&event);
    log_activity_event(&event);
}

void log_app_stopped(void) {
    ActivityEvent event = {0};
    event.timestamp = time(NULL);
    event.event_type = EVENT_APP_STOPPED;
    
    get_current_system_state(&event);
    log_activity_event(&event);
}

void cleanup_activity_logging(void) {
    log_app_stopped();
    if (log_file) {
        fclose(log_file);
        log_file = NULL;
    }
}
