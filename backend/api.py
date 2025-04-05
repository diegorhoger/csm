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
from flask import Flask, request, jsonify, send_file, Response, stream_with_context
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
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://localhost:5001")

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
    cors_allowed_origins="*",  # Allow all origins temporarily to debug the issue
    async_mode=async_mode,
    logger=DEBUG,
    engineio_logger=DEBUG,
    ping_timeout=60,
    ping_interval=25,
    max_http_buffer_size=1024 * 1024,  # 1MB buffer size
    websocket_ping_timeout=55  # Websocket specific ping timeout
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

@socketio.on('debug_connection')
def handle_debug_connection(data=None):
    """Debug connection issues."""
    try:
        log(f"Debug connection request received from {request.sid}")
        
        # Get client-side debugging info
        client_info = data or {}
        log(f"Client debugging info: {client_info}")
        
        # Send back server-side information about the connection
        emit('debug_response', {
            'server_time': int(time.time() * 1000),
            'sid': request.sid,
            'origin': request.origin,
            'transport': request.args.get('transport', 'unknown'),
            'async_mode': async_mode,
            'active_sessions': len(active_sessions)
        })
        
    except Exception as e:
        log(f"Error in debug endpoint: {str(e)}")
        log(traceback.format_exc())
        emit('error', {'message': f"Debug error: {str(e)}"})

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

# Track conversation history
conversation_histories = {}

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

# Serve test HTML page
@app.route('/test')
def test_page():
    """Serve a test page for API testing."""
    return app.send_static_file('index.html')

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
    """Get available mentors."""
    mentors = [
        {
            "id": "marcus",
            "name": "Marcus Aurelius",
            "style": "calm",
            "title": "Philosopher and Roman Emperor",
            "years": "121-180 CE",
            "image": "./images/marcus.png",
            "description": "Known for his personal reflections in \"Meditations\", Marcus Aurelius ruled as Roman Emperor while practicing Stoic philosophy.",
            "voiceId": "0",
            "voice": os.getenv("TTS_VOICE_MARCUS", "onyx")
        },
        {
            "id": "seneca",
            "name": "Seneca",
            "style": "motivational",
            "title": "Philosopher and Statesman",
            "years": "4 BCE-65 CE",
            "image": "./images/seneca.png",
            "description": "A Roman Stoic philosopher who served as advisor to Emperor Nero and wrote influential letters on ethics and natural philosophy.",
            "voiceId": "1",
            "voice": os.getenv("TTS_VOICE_SENECA", "echo")
        },
        {
            "id": "epictetus",
            "name": "Epictetus",
            "style": "firm",
            "title": "Stoic Philosopher and Former Slave",
            "years": "50-135 CE",
            "image": "./images/epictetus.png",
            "description": "Born a slave and later freed, Epictetus taught that philosophy is a way of life, not just an intellectual exercise.",
            "voiceId": "2",
            "voice": os.getenv("TTS_VOICE_EPICTETUS", "ash")
        }
    ]
    return jsonify(mentors)

