# CSM - Conversational Stoic Mentor

A voice-powered AI mentor application that allows users to have philosophical conversations with famous Stoic philosophers through a natural speech interface.

## Project Structure

- `/backend`: The consolidated backend API with voice activity detection (VAD), OpenAI integration, and WebSocket communication
- `/stoic-mentor`: The frontend application with React, Socket.IO, and audio processing capabilities

## Features

- **Voice-powered Interface**: Speak directly to AI mentors and hear their responses
- **Real-time Voice Activity Detection**: Detects speech start and end using WebSocket-based VAD
- **Multiple Stoic Philosophers**: Interact with Marcus Aurelius, Seneca, or Epictetus
- **Natural Conversation Flow**: Smooth conversation with proper turn-taking
- **Secure API Integration**: All API keys are stored securely on the backend
- **Streaming Responses**: Real-time streaming of AI responses for natural conversation

## Backend

The backend is a Flask and Socket.IO-based API that provides:

- Voice Activity Detection (VAD) via WebSockets
- OpenAI API integration for GPT models and transcription
- Secure API key storage and management
- Real-time communication capabilities
- Audio transcription services

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
# CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://localhost:5001

# Run the backend
python api.py --port 5001
```

### Frontend Setup

```bash
# Navigate to the frontend directory
cd stoic-mentor

# Install dependencies
npm install

# Create .env file (optional, since we now use the backend for API calls)
# Example:
# VITE_BACKEND_URL=http://localhost:5001

# Run the development server
npm run dev
```

## How to Use

1. Start the backend server on port 5001
2. Start the frontend development server
3. Open your browser to http://localhost:5173
4. Select a Stoic mentor from the options
5. Click the microphone button and start speaking
6. The mentor will respond with philosophical guidance based on Stoic principles

## Testing

You can test various API endpoints directly using the built-in test page:

1. Start the backend server
2. Visit http://localhost:5001/test in your browser
3. Test the health endpoint, mentor API, Socket.IO connection, and audio transcription

## Troubleshooting

### WebSocket Connection Issues

If you experience WebSocket connection problems:

1. Check that the backend server is running on port 5001
2. Ensure that CORS is properly configured on the backend
3. Try using the test page to diagnose connection issues
4. Look for any error messages in the browser console or backend logs

### Audio Recording Issues

If audio recording doesn't work:

1. Ensure your browser has permission to access the microphone
2. Check that the audio format is supported (WAV is preferred)
3. Try testing audio recording using the test page

## License

MIT 