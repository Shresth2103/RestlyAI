#!/usr/bin/env python3
"""
AI-Powered Daily Summary Generator for Restly

Sends activity data to AI APIs (OpenAI, Anthropic, etc.) to generate 
personalized daily summaries and recommendations.
"""

import json
import os
import sys
import asyncio
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import subprocess

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    print("Warning: httpx not installed. Install with: pip install httpx", file=sys.stderr)


class AIConfig:
    """Configuration for AI API integration."""
    
    def __init__(self, config_file: Optional[Path] = None):
        if config_file is None:
            config_file = Path.home() / ".config" / "restly" / "ai_config.json"
        
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load AI configuration from file."""
        default_config = {
            "provider": "gemini",  # openai, anthropic, gemini, local
            "api_key": "",
            "model": "gemini-1.5-flash",
            "base_url": "",  # For local models or custom endpoints
            "max_tokens": 1000,
            "temperature": 0.7,
            "system_prompt": self._get_default_system_prompt()
        }
        
        if not self.config_file.exists():
            self._save_config(default_config)
            return default_config
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Merge with defaults for missing keys
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading AI config: {e}. Using defaults.", file=sys.stderr)
            return default_config
    
    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to file."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving AI config: {e}", file=sys.stderr)
    
    def _get_default_system_prompt(self) -> str:
        """Get the default system prompt for AI summary generation."""
        return """You are a helpful assistant that analyzes computer usage and eye health data from Restly, 
an application that helps users take breaks and care for their eyes while working on computers.

Your task is to:
1. Analyze the provided daily activity data
2. Generate a personalized, encouraging summary of the user's day
3. Provide specific, actionable recommendations for improving eye health and productivity
4. Highlight positive behaviors and suggest gentle improvements for areas that need attention

Keep the tone friendly, supportive, and motivating. Focus on health benefits and productivity improvements.
The summary should be SHORT and concise (50-100 words maximum). Use bullet points and be direct.

Consider factors like:
- Break compliance rate and consistency
- Use of deep work sessions
- Peak activity times
- Break rescheduling patterns
- Overall work-life balance indicators

Format the response as a brief summary with 2-3 bullet points maximum."""
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value and save."""
        self.config[key] = value
        self._save_config(self.config)


