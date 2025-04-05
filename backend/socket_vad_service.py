"""
Socket-based Voice Activity Detection (VAD) Service

This module provides a WebSocket interface for real-time audio processing
and voice activity detection. It integrates with AudioAnalysisService for
advanced audio analysis capabilities.
"""

import base64
import numpy as np
import time
import webrtcvad
import threading
import uuid
from typing import Dict, Any, Optional, List, Tuple
from audio_analysis_service import AudioAnalysisService, AudioAnalysisEvent
from dataclasses import dataclass
# Import Silero VAD service
from silero_vad_service import SileroVADService

# Default configuration
DEFAULT_SOCKET_VAD_CONFIG = {
    'sample_rate': 16000,  # WebRTC VAD requires 8000, 16000, 32000, or 48000 Hz
    'frame_duration_ms': 30,  # WebRTC VAD accepts 10, 20, or 30 ms
    'aggressiveness': 2,  # WebRTC VAD aggressiveness (0-3)
    'use_webrtc_vad': True,
    'use_rms_vad': True,
    'use_silero_vad': True,  # Enable Silero VAD by default
    'webrtc_weight': 0.4,  # Weight for WebRTC VAD result in ensemble
    'rms_weight': 0.2,  # Weight for RMS VAD result in ensemble
    'silero_weight': 0.4,  # Weight for Silero VAD result in ensemble
    'session_timeout_ms': 300000,  # 5 minutes
    'buffer_size': 1024,  # Buffer size for audio processing
    'debug': False
}

@dataclass
class AudioFrame:
    """Represents a frame of audio data for processing."""
    data: bytes
    rms_level: float
    timestamp: int
    is_speech_rms: bool = False
    is_speech_webrtc: bool = False
    is_speech_silero: bool = False  # Added Silero speech detection
    is_speech_ensemble: bool = False

