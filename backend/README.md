# CSM Backend API

A consolidated API backend for the CSM project with voice activity detection (VAD), OpenAI integration, and real-time communication features.

## Features

- Voice Activity Detection (VAD) via WebSockets
- OpenAI API integration for text generation (GPT models)
- Text-to-Speech capabilities
- Speech-to-Text transcription
- Real-time communication with Socket.IO
- RESTful API endpoints

## Setup & Installation

### Prerequisites

- Python 3.8+
- Virtual environment (recommended)
- OpenAI API key for AI features

### Installation

1. Clone the repository
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your configuration:
   ```
   OPENAI_API_KEY=your_api_key_here
   DEBUG=true
   CORS_ORIGINS=http://localhost:5173,http://localhost:3000
   ```

## Running the Server

```bash
python api.py
```

The server will start on http://0.0.0.0:5000 by default. You can change the port and host using environment variables:

```bash
PORT=8000 HOST=127.0.0.1 python api.py
```

## API Endpoints

### Health Check

- `GET /api/health` - Check if the API is running

### AI Endpoints

- `GET /api/mentors` - Get list of available AI mentors/assistants
- `POST /api/gpt` - Generate text using OpenAI's models
- `POST /api/tts` - Convert text to speech
- `POST /api/transcribe` - Transcribe audio to text

### Audio Analysis

- `POST /api/audio-analysis` - Process audio level data
- `POST /api/audio-analysis/calibrate` - Force recalibration
- `GET /api/audio-analysis/threshold` - Get current threshold values
- `POST /api/audio-analysis/config` - Update configuration
- `GET /api/audio-analysis/debug` - Get debug state

## WebSocket Events

### Connection Events

- `connect` - Client connects
- `disconnect` - Client disconnects

### VAD (Voice Activity Detection)

- `init_vad` - Initialize VAD session
- `process_audio` - Process audio data for VAD
- `force_recalibration` - Force recalibration of VAD system
- `update_vad_config` - Update VAD configuration
- `get_debug_state` - Get debug information

### Response Events

- `connected` - Sent after successful connection
- `vad_initialized` - VAD session initialized
- `vad_result` - VAD processing result
- `speech_start` - Speech detected
- `speech_end` - End of speech detected
- `recalibration_started` - VAD recalibration started
- `config_updated` - Configuration updated
- `debug_state` - Debug state information
- `error` - Error message

## Development

The backend is built with Flask and Socket.IO, providing both REST API endpoints and real-time WebSocket communication.

### Architecture

- `api.py` - Main application file
- `audio_analysis_service.py` - Audio level analysis service
- `socket_vad_service.py` - Socket-based VAD service

### Environment Variables

- `DEBUG` - Enable debug mode (default: true)
- `OPENAI_API_KEY` - OpenAI API key
- `PORT` - Server port (default: 5000)
- `HOST` - Server host (default: 0.0.0.0)
- `CORS_ORIGINS` - Comma-separated list of allowed origins for CORS

## Python 3.13 Compatibility

The backend has been tested and configured to work with Python 3.13, which has known compatibility issues with some async libraries. If you're using Python 3.13:

1. The backend will automatically use the `threading` async mode instead of `eventlet` or `gevent`
2. Performance may be slightly lower than with specialized async libraries, but functionality remains the same
3. In the future, when libraries fully support Python 3.13, you can modify the code to use them

If you're using Python 3.8-3.12, you can uncomment and install one of the optional async backends in requirements.txt for better performance:

```bash
# Uncomment the relevant line in requirements.txt first
pip install eventlet==0.33.3
# OR
pip install gevent==24.2.1 gevent-websocket==0.10.1
```

## Testing

You can test the backend using the included test client:

```bash
# Install test dependencies
pip install requests python-socketio

# Run the test client
python test_client.py
```

The test client verifies both the REST API endpoints and WebSocket functionality.

## License

MIT 