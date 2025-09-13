#!/usr/bin/env python3
"""
Simple script to configure Gemini API key for Restly AI summaries
"""

import json
import os
import sys
from pathlib import Path

def setup_gemini_api_key():
    """Set up Gemini API key for Restly AI summaries."""
    config_dir = Path.home() / ".config" / "restly"
    config_file = config_dir / "ai_config.json"
    
    # Create config directory if it doesn't exist
    config_dir.mkdir(parents=True, exist_ok=True)
    
    print("Setting up Google Gemini API for Restly AI summaries...")
    print("\nTo get your Gemini API key:")
    print("1. Go to https://makersuite.google.com/app/apikey")
    print("2. Create a new API key")
    print("3. Copy the API key")
    
    api_key = input("\nEnter your Gemini API key: ").strip()
    
    if not api_key:
        print("No API key provided. Exiting.")
        return False
    
    # Create or update config
    config = {
        "provider": "gemini",
        "api_key": api_key,
        "model": "gemini-1.5-flash",
        "base_url": "",
        "max_tokens": 1000,
        "temperature": 0.7,
        "system_prompt": """You are a helpful assistant that analyzes computer usage and eye health data from Restly, 
an application that helps users take breaks and care for their eyes while working on computers.

Your task is to:
1. Analyze the provided daily activity data
2. Generate a personalized, encouraging summary of the user's day
3. Provide specific, actionable recommendations for improving eye health and productivity
4. Highlight positive behaviors and suggest gentle improvements for areas that need attention

Keep the tone friendly, supportive, and motivating. Focus on health benefits and productivity improvements.
The summary should be concise but informative (200-400 words).

Consider factors like:
- Break compliance rate and consistency
- Use of deep work sessions
- Peak activity times
- Break rescheduling patterns
- Overall work-life balance indicators

Format the response in markdown with clear sections for Summary, Insights, and Recommendations."""
    }
    
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        # Set secure file permissions (readable only by owner)
        os.chmod(config_file, 0o600)
        
        print(f"\n✅ Gemini API key configured successfully!")
        print(f"Configuration saved to: {config_file}")
        print("🔒 File permissions set to secure (readable only by you)")
        print("\nYou can now generate AI-powered daily summaries with:")
        print("  python3 ai_summary.py --date YYYY-MM-DD")
        print("\nOr generate a summary for today:")
        print("  python3 ai_summary.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving configuration: {e}")
        return False

if __name__ == "__main__":
    success = setup_gemini_api_key()
    sys.exit(0 if success else 1)
