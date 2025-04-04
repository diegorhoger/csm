import os
import io
import tempfile
import json
import traceback
import time
import uuid
import numpy as np
import threading
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit, disconnect
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from audio_analysis_service import audio_analysis_service
from socket_vad_service import socket_vad_service

# Load environment variables
load_dotenv()

# Try to get OpenAI API key
try:
    import openai
    openai_api_key = os.getenv("OPENAI_API_KEY") or os.getenv("VITE_OPENAI_API_KEY")
    if openai_api_key:
        openai.api_key = openai_api_key
        print(f"✅ Found OpenAI API key: {openai_api_key[:5]}...{openai_api_key[-5:]}")
    else:
        print("⚠️ WARNING: OpenAI API key not found in environment variables")
except ImportError:
    print("⚠️ OpenAI package not installed, AI features will be unavailable")

# Initialize Flask app
app = Flask(__name__)

# Global configuration
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
TEMP_DIR = tempfile.gettempdir()
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")

# Enable CORS for development and production
CORS(app, resources={r"/*": {"origins": CORS_ORIGINS.split(",")}}, supports_credentials=True)

# Initialize SocketIO with appropriate async mode
# Python 3.13 has issues with gevent monkey-patching, use threading mode
try:
    import sys
    if sys.version_info >= (3, 13):
        # For Python 3.13+, use threading mode to avoid gevent monkey-patching issues
        async_mode = 'threading'
        print(f"🔄 Using threading mode for Python {sys.version}")
    else:
        # For older Python versions, prefer eventlet for production, fallback to gevent
        try:
            import eventlet
            async_mode = 'eventlet'
        except ImportError:
            try:
                import gevent
                async_mode = 'gevent'
            except ImportError:
                async_mode = 'threading'
except Exception as e:
    # Fallback to threading mode which is always available
    async_mode = 'threading'
    print(f"⚠️ Exception setting async mode: {e}, falling back to threading")
        
print(f"🔄 Using SocketIO async mode: {async_mode}")

socketio = SocketIO(
    app, 
    cors_allowed_origins=CORS_ORIGINS.split(","), 
    async_mode=async_mode,
    logger=DEBUG,
    engineio_logger=DEBUG
)

# Helper function for logging
def log(message):
    """Log a message to the console with timestamp."""
    if DEBUG:
        print(f"[{time.strftime('%H:%M:%S')}] {message}")