class UserSession:
    """Manages a single user's VAD session and state."""
    
    def __init__(self, session_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a new user session with configuration.
        
        Args:
            session_id: Unique identifier for this session
            config: Configuration options, will be merged with defaults
        """
        self.session_id = session_id
        self.created_at = int(time.time() * 1000)
        self.last_activity = self.created_at
        self.config = DEFAULT_SOCKET_VAD_CONFIG.copy()
        if config:
            self.config.update(config)
        
        # Audio analysis service for RMS-based VAD
        self.audio_service = AudioAnalysisService({
            'debug': self.config['debug']
        })
        
        # WebRTC VAD if enabled
        self.webrtc_vad = None
        if self.config['use_webrtc_vad']:
            self.webrtc_vad = webrtcvad.Vad(self.config['aggressiveness'])
        
        # Silero VAD if enabled
        self.silero_vad = None
        if self.config['use_silero_vad']:
            self.silero_vad = SileroVADService({
                'debug': self.config['debug'],
                'sample_rate': self.config['sample_rate']
            })
        
        # Session state
        self.is_speaking = False
        self.speech_start_time = 0
        self.speech_end_time = 0
        self.frames: List[AudioFrame] = []
        self.max_frames = 100  # Keep last 100 frames for analysis
        
        # Debug stats
        self.total_frames = 0
        self.speech_frames = 0
        
        # Calculate frame size in bytes based on sample rate and frame duration
        bytes_per_sample = 2  # 16-bit audio = 2 bytes per sample
        self.frame_size = int(self.config['sample_rate'] * 
                             (self.config['frame_duration_ms'] / 1000.0) * 
                             bytes_per_sample)
                             
        if self.config['debug']:
            print(f"[UserSession] Created new session {session_id}")
            print(f"[UserSession] Frame size: {self.frame_size} bytes")
            if self.silero_vad:
                print(f"[UserSession] Silero VAD enabled")
    
    def is_expired(self) -> bool:
        """Check if this session has expired based on inactivity."""
        now = int(time.time() * 1000)
        return (now - self.last_activity) > self.config['session_timeout_ms']
    
    def update_activity(self) -> None:
        """Update the last activity timestamp."""
        self.last_activity = int(time.time() * 1000)
    
    def process_audio_chunk(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Process an incoming audio chunk and determine VAD status.
        
        Args:
            audio_data: Base64-encoded PCM audio data
            
        Returns:
            Dictionary with VAD results
        """
        self.update_activity()
        timestamp = int(time.time() * 1000)
        
        # Decode base64 audio data
        try:
            decoded_audio = base64.b64decode(audio_data)
        except Exception as e:
            if self.config['debug']:
                print(f"[UserSession] Error decoding audio: {e}")
            return {"error": "Invalid audio data format"}
        
        # Process the audio frame by frame
        results = []
        for i in range(0, len(decoded_audio), self.frame_size):
            if i + self.frame_size <= len(decoded_audio):
                frame_data = decoded_audio[i:i+self.frame_size]
                result = self._process_frame(frame_data, timestamp)
                results.append(result)
        
        # Determine overall speech state from the frame results
        if results:
            # Count speech frames
            speech_frames = sum(1 for r in results if r['is_speech'])
            speech_ratio = speech_frames / len(results)
            
            new_is_speaking = speech_ratio > 0.5  # More than half of frames have speech
            
            # Handle state transitions
            if new_is_speaking and not self.is_speaking:
                self.is_speaking = True
                self.speech_start_time = timestamp
                return {
                    "event": "speech_start",
                    "timestamp": timestamp,
                    "confidence": speech_ratio,
                    "session_id": self.session_id
                }
            elif not new_is_speaking and self.is_speaking:
                self.is_speaking = False
                self.speech_end_time = timestamp
                return {
                    "event": "speech_end",
                    "timestamp": timestamp,
                    "duration_ms": self.speech_end_time - self.speech_start_time,
                    "session_id": self.session_id
                }
        
        # Return regular update if no state change
        return {
            "event": "vad_update",
            "timestamp": timestamp,
            "is_speaking": self.is_speaking,
            "session_id": self.session_id
        }
    
    def _process_frame(self, frame_data: bytes, timestamp: int) -> Dict[str, Any]:
        """
        Process a single frame of audio.
        
        Args:
            frame_data: PCM audio data for a single frame
            timestamp: Current timestamp in milliseconds
            
        Returns:
            Frame processing results
        """
        self.total_frames += 1
        
        # Calculate RMS level for this frame
        pcm_data = np.frombuffer(frame_data, dtype=np.int16)
        rms_level = np.sqrt(np.mean(pcm_data.astype(np.float32) ** 2)) / 32768.0  # Normalize to 0-1
        
        # Process with AudioAnalysisService (RMS-based)
        rms_result = self.audio_service.add_audio_sample(rms_level, timestamp)
        is_speech_rms = rms_result['is_speech']
        
        # Process with WebRTC VAD if enabled
        is_speech_webrtc = False
        if self.webrtc_vad and len(frame_data) == self.frame_size:
            try:
                is_speech_webrtc = self.webrtc_vad.is_speech(frame_data, self.config['sample_rate'])
            except Exception as e:
                if self.config['debug']:
                    print(f"[UserSession] WebRTC VAD error: {e}")
        
        # Process with Silero VAD if enabled
        is_speech_silero = False
        silero_confidence = 0.0
        if self.silero_vad and len(frame_data) == self.frame_size:
            try:
                silero_result = self.silero_vad.process_audio(frame_data)
                is_speech_silero = silero_result['is_speech']
                silero_confidence = silero_result.get('confidence', 0.0)
            except Exception as e:
                if self.config['debug']:
                    print(f"[UserSession] Silero VAD error: {e}")
        
        # Combine results from all methods
        is_speech_ensemble = False
        ensemble_score = 0.0
        
        # Set up weights based on which VADs are enabled
        total_weight = 0
        weighted_sum = 0
        
        if self.config['use_rms_vad']:
            weighted_sum += is_speech_rms * self.config['rms_weight']
            total_weight += self.config['rms_weight']
            
        if self.config['use_webrtc_vad']:
            weighted_sum += is_speech_webrtc * self.config['webrtc_weight']
            total_weight += self.config['webrtc_weight']
            
        if self.config['use_silero_vad']:
            weighted_sum += is_speech_silero * self.config['silero_weight']
            total_weight += self.config['silero_weight']
        
        # Calculate ensemble score if any VAD is enabled
        if total_weight > 0:
            ensemble_score = weighted_sum / total_weight
            is_speech_ensemble = ensemble_score > 0.5
        else:
            # Fallback to RMS if no VAD is enabled
            is_speech_ensemble = is_speech_rms
        
        # Store frame info for debugging
        frame = AudioFrame(
            data=frame_data,
            rms_level=rms_level,
            timestamp=timestamp,
            is_speech_rms=is_speech_rms,
            is_speech_webrtc=is_speech_webrtc,
            is_speech_silero=is_speech_silero,
            is_speech_ensemble=is_speech_ensemble
        )
        
        if len(self.frames) >= self.max_frames:
            self.frames.pop(0)  # Remove oldest frame
        self.frames.append(frame)
        
        if is_speech_ensemble:
            self.speech_frames += 1
        
        # Return frame processing result
        return {
            "rms_level": rms_level,
            "is_speech_rms": is_speech_rms,
            "is_speech_webrtc": is_speech_webrtc,
            "is_speech_silero": is_speech_silero,
            "silero_confidence": silero_confidence,
            "is_speech": is_speech_ensemble,
            "ensemble_score": ensemble_score,
            "timestamp": timestamp
        }
    
    def get_noise_profile(self) -> Dict[str, Any]:
        """Get the current noise profile from the audio analysis service."""
        return self.audio_service.get_noise_profile()
    
    def force_recalibration(self) -> None:
        """Force recalibration of the audio analysis service."""
        self.audio_service.force_recalibration()
    
    def update_vad_config(self, config: Dict[str, Any]) -> None:
        """Update the VAD configuration."""
        # Update session config
        if config:
            self.config.update(config)
            
            # Update WebRTC VAD if aggressiveness changed
            if 'aggressiveness' in config and self.config['use_webrtc_vad']:
                self.webrtc_vad = webrtcvad.Vad(self.config['aggressiveness'])
                
            # Update Silero VAD if sample rate changed
            if 'sample_rate' in config and self.config['use_silero_vad']:
                self.silero_vad.update_config({
                    'sample_rate': config['sample_rate']
                })
                
            # Apply audio service config changes
            audio_service_config = {}
            if 'initial_sensitivity_factor' in config:
                audio_service_config['initial_sensitivity_factor'] = config['initial_sensitivity_factor']
            if 'debug' in config:
                audio_service_config['debug'] = config['debug']
                
            if audio_service_config:
                self.audio_service.update_config(audio_service_config)
                
            if 'recalibrate' in config and config['recalibrate']:
                self.force_recalibration()
    
    def get_debug_state(self) -> Dict[str, Any]:
        """Get debug state information."""
        audio_debug = self.audio_service.get_debug_state() or {}
        
        # Get Silero VAD stats if available
        silero_stats = {}
        if self.silero_vad:
            silero_stats = self.silero_vad.get_stats()
        
        # Return session state and audio analysis state
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "is_speaking": self.is_speaking,
            "total_frames": self.total_frames,
            "speech_frames": self.speech_frames,
            "speech_ratio": self.speech_frames / max(1, self.total_frames),
            "frame_size": self.frame_size,
            "config": self.config,
            "recent_frames": [
                {
                    "rms_level": f.rms_level,
                    "is_speech_rms": f.is_speech_rms,
                    "is_speech_webrtc": f.is_speech_webrtc,
                    "is_speech_silero": f.is_speech_silero,
                    "is_speech_ensemble": f.is_speech_ensemble,
                    "timestamp": f.timestamp
                }
                for f in self.frames[-5:] if self.frames
            ],
            "audio_analysis": audio_debug,
            "silero_vad": silero_stats
        }

