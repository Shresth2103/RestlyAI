#ifndef ACTIVITY_LOG_H
#define ACTIVITY_LOG_H

#include <stdbool.h>
#include <time.h>

// Event types for activity logging
typedef enum {
    EVENT_BREAK_SHOWN,
    EVENT_BREAK_COMPLETED,
    EVENT_SESSION_STARTED,
    EVENT_SESSION_ENDED,
    EVENT_PAUSE_TOGGLED,
    EVENT_BREAK_RESCHEDULED,
    EVENT_COMMAND_RECEIVED,
    EVENT_APP_STARTED,
    EVENT_APP_STOPPED
} ActivityEventType;

// Break types
typedef enum {
    BREAK_TYPE_EYE_CARE,
    BREAK_TYPE_CUSTOM_MESSAGE
} BreakType;

// Session types
typedef enum {
    SESSION_TYPE_DEEP_WORK,
    SESSION_TYPE_REGULAR
} SessionType;

// Activity event structure
typedef struct {
    time_t timestamp;
    ActivityEventType event_type;
    
    // Event-specific data
    union {
        struct {
            BreakType break_type;
            int duration_seconds;
            bool user_dismissed;
        } break_event;
        
        struct {
            SessionType session_type;
            int duration_minutes;
        } session_event;
        
        struct {
            bool is_paused;
        } pause_event;
        
        struct {
            int delay_minutes;
        } reschedule_event;
        
        struct {
            char command_text[256];
        } command_event;
    } event_data;
    
    // System state at time of event
    struct {
        bool is_paused;
        bool in_deep_work_session;
        int next_break_in_minutes;
        int total_breaks_today;
        int total_work_minutes_today;
    } system_state;
} ActivityEvent;

// Function declarations
void init_activity_logging(void);
void log_activity_event(ActivityEvent* event);
void log_break_shown(BreakType break_type, int duration_seconds);
void log_break_completed(BreakType break_type, int duration_seconds, bool user_dismissed);
void log_session_started(SessionType session_type, int duration_minutes);
void log_session_ended(SessionType session_type, int actual_duration_minutes);
void log_pause_toggled(bool is_paused);
void log_break_rescheduled(int delay_minutes);
void log_command_received(const char* command_text);
void log_app_started(void);
void log_app_stopped(void);
void cleanup_activity_logging(void);

// Utility functions
const char* get_activity_log_path(void);
void get_current_system_state(ActivityEvent* event);

#endif