@app.route('/api/mentor-chat', methods=['POST'])
def mentor_chat():
    """Chat with a mentor using OpenAI."""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        conversation_id = data.get('conversation_id', str(uuid.uuid4()))
        messages = data.get('messages', [])
        stream = data.get('stream', False)
        model = data.get('model', 'gpt-4o')
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 1000)
        
        # Check if messages is empty or not provided
        if not messages:
            return jsonify({'error': 'No messages provided'}), 400
            
        # Check if OpenAI is available
        if 'openai' not in globals() or not openai.api_key:
            return jsonify({'error': 'OpenAI API not configured'}), 500
            
        # Log the request
        log(f"Mentor chat request: {len(messages)} messages, model={model}, temp={temperature}, stream={stream}")
        
        # Update conversation history
        if conversation_id not in conversation_histories:
            conversation_histories[conversation_id] = []
            
        # Add new messages to history
        conversation_histories[conversation_id].extend(messages)
        
        # Trim history if it gets too long (keep last 20 messages)
        if len(conversation_histories[conversation_id]) > 20:
            conversation_histories[conversation_id] = conversation_histories[conversation_id][-20:]
            
        # If streaming is requested, use SSE for streaming response
        if stream:
            def generate():
                try:
                    response = openai.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        stream=True
                    )
                    
                    for chunk in response:
                        content = chunk.choices[0].delta.content
                        if content:
                            yield f"data: {json.dumps({'content': content})}\n\n"
                            
                    yield f"data: {json.dumps({'done': True})}\n\n"
                    
                except Exception as e:
                    log(f"Error in streaming mentor chat: {e}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
                    
            return Response(stream_with_context(generate()), content_type='text/event-stream')
            
        # For non-streaming responses, return the complete response
        response = openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        response_message = response.choices[0].message.content
        log(f"Mentor response: '{response_message[:30]}...'")
        
        # Add response to conversation history
        conversation_histories[conversation_id].append({
            "role": "assistant",
            "content": response_message
        })
        
        return jsonify({
            'content': response_message,
            'conversation_id': conversation_id
        })
        
    except Exception as e:
        log(f"Error in mentor chat: {e}")
        log(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    """Convert text to speech using OpenAI's TTS API."""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        text = data.get('text')
        voice = data.get('voice', 'onyx')  # Use 'onyx' as the default voice
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
            
        # Check if OpenAI is available
        if 'openai' not in globals() or not openai.api_key:
            return jsonify({'error': 'OpenAI API not configured'}), 500
            
        log(f"TTS request: '{text[:30]}...' with voice {voice}")
        
        # Generate speech using OpenAI
        response = openai.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
            speed=data.get('speed', 1.0)
        )
        
        # Save audio to temporary file
        temp_file = f"tts_{str(uuid.uuid4())}.mp3"
        temp_path = os.path.join(TEMP_DIR, temp_file)
        
        with open(temp_path, 'wb') as f:
            response.stream_to_file(temp_path)
            
        log(f"TTS audio generated: {temp_path}")
        
        # Send the file
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
        log("Transcribe endpoint called")
        
        # Debug request details
        log(f"Request files: {list(request.files.keys())}")
        log(f"Request headers: {dict(request.headers)}")
        
        # Check if file was uploaded
        if 'audio' not in request.files and 'file' not in request.files:
            log("Error: No audio file provided in request")
            return jsonify({'error': 'No audio file provided'}), 400
            
        # Get the file from either 'audio' or 'file' field
        file = request.files.get('audio') or request.files.get('file')
        if not file:
            log("Error: File object is None")
            return jsonify({'error': 'File object is None'}), 400
            
        filename = secure_filename(file.filename)
        log(f"Processing file: {filename}")
        
        # Check if OpenAI is available
        if 'openai' not in globals() or not openai.api_key:
            log("Error: OpenAI API not configured")
            return jsonify({'error': 'OpenAI API not configured'}), 500
            
        # Save file to temporary directory
        temp_path = os.path.join(TEMP_DIR, f"transcribe_{filename}")
        file.save(temp_path)
        
        log(f"Transcribing audio: {temp_path}, file size: {os.path.getsize(temp_path)} bytes")
        
        # Transcribe the audio
        try:
            with open(temp_path, "rb") as audio_file:
                transcript = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=request.form.get('language', None),
                    prompt=request.form.get('prompt', None)
                )
                
            log(f"Transcription result: {transcript.text[:100]}...")
        except Exception as e:
            log(f"OpenAI transcription error: {str(e)}")
            log(traceback.format_exc())
            return jsonify({'error': f"OpenAI transcription error: {str(e)}"}), 500
        
        # Clean up
        try:
            os.remove(temp_path)
            log(f"Cleaned up temporary file: {temp_path}")
        except Exception as cleanup_error:
            log(f"Warning: Could not clean up temp file: {str(cleanup_error)}")
            
        return jsonify({
            'text': transcript.text
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
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        messages = data.get('messages', [])
        model = data.get('model', 'gpt-3.5-turbo')
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 1000)
        
        # Check if OpenAI is available
        if 'openai' not in globals() or not openai.api_key:
            return jsonify({'error': 'OpenAI API not configured'}), 500
            
        # Check if messages is empty or not provided
        if not messages:
            return jsonify({'error': 'No messages provided'}), 400
            
        # For older format support
        if isinstance(messages, str):
            # Convert string to a user message
            messages = [{"role": "user", "content": messages}]
            
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
            'content': response_message
        })
        
    except Exception as e:
        log(f"Error in GPT: {e}")
        log(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

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

@app.route('/api/vad/stats', methods=['GET'])
def get_vad_stats():
    """Get stats about the VAD systems for comparison."""
    try:
        # Get all active session stats
        session_stats = []
        for session_id, session in socket_vad_service.sessions.items():
            session_stats.append(session.get_debug_state())
        
        # Aggregate stats
        total_frames = sum(s['total_frames'] for s in session_stats)
        speech_frames = sum(s['speech_frames'] for s in session_stats)
        
        # Get Silero VAD stats from a dummy session if no active sessions
        silero_stats = {}
        if not session_stats:
            from silero_vad_service import SileroVADService
            silero_vad = SileroVADService()
            silero_stats = silero_vad.get_stats()
        else:
            # Use stats from the first session that has Silero VAD enabled
            for s in session_stats:
                if 'silero_vad' in s and s['silero_vad']:
                    silero_stats = s['silero_vad']
                    break
        
        return jsonify({
            'active_sessions': len(session_stats),
            'total_frames_processed': total_frames,
            'speech_frames_detected': speech_frames,
            'speech_ratio': speech_frames / max(1, total_frames),
            'silero_vad': silero_stats
        })
        
    except Exception as e:
        log(f"Error getting VAD stats: {e}")
        log(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    log(f"Starting server on {host}:{port} with {socketio.async_mode} mode")
    socketio.run(app, host=host, port=port, debug=DEBUG) 