class SocketVADService:
    """
    Service to manage WebSocket-based VAD sessions and processing.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Socket VAD Service."""
        self.sessions: Dict[str, UserSession] = {}
        self.config = DEFAULT_SOCKET_VAD_CONFIG.copy()
        if config:
            self.config.update(config)
        
        # Set up periodic cleanup of expired sessions
        self.cleanup_interval = 60  # seconds
        self.cleanup_timer = None
        self._start_cleanup_timer()
    
    def _start_cleanup_timer(self):
        """Start the timer for periodic cleanup of expired sessions."""
        self.cleanup_timer = threading.Timer(self.cleanup_interval, self._cleanup_expired_sessions)
        self.cleanup_timer.daemon = True
        self.cleanup_timer.start()
    
    def get_or_create_session(self, session_id: Optional[str] = None) -> Tuple[str, UserSession]:
        """
        Get an existing session by ID or create a new one.
        
        Args:
            session_id: Optional existing session ID
            
        Returns:
            Tuple of (session_id, session)
        """
        # Check if session exists and is valid
        if session_id and session_id in self.sessions:
            session = self.sessions[session_id]
            if not session.is_expired():
                session.update_activity()
                return session_id, session
        
        # Create new session
        new_session_id = session_id or str(uuid.uuid4())
        self.sessions[new_session_id] = UserSession(new_session_id, self.config)
        
        return new_session_id, self.sessions[new_session_id]
    
    def process_audio(self, session_id: str, audio_data: bytes) -> Dict[str, Any]:
        """
        Process audio data for a specific session.
        
        Args:
            session_id: Session ID to process for
            audio_data: Base64-encoded audio data
            
        Returns:
            Processing results
        """
        if session_id in self.sessions:
            session = self.sessions[session_id]
            return session.process_audio_chunk(audio_data)
        else:
            return {"error": f"Session {session_id} not found"}
    
    def _cleanup_expired_sessions(self) -> None:
        """Remove expired sessions and restart timer."""
        try:
            # Find expired sessions
            now = time.time()
            expired_sessions = [
                sid for sid, session in self.sessions.items()
                if session.is_expired()
            ]
            
            # Remove expired sessions
            for sid in expired_sessions:
                del self.sessions[sid]
                
            if expired_sessions and self.config['debug']:
                print(f"[SocketVADService] Cleaned up {len(expired_sessions)} expired sessions.")
                print(f"[SocketVADService] Active sessions: {len(self.sessions)}")
        except Exception as e:
            print(f"[SocketVADService] Error during session cleanup: {e}")
        finally:
            # Restart timer
            self._start_cleanup_timer()
    
    def get_session_count(self) -> int:
        """Get the current number of active sessions."""
        return len(self.sessions)
    
    def get_session(self, session_id: str) -> Optional[UserSession]:
        """Get a session by ID."""
        return self.sessions.get(session_id)
    
    def remove_session(self, session_id: str) -> bool:
        """Remove a session by ID."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

# Create a global instance for service-wide use
socket_vad_service = SocketVADService() 