#!/usr/bin/env python3
"""
Restly Daily Summary Generator

Analyzes daily activity logs and prepares data for AI-powered insights.
Can send data to an AI API for generating personalized daily summaries.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse


class ActivityAnalyzer:
    def __init__(self, config_dir: Optional[str] = None):
        if config_dir is None:
            self.config_dir = Path.home() / ".config" / "restly"
        else:
            self.config_dir = Path(config_dir)
        
        self.activity_dir = self.config_dir / "activity"
        self.activity_dir.mkdir(parents=True, exist_ok=True)
    
    def get_log_file_path(self, date: datetime) -> Path:
        """Get the path to the activity log file for a specific date."""
        date_str = date.strftime("%Y-%m-%d")
        return self.activity_dir / f"activity_{date_str}.jsonl"
    
    def load_daily_activities(self, date: datetime) -> List[Dict[str, Any]]:
        """Load all activities for a specific date."""
        log_file = self.get_log_file_path(date)
        activities = []
        
        if not log_file.exists():
            return activities
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            activity = json.loads(line)
                            activities.append(activity)
                        except json.JSONDecodeError as e:
                            print(f"Warning: Skipping malformed JSON line: {e}", file=sys.stderr)
        except IOError as e:
            print(f"Error reading log file {log_file}: {e}", file=sys.stderr)
        
        return activities
    
    def analyze_daily_patterns(self, activities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze daily activity patterns and extract insights."""
        if not activities:
            return {
                "total_breaks": 0,
                "total_work_minutes": 0,
                "break_compliance": 0.0,
                "deep_work_sessions": 0,
                "commands_used": 0,
                "pause_events": 0,
                "break_types": {},
                "hourly_activity": {},
                "insights": []
            }
        
        # Initialize counters
        break_count = 0
        break_completed_count = 0
        deep_work_sessions = 0
        commands_used = 0
        pause_events = 0
        break_types = {"eye_care": 0, "custom_message": 0}
        hourly_activity = {}
        reschedule_count = 0
        
        # Get work time from final system state
        final_work_minutes = 0
        if activities:
            last_activity = activities[-1]
            if "system_state" in last_activity:
                final_work_minutes = last_activity["system_state"].get("total_work_minutes_today", 0)
        
        # Process each activity
        for activity in activities:
            timestamp = activity.get("timestamp", "")
            event_type = activity.get("event_type", "")
            event_data = activity.get("event_data", {})
            
            # Extract hour for hourly analysis
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                hour = dt.hour
                hourly_activity[hour] = hourly_activity.get(hour, 0) + 1
            except (ValueError, AttributeError):
                pass
            
            # Count events
            if event_type == "break_shown":
                break_count += 1
                break_type = event_data.get("break_type", "unknown")
                if break_type in break_types:
                    break_types[break_type] += 1
            
            elif event_type == "break_completed":
                break_completed_count += 1
            
            elif event_type == "session_started":
                if event_data.get("session_type") == "deep_work":
                    deep_work_sessions += 1
            
            elif event_type == "command_received":
                commands_used += 1
            
            elif event_type == "pause_toggled":
                pause_events += 1
            
            elif event_type == "break_rescheduled":
                reschedule_count += 1
        
        # Calculate break compliance rate
        break_compliance = (break_completed_count / break_count * 100) if break_count > 0 else 0
        
        # Generate insights
        insights = []
        
        if break_compliance < 50:
            insights.append("Low break compliance detected - consider adjusting break duration or frequency")
        elif break_compliance > 90:
            insights.append("Excellent break compliance! You're taking good care of your eyes")
        
        if deep_work_sessions > 0:
            insights.append(f"Used {deep_work_sessions} deep work session(s) - great for focused productivity")
        
        if reschedule_count > break_count * 0.3:
            insights.append("Frequent break rescheduling detected - consider adjusting default intervals")
        
        if pause_events > 3:
            insights.append("Multiple pause/resume events - consider if current settings match your workflow")
        
        if commands_used > 5:
            insights.append("Active user of voice commands - you're making the most of Restly's features!")
        
        # Analyze work patterns
        peak_hours = sorted(hourly_activity.items(), key=lambda x: x[1], reverse=True)[:3]
        if peak_hours:
            peak_hours_str = ", ".join([f"{h:02d}:00" for h, _ in peak_hours])
            insights.append(f"Most active hours: {peak_hours_str}")
        
        return {
            "total_breaks": break_count,
            "breaks_completed": break_completed_count,
            "total_work_minutes": final_work_minutes,
            "break_compliance": round(break_compliance, 1),
            "deep_work_sessions": deep_work_sessions,
            "commands_used": commands_used,
            "pause_events": pause_events,
            "break_types": break_types,
            "hourly_activity": hourly_activity,
            "reschedule_count": reschedule_count,
            "insights": insights
        }
    
    def generate_daily_summary(self, date: datetime) -> Dict[str, Any]:
        """Generate a comprehensive daily summary."""
        activities = self.load_daily_activities(date)
        analysis = self.analyze_daily_patterns(activities)
        
        # Calculate total active time
        if activities:
            first_activity = min(activities, key=lambda x: x.get("timestamp", ""))
            last_activity = max(activities, key=lambda x: x.get("timestamp", ""))
            
            try:
                start_time = datetime.fromisoformat(first_activity["timestamp"].replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(last_activity["timestamp"].replace('Z', '+00:00'))
                active_duration = (end_time - start_time).total_seconds() / 3600  # hours
            except (ValueError, KeyError):
                active_duration = 0
        else:
            active_duration = 0
        
        summary = {
            "date": date.strftime("%Y-%m-%d"),
            "total_activities": len(activities),
            "active_duration_hours": round(active_duration, 1),
            "analysis": analysis,
            "raw_activities": activities,
            "generated_at": datetime.now().isoformat()
        }
        
        return summary
    
    def prepare_ai_summary_data(self, date: datetime) -> Dict[str, Any]:
        """Prepare data structure optimized for AI analysis and summary generation."""
        summary = self.generate_daily_summary(date)
        
        # Create a condensed version for AI processing
        ai_data = {
            "date": summary["date"],
            "productivity_metrics": {
                "total_work_minutes": summary["analysis"]["total_work_minutes"],
                "break_compliance_rate": summary["analysis"]["break_compliance"],
                "deep_work_sessions": summary["analysis"]["deep_work_sessions"],
                "total_breaks_taken": summary["analysis"]["breaks_completed"],
                "total_breaks_suggested": summary["analysis"]["total_breaks"]
            },
            "behavior_patterns": {
                "commands_used": summary["analysis"]["commands_used"],
                "pause_resume_events": summary["analysis"]["pause_events"],
                "break_reschedules": summary["analysis"]["reschedule_count"],
                "preferred_break_type": max(summary["analysis"]["break_types"].items(), 
                                          key=lambda x: x[1])[0] if summary["analysis"]["break_types"] else "none",
                "peak_activity_hours": list(summary["analysis"]["hourly_activity"].keys())
            },
            "insights": summary["analysis"]["insights"],
            "recommendations_needed": [
                "break_frequency",
                "work_session_optimization", 
                "eye_health_habits",
                "productivity_improvements"
            ]
        }
        
        return ai_data


def save_summary_to_file(summary: Dict[str, Any], output_path: Path):
    """Save summary to a JSON file."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"Summary saved to: {output_path}")
    except IOError as e:
        print(f"Error saving summary: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Generate daily activity summary from Restly logs")
    parser.add_argument("--date", "-d", type=str, help="Date to analyze (YYYY-MM-DD). Default: today")
    parser.add_argument("--output", "-o", type=str, help="Output file path")
    parser.add_argument("--ai-format", "-a", action="store_true", 
                       help="Generate AI-optimized format for summary generation")
    parser.add_argument("--config-dir", "-c", type=str, help="Custom config directory path")
    parser.add_argument("--days", "-n", type=int, default=1, 
                       help="Number of days to analyze (starting from specified date)")
    
    args = parser.parse_args()
    
    # Parse date
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            print("Error: Invalid date format. Use YYYY-MM-DD", file=sys.stderr)
            return 1
    else:
        target_date = datetime.now()
    
    # Initialize analyzer
    analyzer = ActivityAnalyzer(args.config_dir)
    
    # Generate summaries for requested number of days
    summaries = []
    for i in range(args.days):
        current_date = target_date - timedelta(days=i)
        
        if args.ai_format:
            summary = analyzer.prepare_ai_summary_data(current_date)
        else:
            summary = analyzer.generate_daily_summary(current_date)
        
        summaries.append(summary)
    
    # Output results
    if len(summaries) == 1:
        result = summaries[0]
    else:
        result = {
            "multi_day_summary": True,
            "date_range": f"{(target_date - timedelta(days=args.days-1)).strftime('%Y-%m-%d')} to {target_date.strftime('%Y-%m-%d')}",
            "days": summaries
        }
    
    if args.output:
        output_path = Path(args.output)
        save_summary_to_file(result, output_path)
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
