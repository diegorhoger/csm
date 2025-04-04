# CSM Backend API

A consolidated API backend for the CSM project with voice activity detection (VAD), OpenAI integration, and real-time communication features.

## Features

- Voice Activity Detection (VAD) via WebSockets
- OpenAI API integration for text generation (GPT models)
- Text-to-Speech capabilities
- Speech-to-Text transcription
- Real-time communication with Socket.IO
- RESTful API endpoints
- Diagnostic tools for debugging WebSocket connections

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
   CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://localhost:5001
   ```

## Running the Server

```bash
python api.py --port 5001
```

The server will start on http://0.0.0.0:5001 by default. You can change the port and host using command line arguments or environment variables:

```bash
# Using command line arguments
python api.py --port 8000 --host 127.0.0.1

# Using environment variables
PORT=8000 HOST=127.0.0.1 python api.py
```

## API Endpoints

### Health Check

- `GET /api/health` - Check if the API is running

### AI Endpoints

- `GET /api/mentors` - Get list of available AI mentors/assistants
- `POST /api/mentor-chat` - Generate text using a specific mentor's style
- `POST /api/transcribe` - Transcribe audio to text

### Diagnostic Tools

- `GET /test` - Access the test page for debugging WebSocket and API integrations

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
- `debug_connection` - Test connection and get diagnostic information

### Response Events

- `connected` - Sent after successful connection
- `vad_initialized` - VAD session initialized
- `vad_result` - VAD processing result
- `speech_start` - Speech detected
- `speech_end` - End of speech detected
- `recalibration_started` - VAD recalibration started
- `config_updated` - Configuration updated
- `debug_state` - Debug state information
- `debug_response` - Diagnostic response with connection details
- `error` - Error message

## Development

The backend is built with Flask and Socket.IO, providing both REST API endpoints and real-time WebSocket communication.

### Architecture

- `api.py` - Main application file
- `audio_analysis_service.py` - Audio level analysis service
- `socket_vad_service.py` - Socket-based VAD service
- `static/` - Static files for testing and diagnostics

### Environment Variables

- `DEBUG` - Enable debug mode (default: true)
- `OPENAI_API_KEY` - OpenAI API key
- `PORT` - Server port (default: 5000)
- `HOST` - Server host (default: 0.0.0.0)
- `CORS_ORIGINS` - Comma-separated list of allowed origins for CORS

## Troubleshooting

### WebSocket Connection Issues

If you experience WebSocket connection problems:

1. Check that CORS is properly configured with all necessary origins
2. Ensure you're using the correct Socket.IO client version (v4.x)
3. Use the built-in test page at `/test` to diagnose connection issues
4. Look for detailed error messages in the server logs

### Audio Transcription Issues

If audio transcription isn't working:

1. Check that your OpenAI API key is valid and has access to the Whisper API
2. Ensure audio files are in a supported format (WAV is preferred)
3. Check the audio file size (should be at least 1KB)
4. Look for detailed error messages in the server logs

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

## License

MIT 