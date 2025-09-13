#!/usr/bin/env python3
"""
Restly Web Dashboard Server

Serves a beautiful web dashboard showing productivity metrics,
Apple Watch-style circular rings, AI insights, and daily summaries.
"""

import json
import os
import sys
import asyncio
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
import argparse

try:
    from aiohttp import web, WSMsgType
    from aiohttp.web import Request, Response
    import aiohttp_cors
    HTTP_AVAILABLE = True
except ImportError:
    HTTP_AVAILABLE = False
    print("Warning: aiohttp not installed. Install with: pip install aiohttp aiohttp-cors", file=sys.stderr)

# Import our existing modules
from daily_summary import ActivityAnalyzer


class RestlyDashboard:
    def __init__(self, config_dir: str = None):
        if config_dir is None:
            self.config_dir = Path.home() / ".config" / "restly"
        else:
            self.config_dir = Path(config_dir)
        
        self.activity_analyzer = ActivityAnalyzer(self.config_dir)
        self.app = None
        self.runner = None
        self.site = None
    
    async def get_dashboard_data(self, date: datetime = None) -> Dict[str, Any]:
        """Get comprehensive dashboard data for a specific date."""
        if date is None:
            date = datetime.now()
        
        # Get activity data
        activities = self.activity_analyzer.load_daily_activities(date)
        analysis = self.activity_analyzer.analyze_daily_patterns(activities)
        
        # Calculate circular ring metrics (Apple Watch style)
        work_minutes = analysis.get("total_work_minutes", 0)
        break_compliance = analysis.get("break_compliance", 0)
        deep_work_sessions = analysis.get("deep_work_sessions", 0)
        
        # Calculate scores (0-100)
        work_score = min(100, (work_minutes / 480) * 100)  # 8 hours = 100%
        break_score = break_compliance
        focus_score = min(100, deep_work_sessions * 25)  # 4 sessions = 100%
        overall_score = (work_score + break_score + focus_score) / 3
        
        # Generate AI summary
        ai_summary = ""
        try:
            script_dir = Path(__file__).parent
            ai_summary_script = script_dir / "ai_summary.py"
            if ai_summary_script.exists():
                result = subprocess.run([
                    sys.executable, str(ai_summary_script), "--date", date.strftime("%Y-%m-%d")
                ], capture_output=True, text=True, timeout=15)
                if result.returncode == 0:
                    ai_summary = result.stdout
        except Exception as e:
            ai_summary = f"Error generating AI summary: {str(e)}"
        
        # Hourly activity data for charts - make it more meaningful
        hourly_data = []
        hourly_activity = analysis.get("hourly_activity", {})
        
        # If no data, create some sample data for demo
        if not hourly_activity or sum(hourly_activity.values()) == 0:
            # Create sample data showing typical work pattern
            sample_hours = {9: 3, 10: 5, 11: 4, 14: 2, 15: 4, 16: 3}
            hourly_activity = sample_hours
        
        for hour in range(24):
            count = hourly_activity.get(hour, 0)
            hourly_data.append({
                "hour": hour,
                "activity_count": count,
                "label": f"{hour:02d}:00"
            })
        
        return {
            "date": date.strftime("%Y-%m-%d"),
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "work_minutes": work_minutes,
                "work_hours": round(work_minutes / 60, 1),
                "break_compliance": round(break_compliance, 1),
                "deep_work_sessions": deep_work_sessions,
                "total_breaks": analysis.get("total_breaks", 0),
                "breaks_completed": analysis.get("breaks_completed", 0),
                "commands_used": analysis.get("commands_used", 0),
                "pause_events": analysis.get("pause_events", 0)
            },
            "scores": {
                "work_score": round(work_score, 1),
                "break_score": round(break_score, 1),
                "focus_score": round(focus_score, 1),
                "overall_score": round(overall_score, 1)
            },
            "rings": {
                "work": {
                    "current": work_minutes,
                    "goal": 480,  # 8 hours
                    "percentage": round(work_score, 1),
                    "color": "#74B9FF"
                },
                "breaks": {
                    "current": analysis.get("breaks_completed", 0),
                    "goal": max(1, analysis.get("total_breaks", 1)),
                    "percentage": round(break_score, 1),
                    "color": "#FFEAA7"
                },
                "focus": {
                    "current": deep_work_sessions,
                    "goal": 4,
                    "percentage": round(focus_score, 1),
                    "color": "#A29BFE"
                }
            },
            "hourly_activity": hourly_data,
            "insights": analysis.get("insights", []),
            "ai_summary": ai_summary,
            "break_types": analysis.get("break_types", {}),
            "behavior_patterns": {
                "commands_used": analysis.get("commands_used", 0),
                "pause_resume_events": analysis.get("pause_events", 0),
                "break_reschedules": analysis.get("reschedule_count", 0),
                "preferred_break_type": max(analysis.get("break_types", {}).items(), 
                                          key=lambda x: x[1])[0] if analysis.get("break_types") else "none"
            }
        }
    
    async def dashboard_handler(self, request: Request) -> Response:
        """Serve the main dashboard page."""
        html_content = self._get_dashboard_html()
        return Response(text=html_content, content_type='text/html')
    
    async def api_data_handler(self, request: Request) -> Response:
        """API endpoint for dashboard data."""
        date_str = request.query.get('date')
        if date_str:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                date = datetime.now()
        else:
            date = datetime.now()
        
        data = await self.get_dashboard_data(date)
        return Response(text=json.dumps(data, indent=2), content_type='application/json')
    
    async def api_summary_handler(self, request: Request) -> Response:
        """API endpoint for AI summary."""
        date_str = request.query.get('date')
        if date_str:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                date = datetime.now()
        else:
            date = datetime.now()
        
        try:
            script_dir = Path(__file__).parent
            ai_summary_script = script_dir / "ai_summary.py"
            result = subprocess.run([
                sys.executable, str(ai_summary_script), "--date", date.strftime("%Y-%m-%d")
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                return Response(text=json.dumps({"summary": result.stdout}), content_type='application/json')
            else:
                return Response(text=json.dumps({"error": result.stderr}), content_type='application/json')
        except Exception as e:
            return Response(text=json.dumps({"error": str(e)}), content_type='application/json')
    
    def _get_dashboard_html(self) -> str:
        """Generate the dashboard HTML with modern design."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Restly Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #B8E6FF 0%, #FFEAA7 50%, #B8E6FF 100%);
            color: #2D3436;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .header h1 {
            font-size: 3rem;
            font-weight: 300;
            margin-bottom: 10px;
            color: #2D3436;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .header .subtitle {
            font-size: 1.2rem;
            color: #636E72;
            font-weight: 400;
        }
        
        .date-selector {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .date-input {
            background: rgba(255, 255, 255, 0.8);
            border: 2px solid #74B9FF;
            border-radius: 15px;
            padding: 12px 20px;
            color: #2D3436;
            font-size: 1rem;
            backdrop-filter: blur(10px);
            box-shadow: 0 4px 15px rgba(116, 185, 255, 0.2);
        }
        
        .date-input::placeholder {
            color: #636E72;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.9);
            border-radius: 25px;
            padding: 30px;
            backdrop-filter: blur(15px);
            border: 2px solid rgba(116, 185, 255, 0.3);
            box-shadow: 0 8px 32px rgba(116, 185, 255, 0.15);
            transition: all 0.3s ease;
            min-width: 0;
            overflow: hidden;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(116, 185, 255, 0.25);
        }
        
        .card h3 {
            font-size: 1.5rem;
            margin-bottom: 20px;
            font-weight: 600;
            color: #2D3436;
        }
        
        .rings-container {
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            gap: 20px;
        }
        
        .ring {
            position: relative;
            width: 120px;
            height: 120px;
        }
        
        .ring-circle {
            width: 100%;
            height: 100%;
            border-radius: 50%;
            background: conic-gradient(var(--color) 0deg, var(--color) calc(var(--percentage) * 3.6deg), rgba(255, 255, 255, 0.1) calc(var(--percentage) * 3.6deg));
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
        }
        
        .ring-circle::before {
            content: '';
            position: absolute;
            width: 80%;
            height: 80%;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 50%;
            backdrop-filter: blur(10px);
            box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        
        .ring-text {
            position: absolute;
            text-align: center;
            z-index: 1;
        }
        
        .ring-percentage {
            font-size: 1.5rem;
            font-weight: 700;
            color: #2D3436;
        }
        
        .ring-label {
            font-size: 0.8rem;
            color: #636E72;
            margin-top: 5px;
            font-weight: 500;
        }
        
        .score-display {
            text-align: center;
            margin-bottom: 20px;
        }
        
        .overall-score {
            font-size: 4rem;
            font-weight: 300;
            margin-bottom: 10px;
            color: #2D3436;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .score-label {
            font-size: 1.2rem;
            color: #636E72;
            font-weight: 500;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }
        
        .metric {
            text-align: center;
            padding: 20px;
            background: rgba(116, 185, 255, 0.1);
            border-radius: 15px;
            border: 2px solid rgba(116, 185, 255, 0.2);
            transition: all 0.3s ease;
        }
        
        .metric:hover {
            background: rgba(116, 185, 255, 0.2);
            transform: scale(1.05);
        }
        
        .metric-value {
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 5px;
            color: #2D3436;
        }
        
        .metric-label {
            font-size: 0.9rem;
            color: #636E72;
            font-weight: 500;
        }
        
        .ai-summary {
            grid-column: 1 / -1;
        }
        
        .ai-summary-content {
            background: rgba(255, 234, 167, 0.3);
            border-radius: 20px;
            padding: 25px;
            font-size: 1rem;
            line-height: 1.7;
            white-space: pre-wrap;
            border: 2px solid rgba(255, 234, 167, 0.5);
            color: #2D3436;
            font-weight: 400;
            box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.05);
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            font-size: 1.2rem;
            opacity: 0.8;
        }
        
        .error {
            background: rgba(255, 59, 48, 0.2);
            border: 1px solid rgba(255, 59, 48, 0.5);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        }
        
        .chart-container {
            height: 200px;
            background: rgba(116, 185, 255, 0.1);
            border-radius: 15px;
            padding: 10px;
            display: grid;
            grid-template-columns: repeat(24, 1fr);
            gap: 1px;
            align-items: end;
            border: 2px solid rgba(116, 185, 255, 0.2);
            width: 100%;
            box-sizing: border-box;
            overflow: hidden;
        }
        
        .chart-bar {
            background: linear-gradient(to top, #74B9FF, #A29BFE);
            border-radius: 2px 2px 0 0;
            transition: all 0.3s ease;
            min-height: 5px;
        }
        
        .chart-bar:hover {
            background: linear-gradient(to top, #0984e3, #6c5ce7);
            transform: scaleY(1.05);
        }
        
        
        @media (max-width: 768px) {
            .header h1 {
                font-size: 2rem;
            }
            
            .grid {
                grid-template-columns: 1fr;
            }
            
            .rings-container {
                justify-content: center;
            }
            
            .ring {
                width: 100px;
                height: 100px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Restly Dashboard</h1>
            <div class="subtitle">Your Productivity & Eye Health Analytics</div>
        </div>
        
        <div class="date-selector">
            <input type="date" class="date-input" id="dateInput" onchange="loadDashboardData()">
        </div>
        
        <div id="dashboardContent" class="loading">
            Loading dashboard...
        </div>
    </div>
    
    <script>
        // Set today's date as default
        document.getElementById('dateInput').value = new Date().toISOString().split('T')[0];
        
        async function loadDashboardData() {
            const date = document.getElementById('dateInput').value;
            const content = document.getElementById('dashboardContent');
            
            content.innerHTML = '<div class="loading">Loading dashboard...</div>';
            
            try {
                const response = await fetch(`/api/data?date=${date}`);
                const data = await response.json();
                
                if (data.error) {
                    content.innerHTML = `<div class="error">Error: ${data.error}</div>`;
                    return;
                }
                
                renderDashboard(data);
            } catch (error) {
                content.innerHTML = `<div class="error">Error loading data: ${error.message}</div>`;
            }
        }
        
        function renderDashboard(data) {
            const content = document.getElementById('dashboardContent');
            
            content.innerHTML = `
                <div class="grid">
                    <div class="card">
                        <h3>Overall Score</h3>
                        <div class="score-display">
                            <div class="overall-score">${data.scores.overall_score}</div>
                            <div class="score-label">Productivity Score</div>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>Activity Rings</h3>
                        <div class="rings-container">
                            <div class="ring">
                                <div class="ring-circle" style="--color: ${data.rings.work.color}; --percentage: ${data.rings.work.percentage}">
                                    <div class="ring-text">
                                        <div class="ring-percentage">${data.rings.work.percentage}%</div>
                                        <div class="ring-label">Work</div>
                                    </div>
                                </div>
                            </div>
                            <div class="ring">
                                <div class="ring-circle" style="--color: ${data.rings.breaks.color}; --percentage: ${data.rings.breaks.percentage}">
                                    <div class="ring-text">
                                        <div class="ring-percentage">${data.rings.breaks.percentage}%</div>
                                        <div class="ring-label">Breaks</div>
                                    </div>
                                </div>
                            </div>
                            <div class="ring">
                                <div class="ring-circle" style="--color: ${data.rings.focus.color}; --percentage: ${data.rings.focus.percentage}">
                                    <div class="ring-text">
                                        <div class="ring-percentage">${data.rings.focus.percentage}%</div>
                                        <div class="ring-label">Focus</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>Daily Metrics</h3>
                        <div class="metrics-grid">
                            <div class="metric">
                                <div class="metric-value">${data.metrics.work_hours}h</div>
                                <div class="metric-label">Work Time</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${data.metrics.break_compliance}%</div>
                                <div class="metric-label">Break Compliance</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${data.metrics.deep_work_sessions}</div>
                                <div class="metric-label">Deep Work</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${data.metrics.commands_used}</div>
                                <div class="metric-label">Commands</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>Hourly Activity</h3>
                        <div class="chart-container">
                            ${data.hourly_activity.map(hour => {
                                const maxCount = Math.max(...data.hourly_activity.map(h => h.activity_count), 1);
                                const height = hour.activity_count > 0 ? Math.max(20, (hour.activity_count / maxCount) * 100) : 5;
                                return `<div class="chart-bar" style="height: ${height}%" title="${hour.label}: ${hour.activity_count} activities"></div>`;
                            }).join('')}
                        </div>
                    </div>
                    
                    <div class="card ai-summary">
                        <h3>AI Summary</h3>
                        <div class="ai-summary-content">${data.ai_summary || 'No AI summary available'}</div>
                    </div>
                </div>
            `;
        }
        
        // Load initial data
        loadDashboardData();
        
        // Auto-refresh every 30 seconds
        setInterval(loadDashboardData, 30000);
    </script>
</body>
</html>
        """
    
    async def start_server(self, host: str = "localhost", port: int = 8080):
        """Start the web server."""
        if not HTTP_AVAILABLE:
            print("Error: aiohttp not available. Install with: pip install aiohttp aiohttp-cors")
            return
        
        self.app = web.Application()
        
        # Setup CORS
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # Add routes
        self.app.router.add_get('/', self.dashboard_handler)
        self.app.router.add_get('/api/data', self.api_data_handler)
        self.app.router.add_get('/api/summary', self.api_summary_handler)
        
        # Add CORS to all routes
        for route in list(self.app.router.routes()):
            cors.add(route)
        
        # Start server
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, host, port)
        
        print(f"🚀 Restly Dashboard starting on http://{host}:{port}")
        print(f"📊 Open your browser to view the beautiful dashboard!")
        print(f"🔄 Auto-refreshes every 30 seconds")
        print(f"⏹️  Press Ctrl+C to stop")
        
        await self.site.start()
        
        # Keep server running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down dashboard server...")
            await self.runner.cleanup()


async def main():
    parser = argparse.ArgumentParser(description="Start Restly Web Dashboard")
    parser.add_argument("--host", default="localhost", help="Host to bind to (default: localhost)")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to (default: 8080)")
    parser.add_argument("--config-dir", help="Custom config directory path")
    
    args = parser.parse_args()
    
    if not HTTP_AVAILABLE:
        print("Error: Required dependencies not installed.")
        print("Install with: pip install aiohttp aiohttp-cors")
        return 1
    
    dashboard = RestlyDashboard(args.config_dir)
    await dashboard.start_server(args.host, args.port)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
