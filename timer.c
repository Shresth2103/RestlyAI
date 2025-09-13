#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <time.h>
#include <string.h>
#include <unistd.h>
#include <ctype.h>
#include "timer.h"
#include "config.h"
#include "popup.h"
#include "command_queue.h"
#include "activity_log.h"

// Global state for the timer (exposed for activity logging)
bool is_paused = false;
time_t next_break_time = 0;
bool in_deep_work_session = false;
static time_t session_end_time = 0;
static time_t deep_work_start_time = 0;

void start_timer(AppConfig config)
{
    // Initialize activity logging
    init_activity_logging();
    
    time_t ctime = time(NULL);
    struct tm *lt = localtime(&ctime);
    int inter_sec = config.interval_minutes * 60;
    int s_hour, e_hour, s_min, e_min;
    sscanf(config.start_time, "%2d:%2d", &s_hour, &s_min);
    sscanf(config.end_time, "%2d:%2d", &e_hour, &e_min);
    
    // Initialize next break time
    next_break_time = time(NULL) + inter_sec;

    while (true)
    {   
        // Check for commands from controller every 5 seconds
        process_command_queue();
        
        time_t current_time = time(NULL);
        struct tm *lt = localtime(&current_time);
        int c_hour = lt->tm_hour;
        int c_min = lt->tm_min;
        
        int start_min = s_hour * 60 + s_min;
        int end_min = e_hour * 60 + e_min;
        int cur_min = c_hour * 60 + c_min;

        bool active = false;
        
        if (start_min < end_min) {
            active = (cur_min >= start_min && cur_min <= end_min);
        } else {
            active = (cur_min >= start_min || cur_min <= end_min);
        }
        
        // Check if we're in active hours and not paused
        if (active && !is_paused) {
            // Check if deep work session has ended
            if (in_deep_work_session && current_time >= session_end_time) {
                show_popup("Deep work session complete! Great job! 🎉", 5);
                
                // Log session completion
                int actual_duration = (current_time - deep_work_start_time) / 60;
                log_session_ended(SESSION_TYPE_DEEP_WORK, actual_duration);
                
                in_deep_work_session = false;
                // Reset normal break timer
                next_break_time = current_time + inter_sec;
            }
            
            // Only show regular breaks if not in deep work session
            if (!in_deep_work_session && current_time >= next_break_time) {
                if (config.eye_care == 0) {
                    log_break_shown(BREAK_TYPE_CUSTOM_MESSAGE, 5);
                    show_popup(config.message, 5);
                    log_break_completed(BREAK_TYPE_CUSTOM_MESSAGE, 5, false);
                } else if (config.eye_care == 1) {
                    // Log eye care break sequence
                    int total_duration = 3+3+6+21+3+3+3+3+2; // Total eye care routine duration
                    log_break_shown(BREAK_TYPE_EYE_CARE, total_duration);
                    
                    show_popup("Break Time ദ്ദി( • ᗜ - ) ✧", 3);
                    sleep(3);
                    show_popup("Let's unwind your eyes \n and neck (˶ᵔ ᵕ ᵔ˶)", 3);
                    sleep(3);
                    show_popup("Close your eyes for 5 sec \n and roll them (˶ᵔ ᵕ ᵔ˶)", 6);
                    sleep(6);
                    show_popup("Look at smth far away \n for 20 sec (˶ᵔ ᵕ ᵔ˶)", 21);
                    sleep(21);
                    show_popup("Stretch your neck to the left (˶ᵔ ᵕ ᵔ˶)", 3);
                    sleep(3);
                    show_popup("Now to the right (˶ᵔ ᵕ ᵔ˶)", 3);
                    sleep(3);
                    show_popup("Now look up for 3 sec (˶ᵔ ᵕ ᵔ˶)", 3);
                    sleep(3);
                    show_popup("Now look down for 3 sec (˶ᵔ ᵕ ᵔ˶)", 3);
                    sleep(3);
                    show_popup("Good job! wait for me again!ദ്ദി(˵ •̀ ᴗ - ˵ ) ✧", 2);
                    
                    log_break_completed(BREAK_TYPE_EYE_CARE, total_duration, false);
                }
                
                // Set next break time
                next_break_time = current_time + inter_sec;
            }
        }
        
        // Sleep for 5 seconds before checking again
        sleep(5);
    }
    
    // Clean up activity logging on exit
    cleanup_activity_logging();
}

// Command execution functions
void set_deep_work_session(int duration_minutes) {
    time_t current_time = time(NULL);
    session_end_time = current_time + (duration_minutes * 60);
    deep_work_start_time = current_time;
    in_deep_work_session = true;
    
    // Log session start
    log_session_started(SESSION_TYPE_DEEP_WORK, duration_minutes);
    
    char message[256];
    char time_str[64];
    strftime(time_str, sizeof(time_str), "%H:%M", localtime(&session_end_time));
    snprintf(message, sizeof(message), "Starting %d-minute deep work session! 🎯\nBreaks paused until %s", 
             duration_minutes, time_str);
    show_popup(message, 5);
}

void toggle_pause_resume() {
    is_paused = !is_paused;
    
    // Log pause state change
    log_pause_toggled(is_paused);
    
    if (is_paused) {
        show_popup("Restly paused ⏸️\nBreaks disabled until resumed", 3);
    } else {
        show_popup("Restly resumed ▶️\nBreaks re-enabled", 3);
        // Reset break timer when resuming
        time_t current_time = time(NULL);
        next_break_time = current_time + (20 * 60); // Default 20 min interval
    }
}

