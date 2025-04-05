"""
Test script for Silero VAD with real audio samples
"""

import time
import numpy as np
import wave
import os
import urllib.request
from silero_vad_service import SileroVADService

# URL to a public domain sample with speech
SAMPLE_URL = "https://filesamples.com/samples/audio/wav/sample3.wav"
SAMPLE_PATH = "sample_speech.wav"

def download_sample():
    """Download WAV sample directly."""
    if not os.path.exists(SAMPLE_PATH):
        print(f"Downloading sample from {SAMPLE_URL}")
        try:
            urllib.request.urlretrieve(SAMPLE_URL, SAMPLE_PATH)
            return True
        except Exception as e:
            print(f"Error downloading sample: {e}")
            return False
    return True

def load_test_audio(file_path):
    """Load audio from a WAV file and ensure it's at 16kHz."""
    with wave.open(file_path, 'rb') as wav:
        # Get basic info
        sample_rate = wav.getframerate()
        n_channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        n_frames = wav.getnframes()
        
        # Read audio data
        audio_data = wav.readframes(n_frames)
        
        print(f"Loaded audio: {file_path}")
        print(f"Sample rate: {sample_rate}Hz")
        print(f"Channels: {n_channels}")
        print(f"Sample width: {sample_width} bytes")
        print(f"Frames: {n_frames}")
        print(f"Duration: {n_frames/sample_rate:.2f}s")
        
        # Convert to numpy array
        if sample_width == 2:  # 16-bit audio
            dtype = np.int16
        elif sample_width == 4:  # 32-bit audio
            dtype = np.int32
        else:
            raise ValueError(f"Unsupported sample width: {sample_width}")
        
        # Reshape for mono or stereo
        audio_np = np.frombuffer(audio_data, dtype=dtype)
        if n_channels > 1:
            audio_np = audio_np.reshape(-1, n_channels)
            # Extract first channel only
            audio_np = audio_np[:, 0]
        
        # Resample to 16kHz if needed
        target_sample_rate = 16000
        if sample_rate != target_sample_rate:
            print(f"Resampling from {sample_rate}Hz to {target_sample_rate}Hz")
            try:
                # Try to use librosa if available
                import librosa
                audio_np = librosa.resample(
                    audio_np.astype(float), 
                    orig_sr=sample_rate, 
                    target_sr=target_sample_rate
                )
                # Convert back to int16
                audio_np = (audio_np * 32767).astype(np.int16)
                sample_rate = target_sample_rate
            except ImportError:
                # Simple resampling as fallback
                print("Librosa not available, using simple resampling (lower quality)")
                # Calculate resampling ratio
                ratio = target_sample_rate / sample_rate
                new_length = int(len(audio_np) * ratio)
                # Simple linear interpolation
                indices = np.linspace(0, len(audio_np) - 1, new_length)
                audio_np = np.interp(indices, np.arange(len(audio_np)), audio_np)
                audio_np = audio_np.astype(np.int16)
                sample_rate = target_sample_rate
        
        return audio_np, sample_rate

def main():
    # Check if we can use real audio
    if not os.path.exists(SAMPLE_PATH):
        if not download_sample():
            # If download failed, fall back to test_audio.wav
            print("Falling back to test_audio.wav")
            test_file = "test_audio.wav"
        else:
            test_file = SAMPLE_PATH
    else:
        test_file = SAMPLE_PATH
    
    # Initialize Silero VAD
    print("Initializing Silero VAD...")
    silero_vad = SileroVADService({
        'debug': True,
        'sample_rate': 16000,
        'threshold': 0.3
    })
    
    # Load test audio
    print("\nLoading test audio...")
    try:
        audio_np, sample_rate = load_test_audio(test_file)
    except Exception as e:
        print(f"Error loading audio: {e}")
        return
    
    # Process in frames of 30ms (large enough for single inference)
    frame_duration_ms = 30
    frame_size = int(sample_rate * frame_duration_ms / 1000)
    total_frames = len(audio_np) // frame_size
    
    print(f"\nProcessing {total_frames} frames of {frame_size} samples ({frame_duration_ms}ms each)...")
    print(f"Required samples for VAD model: {silero_vad.required_samples}")
    
    # Stats
    speech_frames = 0
    total_time = 0
    speech_segments = []
    current_segment = None
    max_frames_to_process = min(total_frames, 1000)  # Limit to 1000 frames (30 seconds at 30ms/frame)
    
    # Create audio buffer for processing
    audio_buffer = np.array([], dtype=np.int16)
    
    for i in range(max_frames_to_process):
        frame = audio_np[i * frame_size:(i + 1) * frame_size]
        
        # Add current frame to buffer
        audio_buffer = np.append(audio_buffer, frame)
        
        # Check if we have enough samples
        if len(audio_buffer) >= silero_vad.required_samples:
            # Process exactly the required number of samples
            process_chunk = audio_buffer[:silero_vad.required_samples]
            
            # Convert to bytes for processing
            chunk_bytes = process_chunk.tobytes()
            
            # Process with Silero VAD
            start_time = time.time()
            result = silero_vad.process_audio(chunk_bytes)
            end_time = time.time()
            
            # Remove processed samples from buffer while keeping some overlap
            # Keep half of the processed samples for better detection
            overlap = silero_vad.required_samples // 2
            audio_buffer = audio_buffer[silero_vad.required_samples - overlap:]
        else:
            # Not enough samples yet, skip processing
            continue
        
        # Track time info
        frame_time_ms = i * frame_duration_ms
        frame_time_sec = frame_time_ms / 1000
        
        # Update stats
        is_speech = result.get('is_speech', False)
        confidence = result.get('confidence', 0)
        
        if is_speech:
            speech_frames += 1
            
            # Track speech segments
            if current_segment is None:
                current_segment = {
                    'start': frame_time_sec, 
                    'confidence': confidence
                }
        elif current_segment is not None:
            # End of speech segment
            current_segment['end'] = frame_time_sec
            current_segment['duration'] = current_segment['end'] - current_segment['start']
            speech_segments.append(current_segment)
            current_segment = None
        
        process_time = (end_time - start_time) * 1000  # ms
        total_time += process_time
        
        # Print progress every 10%
        if i % max(1, max_frames_to_process // 10) == 0:
            progress = i / max_frames_to_process * 100
            
            print(f"Progress: {progress:.1f}% | Frame {i}/{max_frames_to_process} | "
                  f"Time: {frame_time_sec:.2f}s | Is speech: {is_speech} | "
                  f"Confidence: {confidence:.3f} | Process time: {process_time:.2f}ms")
    
    # Close the last segment if needed
    if current_segment is not None:
        current_segment['end'] = max_frames_to_process * frame_duration_ms / 1000
        current_segment['duration'] = current_segment['end'] - current_segment['start']
        speech_segments.append(current_segment)
    
    # Print stats
    print("\nSilero VAD Stats:")
    stats = silero_vad.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print(f"\nResults:")
    print(f"  Processed frames: {max_frames_to_process}")
    print(f"  Speech frames: {speech_frames} ({speech_frames/max_frames_to_process*100:.1f}%)")
    print(f"  Average processing time: {total_time/max_frames_to_process:.2f}ms per frame")
    
    print(f"\nDetected Speech Segments:")
    if not speech_segments:
        print("  No speech detected")
    else:
        for i, segment in enumerate(speech_segments):
            print(f"  Segment {i+1}: {segment['start']:.2f}s to {segment['end']:.2f}s "
                  f"({segment['duration']*1000:.0f}ms), confidence: {segment.get('confidence', 0):.3f}")
    
if __name__ == "__main__":
    main() 