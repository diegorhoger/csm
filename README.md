# CSM - Conversational Stoic Mentor

A conversational AI application with voice activity detection and real-time communication capabilities.

## Project Structure

- `/backend`: The consolidated backend API with voice activity detection (VAD) and AI integration
- `/stoic-mentor`: The frontend application

## Backend

The backend is a Flask and Socket.IO-based API that provides:

- Voice Activity Detection (VAD) via WebSockets
- OpenAI API integration for GPT models, text-to-speech, and transcription
- Real-time communication capabilities

[See Backend Documentation](./backend/README.md)

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
# See backend README for details

# Run the backend
python api.py
```

### Frontend Setup

See the stoic-mentor directory for frontend setup instructions.

## Development

The project is structured to support modern development practices:

- Backend and frontend are separated for independent development
- Real-time communication via WebSockets
- AI integration with OpenAI's APIs
- Voice activity detection for interactive experiences

## License

MIT 