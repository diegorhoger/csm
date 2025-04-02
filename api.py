import os
os.environ["DISABLE_TRITON"] = "1"
os.environ["NO_TORCH_COMPILE"] = "1"

import io
import torch
import base64
import tempfile
import torchaudio
import traceback
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from generator import load_csm_1b, Segment
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# Global constants
TEMP_DIR = tempfile.gettempdir()
AUDIO_SAMPLE_RATE = 24000

# Load the CSM model globally for reuse
generator = None

def get_generator():
    global generator
    if generator is None:
        # Select the best available device
        if torch.cuda.is_available():
            device = "cuda"
        else:
            device = "cpu"
        print(f"Initializing CSM model on {device}...")
        generator = load_csm_1b(device=device)
    return generator

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint to verify the API is running."""
    return jsonify({"status": "ok", "model": "loaded" if generator is not None else "not_loaded"})

@app.route('/api/mentors', methods=['GET'])
def get_mentors():
    """Returns the available mentor personalities."""
    mentors = {
        "marcus": {
            "name": "Marcus Aurelius",
            "style": "calm",
            "description": "Roman Emperor and Stoic philosopher, speaks with quiet strength and wisdom."
        },
        "seneca": {
            "name": "Seneca",
            "style": "motivational",
            "description": "Roman Stoic philosopher and statesman, speaks with eloquence and motivation."
        },
        "epictetus": {
            "name": "Epictetus",
            "style": "firm",
            "description": "Former slave turned influential Stoic philosopher, speaks bluntly and challenges assumptions."
        }
    }
    return jsonify(mentors)

@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    """Converts text to speech using the CSM model."""
    try:
        # Get JSON data from request
        data = request.json
        if not data or 'text' not in data:
            return jsonify({"error": "No text provided"}), 400
            
        text = data.get('text')
        speaker_id = data.get('speaker', 0)  # Default to first speaker if not specified
        
        # Generate audio from text
        model = get_generator()
        
        # Process context if provided
        context = []
        if 'context' in data and isinstance(data['context'], list):
            for segment_data in data['context']:
                if 'text' in segment_data and 'speaker' in segment_data and 'audio' in segment_data:
                    # Convert base64 audio to tensor
                    audio_bytes = base64.b64decode(segment_data['audio'])
                    audio_tensor = convert_audio_bytes_to_tensor(audio_bytes)
                    
                    # Create segment
                    segment = Segment(
                        text=segment_data['text'],
                        speaker=segment_data['speaker'],
                        audio=audio_tensor
                    )
                    context.append(segment)
        
        # Generate audio
        print(f"Generating audio for text: {text}")
        audio_tensor = model.generate(
            text=text,
            speaker=speaker_id,
            context=context,
            max_audio_length_ms=30000,  # 30 seconds max
            temperature=0.9,
            topk=50
        )
        
        # Convert tensor to WAV file in memory
        buffer = io.BytesIO()
        torchaudio.save(buffer, audio_tensor.unsqueeze(0).cpu(), model.sample_rate, format="wav")
        buffer.seek(0)
        
        # Return audio file
        return send_file(
            buffer,
            mimetype="audio/wav",
            as_attachment=True,
            download_name=f"speech_{speaker_id}.wav"
        )
        
    except Exception as e:
        print(f"Error in text_to_speech: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/transcribe', methods=['POST'])
def transcribe_audio():
    """Transcribes speech to text.
    
    Note: This is a placeholder. In a real implementation, 
    you would integrate with a speech recognition service like Whisper.
    """
    try:
        # Check if file is in request
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400
            
        file = request.files['audio']
        if file.filename == '':
            return jsonify({"error": "No audio file selected"}), 400
            
        # Save temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(TEMP_DIR, filename)
        file.save(filepath)
        
        # Placeholder for speech-to-text processing
        # In a real implementation, you would call a speech recognition model here
        # For now, we'll return a dummy response
        
        # TODO: Implement actual speech-to-text using Whisper or another service
        transcription = "This is a placeholder transcription. Implement Whisper integration here."
        
        # Clean up
        os.remove(filepath)
        
        return jsonify({"transcription": transcription})
        
    except Exception as e:
        print(f"Error in transcribe_audio: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/stream', methods=['POST'])
def stream_audio():
    """Streams audio processing for real-time conversation.
    
    Note: This is a placeholder for future implementation of streaming audio.
    """
    return jsonify({"message": "Streaming not yet implemented"}), 501

def convert_audio_bytes_to_tensor(audio_bytes):
    """Converts audio bytes to a PyTorch tensor."""
    # Save bytes to a temporary file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
        temp_file.write(audio_bytes)
        temp_path = temp_file.name
    
    # Load audio file as tensor
    try:
        waveform, sample_rate = torchaudio.load(temp_path)
        # Convert to mono if needed
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)
        
        # Resample if needed
        if sample_rate != AUDIO_SAMPLE_RATE:
            waveform = torchaudio.functional.resample(
                waveform, orig_freq=sample_rate, new_freq=AUDIO_SAMPLE_RATE
            )
        
        # Return flattened mono audio
        return waveform.squeeze()
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == '__main__':
    # Initialize the model at startup
    get_generator()
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000) 