class AISummaryGenerator:
    """Generate AI-powered summaries of daily activity."""
    
    def __init__(self, config: AIConfig):
        self.config = config
        
        if not HTTPX_AVAILABLE and self.config.get("provider") not in ["local", None]:
            raise ImportError("httpx is required for API calls. Install with: pip install httpx")
    
    async def generate_summary(self, activity_data: Dict[str, Any]) -> str:
        """Generate an AI summary from activity data."""
        provider = self.config.get("provider", "gemini")
        
        if provider == "openai":
            return await self._generate_openai_summary(activity_data)
        elif provider == "anthropic":
            return await self._generate_anthropic_summary(activity_data)
        elif provider == "gemini":
            return await self._generate_gemini_summary(activity_data)
        elif provider == "local":
            return await self._generate_local_summary(activity_data)
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")
    
    async def _generate_openai_summary(self, activity_data: Dict[str, Any]) -> str:
        """Generate summary using OpenAI API."""
        api_key = self.config.get("api_key")
        if not api_key:
            raise ValueError("OpenAI API key not configured")
        
        model = self.config.get("model", "gpt-4")
        base_url = self.config.get("base_url", "https://api.openai.com/v1")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        messages = [
            {"role": "system", "content": self.config.get("system_prompt")},
            {"role": "user", "content": f"Please analyze this daily activity data and provide a summary:\n\n{json.dumps(activity_data, indent=2)}"}
        ]
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": self.config.get("max_tokens", 1000),
            "temperature": self.config.get("temperature", 0.7)
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
    
    async def _generate_anthropic_summary(self, activity_data: Dict[str, Any]) -> str:
        """Generate summary using Anthropic API."""
        api_key = self.config.get("api_key")
        if not api_key:
            raise ValueError("Anthropic API key not configured")
        
        model = self.config.get("model", "claude-3-sonnet-20240229")
        base_url = self.config.get("base_url", "https://api.anthropic.com")
        
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        user_message = f"{self.config.get('system_prompt')}\n\nPlease analyze this daily activity data and provide a summary:\n\n{json.dumps(activity_data, indent=2)}"
        
        payload = {
            "model": model,
            "max_tokens": self.config.get("max_tokens", 1000),
            "temperature": self.config.get("temperature", 0.7),
            "messages": [
                {"role": "user", "content": user_message}
            ]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/v1/messages",
                headers=headers,
                json=payload,
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise Exception(f"Anthropic API error: {response.status_code} - {response.text}")
            
            result = response.json()
            return result["content"][0]["text"]
    
    async def _generate_gemini_summary(self, activity_data: Dict[str, Any]) -> str:
        """Generate summary using Google Gemini API."""
        api_key = self.config.get("api_key")
        if not api_key:
            raise ValueError("Google Gemini API key not configured")
        
        model = self.config.get("model", "gemini-1.5-flash")
        base_url = self.config.get("base_url", "https://generativelanguage.googleapis.com")
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Prepare the prompt
        system_prompt = self.config.get("system_prompt")
        user_message = f"{system_prompt}\n\nPlease analyze this daily activity data and provide a summary:\n\n{json.dumps(activity_data, indent=2)}"
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": user_message
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": self.config.get("temperature", 0.7),
                "maxOutputTokens": self.config.get("max_tokens", 1000),
                "topP": 0.8,
                "topK": 10
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/v1beta/models/{model}:generateContent?key={api_key}",
                headers=headers,
                json=payload,
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise Exception(f"Gemini API error: {response.status_code} - {response.text}")
            
            result = response.json()
            
            if "candidates" not in result or not result["candidates"]:
                raise Exception("No response generated from Gemini API")
            
            return result["candidates"][0]["content"]["parts"][0]["text"]
    
    async def _generate_local_summary(self, activity_data: Dict[str, Any]) -> str:
        """Generate summary using local model (placeholder for future implementation)."""
        # This is a placeholder for local model integration
        # You could integrate with ollama, llamacpp, or other local inference engines
        
        # Simple template-based summary for now
        metrics = activity_data.get("productivity_metrics", {})
        patterns = activity_data.get("behavior_patterns", {})
        insights = activity_data.get("insights", [])
        
        work_minutes = metrics.get("total_work_minutes", 0)
        break_compliance = metrics.get("break_compliance_rate", 0)
        deep_work_sessions = metrics.get("deep_work_sessions", 0)
        
        summary = f"""# Daily Summary for {activity_data.get('date', 'today')}

## Overview
Today you worked for {work_minutes} minutes with a {break_compliance}% break compliance rate. 
{f"You completed {deep_work_sessions} deep work session(s) - great for focused productivity!" if deep_work_sessions > 0 else "Consider using deep work sessions for better focus."}

## Key Insights
"""
        for insight in insights[:3]:  # Top 3 insights
            summary += f"- {insight}\n"
        
        summary += f"""
## Recommendations
- {"Excellent break compliance! Keep it up!" if break_compliance > 80 else "Try to improve break compliance for better eye health"}
- {"You're making good use of Restly's features" if patterns.get("commands_used", 0) > 2 else "Explore Restly's voice commands for easier control"}
- Take regular 20-second breaks to look at something 20 feet away (20-20-20 rule)

*This summary was generated locally. For more detailed AI analysis, configure an API key.*
"""
        
        return summary


async def generate_ai_summary_for_date(date: datetime, config_dir: Optional[str] = None) -> str:
    """Generate AI summary for a specific date."""
    # Import daily_summary here to avoid circular imports
    from daily_summary import ActivityAnalyzer
    
    # Generate activity data
    analyzer = ActivityAnalyzer(config_dir)
    activity_data = analyzer.prepare_ai_summary_data(date)
    
    # Generate AI summary
    ai_config = AIConfig()
    generator = AISummaryGenerator(ai_config)
    
    summary = await generator.generate_summary(activity_data)
    return summary


def setup_ai_config():
    """Interactive setup for AI configuration."""
    print("Setting up AI integration for Restly...")
    print("\nSupported providers:")
    print("1. OpenAI (GPT-4, GPT-3.5)")
    print("2. Anthropic (Claude)")
    print("3. Google Gemini (Gemini 1.5)")
    print("4. Local (template-based, no API key needed)")
    
    provider_map = {"1": "openai", "2": "anthropic", "3": "gemini", "4": "local"}
    provider_choice = input("\nSelect provider (1-4): ").strip()
    provider = provider_map.get(provider_choice, "local")
    
    config = AIConfig()
    config.set("provider", provider)
    
    if provider != "local":
        api_key = input(f"Enter your {provider.title()} API key: ").strip()
        config.set("api_key", api_key)
        
        if provider == "openai":
            model = input("Model (default: gpt-4): ").strip() or "gpt-4"
        elif provider == "gemini":
            model = input("Model (default: gemini-1.5-flash): ").strip() or "gemini-1.5-flash"
        else:
            model = input("Model (default: claude-3-sonnet-20240229): ").strip() or "claude-3-sonnet-20240229"
        
        config.set("model", model)
    
    print(f"\nAI configuration saved! Provider: {provider}")
    print("You can now generate AI-powered daily summaries.")


async def main():
    parser = argparse.ArgumentParser(description="Generate AI-powered daily summaries from Restly activity data")
    parser.add_argument("--date", "-d", type=str, help="Date to analyze (YYYY-MM-DD). Default: today")
    parser.add_argument("--config-dir", "-c", type=str, help="Custom config directory path")
    parser.add_argument("--setup", "-s", action="store_true", help="Setup AI configuration")
    parser.add_argument("--output", "-o", type=str, help="Output file path")
    
    args = parser.parse_args()
    
    if args.setup:
        setup_ai_config()
        return 0
    
    # Parse date
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            print("Error: Invalid date format. Use YYYY-MM-DD", file=sys.stderr)
            return 1
    else:
        target_date = datetime.now()
    
    try:
        summary = await generate_ai_summary_for_date(target_date, args.config_dir)
        
        if args.output:
            output_path = Path(args.output)
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(summary)
                print(f"AI summary saved to: {output_path}")
            except IOError as e:
                print(f"Error saving summary: {e}", file=sys.stderr)
        else:
            print(summary)
    
    except Exception as e:
        print(f"Error generating AI summary: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
