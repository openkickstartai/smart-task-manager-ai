# Smart Task Manager AI

An intelligent task management system that learns from your productivity patterns and optimizes workflow using machine learning.

## Features

- 🧠 **AI-Powered Prioritization** - Tasks automatically prioritized based on your work patterns
- 📊 **Smart Deadline Predictions** - ML models predict realistic completion times
- 🗣️ **Natural Language Input** - Add tasks using plain English
- 📈 **Productivity Insights** - Automated reports and recommendations
- 🔗 **Calendar Integration** - Sync with Google Calendar, Outlook, etc.

## Tech Stack

- **Backend:** Python, FastAPI, PostgreSQL, Redis
- **ML Engine:** Scikit-learn, Pandas, NumPy
- **Frontend:** React, TypeScript, Tailwind CSS
- **Queue:** Celery with Redis
- **Deployment:** Docker, Docker Compose

## Quick Start

```bash
# Clone the repository
git clone https://github.com/openkickstartai/smart-task-manager-ai
cd smart-task-manager-ai

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Run with Docker Compose
docker-compose up -d

# Or run locally
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Usage

1. **Add a task:**
   ```
   "Finish the quarterly report by Friday at 5pm"
   ```

2. **Get AI prioritization:**
   The system will analyze your workload and suggest the optimal order.

3. **View insights:**
   Check your productivity dashboard for personalized recommendations.

## API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.