# Socket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle new WebSocket connections."""
    log(f"New client connected: {request.sid}")
    log(f"Connection details: Origin: {request.origin}")
    emit('connected', {'status': 'connected', 'sid': request.sid})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnections."""
    log(f"Client disconnected: {request.sid}")
    
    # Clean up any VAD session if it exists
    session_id = request.args.get('session_id')
    if session_id:
        socket_vad_service.remove_session(session_id)
        log(f"Removed VAD session: {session_id}")
    
    # Also check active sessions for this client ID
    for sid, session in list(active_sessions.items()):
        if session.get('client_id') == request.sid:
            del active_sessions[sid]
            log(f"Removed session {sid} for disconnected client {request.sid}")

# Track active sessions
active_sessions = {}

@socketio.on('init_vad')
def handle_init_vad(data=None):
    """Initialize a new VAD session or retrieve an existing one."""
    try:
        data = data or {}
        # Get session ID from data or create a new one
        session_id = data.get('session_id')
        
        # Get or create a session via the socket VAD service
        session_id, session = socket_vad_service.get_or_create_session(session_id)
        
        # Store session mapping
        active_sessions[session_id] = {
            'client_id': request.sid,
            'created_at': time.time(),
            'last_activity': time.time()
        }
        
        # Return session info
        emit('vad_initialized', {
            'session_id': session_id,
            'noise_profile': session.get_noise_profile(),
            'config': session.config
        })
        
        log(f"VAD session initialized: {session_id}")
        
    except Exception as e:
        log(f"Error initializing VAD: {e}")
        log(traceback.format_exc())
        emit('error', {'message': f"Failed to initialize VAD: {str(e)}"})

@socketio.on('process_audio')
def handle_process_audio(data):
    """Process audio data for VAD."""
    try:
        # Get session ID and audio data
        session_id = data.get('session_id')
        audio_data = data.get('audio') or data.get('level')
        
        if not session_id:
            emit('error', {'message': "Missing session_id"})
            return
            
        # Update session activity time
        if session_id in active_sessions:
            active_sessions[session_id]['last_activity'] = time.time()
            
        # If we have a simple audio level, use the legacy approach
        if isinstance(audio_data, (int, float)):
            result = audio_analysis_service.add_audio_sample(audio_data, int(time.time() * 1000))
            emit('vad_result', result)
            return
        
        # Otherwise, use the full socket VAD service
        if not audio_data:
            emit('error', {'message': "Missing audio data"})
            return
            
        # Process the audio
        result = socket_vad_service.process_audio(session_id, audio_data)
        
        # Check for events that should trigger specific responses
        if 'event' in result:
            emit(result['event'], result)
        else:
            emit('vad_result', result)
            
    except Exception as e:
        log(f"Error processing audio: {e}")
        log(traceback.format_exc())
        emit('error', {'message': f"Failed to process audio: {str(e)}"})

@socketio.on('force_recalibration')
def handle_force_recalibration(data):
    """Force recalibration of the VAD system."""
    try:
        # Get session ID
        session_id = data.get('session_id')
        
        if not session_id:
            # If no session ID, use legacy approach with audio_analysis_service
            audio_analysis_service.force_recalibration()
            emit('recalibration_complete', audio_analysis_service.get_threshold())
            return
        
        # Get the session
        session = socket_vad_service.get_session(session_id)
        if not session:
            emit('error', {'message': f"Session {session_id} not found"})
            return
        
        # Force recalibration
        session.force_recalibration()
        
        emit('recalibration_started', {
            'session_id': session_id,
            'timestamp': int(time.time() * 1000)
        })
        
    except Exception as e:
        log(f"Error forcing recalibration: {e}")
        log(traceback.format_exc())
        emit('error', {'message': f"Failed to force recalibration: {str(e)}"})

@socketio.on('update_vad_config')
def handle_update_vad_config(data):
    """Update the VAD configuration for a session."""
    try:
        # Get session ID and config
        session_id = data.get('session_id')
        config = data.get('config')
        
        if not session_id or not config:
            emit('error', {'message': "Missing session_id or config"})
            return
        
        # Get the session
        session = socket_vad_service.get_session(session_id)
        if not session:
            emit('error', {'message': f"Session {session_id} not found"})
            return
        
        # Update the session config
        session.update_vad_config(config)
        
        emit('config_updated', {
            'session_id': session_id,
            'config': session.config
        })
        
    except Exception as e:
        log(f"Error updating VAD config: {e}")
        log(traceback.format_exc())
        emit('error', {'message': f"Failed to update VAD config: {str(e)}"})

@socketio.on('update_config')
def handle_update_config(data):
    """Legacy handler for updating audio analysis config."""
    try:
        config = data.get('config', {})
        result = audio_analysis_service.update_config(config)
        emit('config_updated', result)
    except Exception as e:
        log(f"Error updating config: {e}")
        log(traceback.format_exc())
        emit('error', {'message': str(e)})

@socketio.on('get_debug_state')
def handle_get_debug_state(data):
    """Get the debug state for a session."""
    try:
        # Get session ID
        session_id = data.get('session_id')
        
        if not session_id:
            # If no session ID, get global debug state
            debug_state = audio_analysis_service.get_debug_state()
            emit('debug_state', debug_state)
            return
        
        # Get the session
        session = socket_vad_service.get_session(session_id)
        if not session:
            emit('error', {'message': f"Session {session_id} not found"})
            return
        
        # Get debug state
        debug_state = session.get_debug_state()
        
        emit('debug_state', debug_state)
        
    except Exception as e:
        log(f"Error getting debug state: {e}")
        log(traceback.format_exc())
        emit('error', {'message': f"Failed to get debug state: {str(e)}"})

# Basic API routes
@app.route('/', methods=['GET'])
def root():
    """Root endpoint for health check and version info."""
    return jsonify({
        'status': 'ok',
        'timestamp': int(time.time()),
        'service': 'CSM Backend API',
        'environment': os.getenv('FLASK_ENV', 'development'),
        'socket_io': {
            'engine': socketio.async_mode,
            'active_sessions': len(active_sessions),
            'vad_sessions': socket_vad_service.get_session_count()
        },
        'debug': DEBUG
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'timestamp': int(time.time())})

# AI endpoints (OpenAI integration)
@app.route('/api/mentors', methods=['GET'])
def get_mentors():
    """Get available mentors/assistants."""
    # This is a placeholder that can be expanded based on your mentor system
    mentors = [
        {
            'id': 'stoic',
            'name': 'Stoic Mentor',
            'description': 'A mentor grounded in stoic philosophy',
            'icon': '🧠',
            'system_prompt': 'You are a stoic mentor, offering guidance based on stoic philosophy.'
        },
        {
            'id': 'coach',
            'name': 'Life Coach',
            'description': 'A supportive life coach to help you achieve your goals',
            'icon': '⭐',
            'system_prompt': 'You are a supportive life coach, helping the user achieve their personal goals.'
        }
    ]
    
    return jsonify({'mentors': mentors})

@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    """Convert text to speech using OpenAI's TTS API."""
    try:
        data = request.json
        if not data or 'text' not in data:
            return jsonify({'error': 'Missing text parameter'}), 400
            
        text = data['text']
        voice = data.get('voice', 'alloy')  # Default voice
        
        # Check if OpenAI is available
        if 'openai' not in globals() or not openai.api_key:
            return jsonify({'error': 'OpenAI API not configured'}), 500
            
        log(f"TTS request: '{text[:30]}...' with voice {voice}")
        
        # Generate speech using OpenAI
        response = openai.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        
        # Save to a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_path = temp_file.name
        
        # Get the binary content and save it
        response.stream_to_file(temp_path)
        
        log(f"TTS audio generated: {temp_path}")
        
        # Return the audio file
        return send_file(
            temp_path,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name='speech.mp3'
        )
        
    except Exception as e:
        log(f"Error in TTS: {e}")
        log(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/transcribe', methods=['POST'])
def transcribe():
    """Transcribe audio using OpenAI's Whisper API."""
    try:
        # Check if a file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Empty file name'}), 400
            
        # Check if OpenAI is available
        if 'openai' not in globals() or not openai.api_key:
            return jsonify({'error': 'OpenAI API not configured'}), 500
            
        # Save to a temporary file
        filename = secure_filename(file.filename)
        temp_path = os.path.join(TEMP_DIR, f"transcribe_{filename}")
        file.save(temp_path)
        
        log(f"Transcribing audio file: {temp_path}")
        
        # Transcribe the audio
        with open(temp_path, "rb") as audio_file:
            transcript = openai.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
        
        # Clean up the temporary file
        os.unlink(temp_path)
        
        log(f"Transcription complete: '{transcript.text[:30]}...'")
        
        return jsonify({
            'text': transcript.text,
            'language': 'en',  # Whisper API doesn't return language info directly
            'duration_seconds': 0,  # Placeholder, would need to analyze audio
            'timestamp': int(time.time())
        })
        
    except Exception as e:
        log(f"Error in transcription: {e}")
        log(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/gpt', methods=['POST'])
def gpt():
    """Generate a response using OpenAI's API."""
    try:
        data = request.json
        if not data or 'messages' not in data:
            return jsonify({'error': 'Missing messages parameter'}), 400
            
        messages = data['messages']
        model = data.get('model', 'gpt-3.5-turbo')
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 500)
        
        # Check if OpenAI is available
        if 'openai' not in globals() or not openai.api_key:
            return jsonify({'error': 'OpenAI API not configured'}), 500
            
        mentor_id = data.get('mentor_id')
        if mentor_id:
            # If a mentor is specified, get the system prompt
            system_prompt = create_system_prompt(mentor_id)
            
            # Add system message if not already present
            if messages and messages[0].get('role') != 'system':
                messages.insert(0, {
                    'role': 'system',
                    'content': system_prompt
                })
        
        log(f"GPT request: {len(messages)} messages, model={model}, temp={temperature}")
        
        # Generate response
        response = openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        response_message = response.choices[0].message.content
        
        log(f"GPT response: '{response_message[:30]}...'")
        
        return jsonify({
            'response': response_message,
            'full_response': {
                'id': response.id,
                'model': response.model,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                },
                'timestamp': int(time.time())
            }
        })
        
    except Exception as e:
        log(f"Error in GPT: {e}")
        log(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

def create_system_prompt(mentor_id):
    """Create a system prompt based on mentor ID."""
    base_prompts = {
        'stoic': """You are a wise stoic mentor, offering guidance grounded in stoic philosophy.
Your responses should be calm, thoughtful, and focused on what is within one's control.
Emphasize the importance of virtue, rationality, and acceptance of what cannot be changed.
Quote stoic philosophers like Epictetus, Seneca, and Marcus Aurelius when appropriate.
Your goal is to help the person become more resilient, rational, and at peace with the world.""",

        'coach': """You are a supportive life coach, helping the user achieve their personal goals.
Your responses should be encouraging, practical, and action-oriented.
Focus on breaking down challenges into manageable steps and celebrating progress.
Ask clarifying questions when needed to better understand the user's situation.
Your goal is to empower the person to take positive action and build effective habits."""
    }
    
    return base_prompts.get(mentor_id, "You are a helpful AI assistant.")

# Audio analysis endpoints - legacy support
@app.route('/api/audio-analysis', methods=['OPTIONS'])
def audio_analysis_options():
    """Handle OPTIONS request for audio analysis endpoint."""
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    return response

@app.route('/api/audio-analysis', methods=['POST'])
def audio_analysis():
    """Process audio level data for VAD."""
    try:
        data = request.json
        if not data or 'level' not in data:
            return jsonify({'error': 'Missing level parameter'}), 400
            
        level = float(data['level'])
        timestamp = data.get('timestamp', int(time.time() * 1000))
        
        result = audio_analysis_service.add_audio_sample(level, timestamp)
        return jsonify(result)
        
    except Exception as e:
        log(f"Error in audio analysis: {e}")
        log(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/audio-analysis/calibrate', methods=['OPTIONS'])
def audio_analysis_calibrate_options():
    """Handle OPTIONS request for calibration endpoint."""
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    return response

@app.route('/api/audio-analysis/calibrate', methods=['POST'])
def force_calibration():
    """Force recalibration of the audio analysis system."""
    try:
        audio_analysis_service.force_recalibration()
        return jsonify({
            'status': 'calibration_started',
            'timestamp': int(time.time() * 1000)
        })
        
    except Exception as e:
        log(f"Error in force calibration: {e}")
        log(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/audio-analysis/threshold', methods=['OPTIONS'])
def audio_analysis_threshold_options():
    """Handle OPTIONS request for threshold endpoint."""
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    return response

@app.route('/api/audio-analysis/threshold', methods=['GET'])
def get_threshold():
    """Get the current threshold value."""
    try:
        profile = audio_analysis_service.get_noise_profile()
        return jsonify(profile)
        
    except Exception as e:
        log(f"Error getting threshold: {e}")
        log(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/audio-analysis/config', methods=['OPTIONS'])
def audio_analysis_config_options():
    """Handle OPTIONS request for config endpoint."""
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Methods', 'POST, PUT, OPTIONS')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    return response

@app.route('/api/audio-analysis/config', methods=['POST', 'PUT'])
def update_config():
    """Update the audio analysis service configuration."""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Missing config parameters'}), 400
            
        audio_analysis_service.update_config(data)
        return jsonify(audio_analysis_service.get_noise_profile())
        
    except Exception as e:
        log(f"Error updating config: {e}")
        log(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/audio-analysis/debug', methods=['OPTIONS'])
def audio_analysis_debug_options():
    """Handle OPTIONS request for debug endpoint."""
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    return response

@app.route('/api/audio-analysis/debug', methods=['GET'])
def get_debug_state():
    """Get debug state for the audio analysis service."""
    try:
        debug_state = audio_analysis_service.get_debug_state()
        if not debug_state:
            return jsonify({'error': 'Debug mode not enabled'}), 400
            
        return jsonify(debug_state)
        
    except Exception as e:
        log(f"Error getting debug state: {e}")
        log(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/socket.io/', methods=['OPTIONS'])
def handle_socket_io_options():
    """Handle OPTIONS request for Socket.IO endpoint."""
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    return response

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    log(f"Starting server on {host}:{port} with {socketio.async_mode} mode")
    socketio.run(app, host=host, port=port, debug=DEBUG) 