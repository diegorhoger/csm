# Council - Emotionally Intelligent AI Mentor

An emotionally intelligent, voice-first AI mentor designed to guide users through an inner journey of growth using real-time emotion recognition, stoic philosophy, and advanced conversational intelligence.

## Project Structure

- `/backend`: The backend API with voice activity detection (VAD), OpenAI integration, emotion analysis, and WebSocket communication
- `/frontend`: The React application with UI components, Socket.IO integration, emotion tracking, and audio processing
- `/docs`: Project documentation including architecture, planning, and ethical guidelines

## Features

- **Emotion Intelligence**: Text-based emotion analysis with Hawkins Energy Scale mapping
- **Dynamic Mentor Selection**: Chooses the appropriate mentor based on emotional state
- **Voice-powered Interface**: Speak directly to AI mentors and hear their responses
- **Real-time Voice Activity Detection**: Detects speech using advanced Silero VAD
- **Multiple Stoic Philosophers**: Interact with Marcus Aurelius, Seneca, or Epictetus
- **Ethical Filtering**: Ensures responses align with the Council AI Constitution
- **Secure API Integration**: All API keys are stored securely on the backend
- **Persistent Storage**: Conversation history and emotional journey tracking with Supabase

## Backend

The backend is a Flask and Socket.IO-based API that provides:

- Advanced Voice Activity Detection (VAD) via WebSockets with Silero integration
- OpenAI API integration for GPT models and transcription
- Emotion analysis using pre-trained DistilBERT models
- Secure API key storage and management
- Supabase database integration
- Ethical filtering based on the Council AI Constitution

## Getting Started

### Backend Setup

```bash
# Navigate to the backend directory
cd backend

# Set up virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your API keys
# Example:
# OPENAI_API_KEY=your_api_key_here
# DEBUG=true
# CORS_ORIGINS=http://localhost:5173,http://localhost:3000
# SUPABASE_URL=your_supabase_url
# SUPABASE_KEY=your_supabase_key

# Run the backend services
python api.py --port 5002
python socket_vad_service.py --port 5003
```

### Frontend Setup

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Create .env file (if not already present)
# Example content in frontend/DOCKER_README.md

# Run the development server
npm run dev
```

## Docker Setup

For a containerized setup with all services:

```bash
cd frontend
docker-compose up --build
```

See [DOCKER_README.md](frontend/DOCKER_README.md) for detailed Docker instructions.

## How to Use

1. Start the backend services and frontend
2. Open your browser to http://localhost:5173
3. Begin a conversation with the AI mentor
4. Your emotional state will be analyzed and tracked
5. The most appropriate mentor will guide you based on your emotional state
6. Your conversation history and emotional journey will be saved

## Documentation

For detailed documentation, see the [docs](docs) directory:

- [ARCHITECTURE.md](docs/ARCHITECTURE.md): System architecture and component design
- [PLAN.md](docs/PLAN.md): Implementation plan and roadmap
- [PRD.md](docs/PRD.md): Product requirements and specifications
- [Council AI Constitution V1.md](docs/Council%20AI%20Constitution%20V1.md): Ethical principles and guidelines

## Troubleshooting

### Common Issues

- **WebSocket Connection**: Ensure all backend services are running (API port 5002, VAD port 5003)
- **Database Connection**: Check Supabase connection parameters
- **Emotion Analysis**: Verify the emotion service is running properly
- **Docker Issues**: See specific troubleshooting in [DOCKER_README.md](frontend/DOCKER_README.md)

For detailed debugging information, visit http://localhost:5002/debug

## License

MIT 