void reschedule_next_break(int delay_minutes) {
    next_break_time += (delay_minutes * 60);
    
    // Log break reschedule
    log_break_rescheduled(delay_minutes);
    
    char message[128];
    snprintf(message, sizeof(message), "Break rescheduled by %d minutes ⏰", delay_minutes);
    show_popup(message, 3);
}

// Keyword-based natural language command parser
void parse_natural_language_command(const char* text) {
    if (!text || strlen(text) == 0) {
        show_popup("Empty command received", 2);
        return;
    }
    
    // Log the command received
    log_command_received(text);
    
    
    // Convert to lowercase for case-insensitive matching
    char lower_text[256];
    strncpy(lower_text, text, sizeof(lower_text) - 1);
    lower_text[sizeof(lower_text) - 1] = '\0';
    
    // Convert to lowercase
    for (int i = 0; lower_text[i]; i++) {
        lower_text[i] = tolower(lower_text[i]);
    }
    
    // Keyword matching patterns
    if (strstr(lower_text, "reschedule") || strstr(lower_text, "delay") || strstr(lower_text, "postpone")) {
        // Extract time duration
        int delay_minutes = 15; // default
        
        // Look for numbers followed by time units
        char* num_start = NULL;
        for (int i = 0; lower_text[i]; i++) {
            if (isdigit(lower_text[i])) {
                num_start = &lower_text[i];
                break;
            }
        }
        
        if (num_start) {
            int num = atoi(num_start);
            
            // Check for time units
            if (strstr(num_start, "minute") || strstr(num_start, "min")) {
                delay_minutes = num;
            } else if (strstr(num_start, "hour") || strstr(num_start, "hr")) {
                delay_minutes = num * 60;
            } else if (strstr(num_start, "second") || strstr(num_start, "sec")) {
                delay_minutes = (num + 59) / 60; // Round up to nearest minute
            } else {
                // Assume minutes if no unit specified
                delay_minutes = num;
            }
        }
        
        reschedule_next_break(delay_minutes);
        char message[128];
        snprintf(message, sizeof(message), "Break rescheduled by %d minutes ⏰", delay_minutes);
        show_popup(message, 3);
    }
    else if (strstr(lower_text, "pause") || strstr(lower_text, "stop")) {
        toggle_pause_resume();
    }
    else if (strstr(lower_text, "resume") || strstr(lower_text, "start") || strstr(lower_text, "continue")) {
        if (is_paused) {
            toggle_pause_resume();
        } else {
            show_popup("Restly is already running ▶️", 2);
        }
    }
    else if (strstr(lower_text, "deep work") || strstr(lower_text, "focus") || strstr(lower_text, "session")) {
        // Extract duration for deep work session
        int duration_minutes = 45; // default
        
        char* num_start = NULL;
        for (int i = 0; lower_text[i]; i++) {
            if (isdigit(lower_text[i])) {
                num_start = &lower_text[i];
                break;
            }
        }
        
        if (num_start) {
            int num = atoi(num_start);
            
            if (strstr(num_start, "minute") || strstr(num_start, "min")) {
                duration_minutes = num;
            } else if (strstr(num_start, "hour") || strstr(num_start, "hr")) {
                duration_minutes = num * 60;
            } else {
                duration_minutes = num;
            }
        }
        
        set_deep_work_session(duration_minutes);
    }
    else if (strstr(lower_text, "break") && strstr(lower_text, "now")) {
        // Force immediate break
        next_break_time = time(NULL);
        show_popup("Taking break now! 🎯", 3);
    }
    else if (strstr(lower_text, "status") || strstr(lower_text, "how") || strstr(lower_text, "what")) {
        // Show current status
        char status_msg[200];
        time_t current_time = time(NULL);
        int minutes_until_break = (next_break_time - current_time) / 60;
        
        if (is_paused) {
            snprintf(status_msg, sizeof(status_msg), "Restly is paused ⏸️\nResume to restart breaks");
        } else if (in_deep_work_session) {
            int minutes_left = (session_end_time - current_time) / 60;
            snprintf(status_msg, sizeof(status_msg), "Deep work session active 🎯\n%d minutes remaining", minutes_left);
        } else {
            snprintf(status_msg, sizeof(status_msg), "Next break in %d minutes ⏰", minutes_until_break);
        }
        
        show_popup(status_msg, 4);
    }
    else {
        // Unknown command - show help
        char help_msg[400];
        snprintf(help_msg, sizeof(help_msg), 
                "Unknown command: %s\n\nTry these keywords:\n"
                "• 'reschedule break' or 'delay 30 minutes'\n"
                "• 'pause' or 'stop'\n"
                "• 'resume' or 'start'\n"
                "• 'deep work 45 minutes'\n"
                "• 'break now'\n"
                "• 'status'", text);
        show_popup(help_msg, 6);
    }
}

// Update execute_command implementation
void execute_command(CommandAction* action) {
    switch (action->type) {
        case CMD_SET_SESSION:
            set_deep_work_session(action->params.session.duration_minutes);
            break;
            
        case CMD_TOGGLE_PAUSE:
            toggle_pause_resume();
            break;
            
        case CMD_RESCHEDULE_BREAK:
            reschedule_next_break(action->params.reschedule.delay_minutes);
            break;
            
        case CMD_SUMMARIZE_DAY:
            show_popup("Day summary feature coming soon! 📊", 3);
            // TODO: Call AI summary script
            break;
            
        case CMD_NL_COMMAND:
            // Parse natural language command using keywords
            parse_natural_language_command(action->params.nl_command.text);
            break;
            
        case CMD_UNKNOWN:
        default:
            break;
    }
}