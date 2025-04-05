"""
Test script for Silero VAD integration
"""

import time
import numpy as np
import wave
from silero_vad_service import SileroVADService

def load_test_audio(file_path):
    """Load audio from a WAV file."""
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
            
        return audio_np, sample_rate

def main():
    # Initialize Silero VAD
    print("Initializing Silero VAD...")
    silero_vad = SileroVADService({
        'debug': True,
        'sample_rate': 16000,
        'threshold': 0.5
    })
    
    # Load test audio
    print("\nLoading test audio...")
    test_file = "test_audio.wav"
    try:
        audio_np, sample_rate = load_test_audio(test_file)
    except Exception as e:
        print(f"Error loading audio: {e}")
        return
    
    # Process in small chunks to test buffering
    chunk_size = 160  # Very small chunks (10ms at 16kHz) to test buffering
    total_chunks = len(audio_np) // chunk_size
    
    print(f"\nProcessing {total_chunks} chunks of {chunk_size} samples...")
    print(f"Required samples: {silero_vad.required_samples}")
    
    # Stats
    speech_chunks = 0
    total_time = 0
    buffering_chunks = 0
    
    for i in range(total_chunks):
        chunk = audio_np[i * chunk_size:(i + 1) * chunk_size]
        
        # Convert to bytes for processing
        chunk_bytes = chunk.tobytes()
        
        # Process with Silero VAD
        start_time = time.time()
        result = silero_vad.process_audio(chunk_bytes)
        end_time = time.time()
        
        # Update stats
        if result.get('is_speech', False):
            speech_chunks += 1
        
        if result.get('buffering', False):
            buffering_chunks += 1
        
        process_time = (end_time - start_time) * 1000  # ms
        total_time += process_time
        
        # Print progress every 10%
        if i % max(1, total_chunks // 10) == 0 or 'buffering' in result:
            progress = i / total_chunks * 100
            buffer_info = ""
            if 'buffer_samples' in result:
                buffer_info = f"Buffer: {result['buffer_samples']} samples"
            
            if 'buffering' in result and result['buffering']:
                print(f"Progress: {progress:.1f}% | Chunk {i}/{total_chunks} | "
                      f"Buffering: {result.get('buffer_samples', 0)}/{result.get('required_samples', 0)} | "
                      f"Process time: {process_time:.2f}ms")
            else:
                print(f"Progress: {progress:.1f}% | Chunk {i}/{total_chunks} | "
                      f"Is speech: {result.get('is_speech', False)} | "
                      f"Confidence: {result.get('confidence', 0):.3f} | "
                      f"{buffer_info} | Process time: {process_time:.2f}ms")
    
    # Print stats
    print("\nSilero VAD Stats:")
    stats = silero_vad.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print(f"\nResults:")
    print(f"  Total chunks: {total_chunks}")
    print(f"  Speech chunks: {speech_chunks} ({speech_chunks/total_chunks*100:.1f}%)")
    print(f"  Buffering chunks: {buffering_chunks} ({buffering_chunks/total_chunks*100:.1f}%)")
    print(f"  Average processing time: {total_time/total_chunks:.2f}ms per chunk")
    
if __name__ == "__main__":
    main() 