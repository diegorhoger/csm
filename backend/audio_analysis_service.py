"""
Audio Analysis Service for Voice Activity Detection (VAD)

This module provides a standalone service for analyzing audio levels
to detect speech and silence, with adaptive thresholding based on
background noise levels.
"""

import time
import math
import statistics
from typing import Dict, List, Optional, Callable, Union, Any, Tuple

# Define event types
class AudioAnalysisEvent:
    """Event types that can be emitted by the AudioAnalysisService."""
    CALIBRATION_START = 'calibration-start'
    CALIBRATION_COMPLETE = 'calibration-complete'
    SPEECH_START = 'speech-start'
    SPEECH_END = 'speech-end'
    THRESHOLD_CHANGED = 'threshold-changed'

# Default configuration
DEFAULT_CONFIG = {
    'initial_sensitivity_factor': 1.5,
    'calibration_duration_ms': 2000,
    'recalibration_interval_ms': 5000,
    'silence_duration_for_recal_ms': 2000,
    'max_sample_history': 50,
    'smoothing_factor': 0.1,
    'consecutive_frames_threshold': 2,
    'debug': False
}

class AudioAnalysisService:
    """
    A standalone service for audio level analysis and speech detection
    with adaptive thresholding.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the AudioAnalysisService with optional configuration.
        
        Args:
            config: Configuration options to override defaults
        """
        # Apply configuration with defaults
        self._config = DEFAULT_CONFIG.copy()
        if config:
            self._config.update(config)
        
        # Internal state
        self._samples = []
        self._noise_floor = 0.0
        self._std_dev = 0.0
        self._sensitivity_factor = self._config['initial_sensitivity_factor']
        self._last_calibration_time = 0
        self._calibration_complete = False
        self._is_calibrating = True
        self._last_is_speech = False
        self._consecutive_speech_frames = 0
        self._consecutive_silence_frames = 0
        self._last_speech_time = 0
        self._last_silence_time = 0
        
        # Event system
        self._event_listeners = {
            AudioAnalysisEvent.CALIBRATION_START: [],
            AudioAnalysisEvent.CALIBRATION_COMPLETE: [],
            AudioAnalysisEvent.SPEECH_START: [],
            AudioAnalysisEvent.SPEECH_END: [],
            AudioAnalysisEvent.THRESHOLD_CHANGED: []
        }
        
        # Start initial calibration
        self._start_calibration()
    
    def _start_calibration(self) -> None:
        """Start the calibration process."""
        self._is_calibrating = True
        self._calibration_complete = False
        self._samples = []
        self._last_calibration_time = int(time.time() * 1000)  # Current time in ms
        
        self._emit_event(AudioAnalysisEvent.CALIBRATION_START)
        
        if self._config['debug']:
            print(f"[AudioAnalysisService] Starting calibration")
    
    def _complete_calibration(self) -> None:
        """Complete the calibration process using collected samples."""
        if len(self._samples) >= 5:
            self._noise_floor = statistics.mean(self._samples)
            self._std_dev = statistics.stdev(self._samples) if len(self._samples) > 1 else 0.01
        else:
            # Not enough samples, use default values
            self._noise_floor = 0.02
            self._std_dev = 0.01
        
        self._is_calibrating = False
        self._calibration_complete = True
        
        if self._config['debug']:
            print(f"[AudioAnalysisService] Calibration complete:")
            print(f"  Noise floor: {self._noise_floor:.4f}")
            print(f"  Standard deviation: {self._std_dev:.4f}")
            print(f"  Dynamic threshold: {self.get_current_threshold():.4f}")
        
        self._emit_event(
            AudioAnalysisEvent.CALIBRATION_COMPLETE,
            self.get_noise_profile()
        )
    
    def add_audio_sample(self, level: float, timestamp: Optional[int] = None) -> Dict[str, Any]:
        """
        Add a new audio level sample for analysis.
        
        Args:
            level: Audio level (0-1 range)
            timestamp: Optional timestamp in ms (defaults to current time)
            
        Returns:
            Analysis result
        """
        # Use current time if timestamp not provided
        if timestamp is None:
            timestamp = int(time.time() * 1000)
        
        # During calibration phase, collect samples
        if self._is_calibrating:
            self._samples.append(level)
            
            # Check if calibration duration has elapsed
            elapsed = timestamp - self._last_calibration_time
            if elapsed >= self._config['calibration_duration_ms']:
                self._complete_calibration()
                
            # Return early during calibration
            return {
                'level': level,
                'threshold': 0,
                'is_speech': False,
                'profile': self.get_noise_profile(),
                'timestamp': timestamp
            }
        
        # Add sample to history
        self._samples.append(level)
        if len(self._samples) > self._config['max_sample_history']:
            self._samples.pop(0)  # Remove oldest sample
        
        # Get current threshold
        threshold = self.get_current_threshold()
        
        # Determine if this is speech
        is_speech = level > threshold
        
        # Track consecutive frames
        if is_speech:
            self._consecutive_speech_frames += 1
            self._consecutive_silence_frames = 0
            self._last_speech_time = timestamp
        else:
            self._consecutive_speech_frames = 0
            self._consecutive_silence_frames += 1
            self._last_silence_time = timestamp
        
        # Require consecutive frames to confirm state change
        confirmed_is_speech = self._consecutive_speech_frames >= self._config['consecutive_frames_threshold']
        
        # Detect state transitions
        if confirmed_is_speech and not self._last_is_speech:
            self._last_is_speech = True
            result = {
                'level': level,
                'threshold': threshold,
                'is_speech': True,
                'profile': self.get_noise_profile(),
                'timestamp': timestamp
            }
            self._emit_event(AudioAnalysisEvent.SPEECH_START, result)
            return result
            
        elif not is_speech and self._last_is_speech and \
             self._consecutive_silence_frames >= self._config['consecutive_frames_threshold']:
            self._last_is_speech = False
            result = {
                'level': level,
                'threshold': threshold,
                'is_speech': False,
                'profile': self.get_noise_profile(),
                'timestamp': timestamp
            }
            self._emit_event(AudioAnalysisEvent.SPEECH_END, result)
            return result
        
        # Check for recalibration opportunity after extended silence
        silence_duration = timestamp - self._last_speech_time
        if not is_speech and \
           silence_duration > self._config['silence_duration_for_recal_ms'] and \
           (timestamp - self._last_calibration_time) > self._config['recalibration_interval_ms']:
            self._recalibrate_from_recent_silence()
        
        # Return regular update
        return {
            'level': level,
            'threshold': threshold,
            'is_speech': self._last_is_speech,
            'profile': self.get_noise_profile(),
            'timestamp': timestamp
        }
    
    def _recalibrate_from_recent_silence(self) -> None:
        """Recalibrate using recent silence samples."""
        # Use only the last N silence samples for recalibration
        silence_samples = self._samples[-min(10, len(self._samples)):]
        
        # Calculate new noise floor from silent samples
        if silence_samples:
            old_floor = self._noise_floor
            
            # Apply smoothing to avoid abrupt changes
            new_floor = statistics.mean(silence_samples)
            self._noise_floor = (old_floor * (1 - self._config['smoothing_factor']) + 
                                new_floor * self._config['smoothing_factor'])
            
            self._std_dev = statistics.stdev(silence_samples) if len(silence_samples) > 1 else self._std_dev
            
            self._last_calibration_time = int(time.time() * 1000)
            
            if self._config['debug'] and abs(old_floor - self._noise_floor) > 0.005:
                print(f"[AudioAnalysisService] Recalibrated noise floor: {old_floor:.4f} → {self._noise_floor:.4f}")
            
            self._adjust_sensitivity_factor()
    
    def _adjust_sensitivity_factor(self) -> None:
        """Dynamically adjust sensitivity factor based on signal conditions."""
        # If std_dev is very low (stable background), reduce sensitivity
        if self._std_dev < 0.01:
            new_factor = min(2.5, self._sensitivity_factor * 1.1)
        # If std_dev is high (variable background), increase sensitivity
        elif self._std_dev > 0.1:
            new_factor = max(1.2, self._sensitivity_factor * 0.9)
        else:
            return
            
        if abs(new_factor - self._sensitivity_factor) > 0.1:
            self._sensitivity_factor = new_factor
            if self._config['debug']:
                print(f"[AudioAnalysisService] Adjusted sensitivity factor: {self._sensitivity_factor:.2f}")
            
            self._emit_event(AudioAnalysisEvent.THRESHOLD_CHANGED, {
                'threshold': self.get_current_threshold(),
                'sensitivity_factor': self._sensitivity_factor
            })
    
    def get_current_threshold(self) -> float:
        """Get the current speech detection threshold."""
        if not self._calibration_complete:
            return 0.1  # Default threshold during calibration
        
        # Dynamic threshold based on noise floor and standard deviation
        return self._noise_floor + (self._std_dev * self._sensitivity_factor)
    
    def get_noise_profile(self) -> Dict[str, Any]:
        """Get the current noise profile information."""
        return {
            'noise_floor': self._noise_floor,
            'std_dev': self._std_dev,
            'sensitivity_factor': self._sensitivity_factor,
            'threshold': self.get_current_threshold(),
            'calibration_complete': self._calibration_complete,
            'last_calibration_time': self._last_calibration_time,
            'samples_count': len(self._samples),
            'recent_levels': self._samples[-5:] if len(self._samples) >= 5 else self._samples
        }
    
    def is_speech_detected(self, level: Optional[float] = None) -> bool:
        """
        Check if speech is detected at the given level.
        
        Args:
            level: Audio level to test, or None to use current speech state
            
        Returns:
            True if speech is detected, False otherwise
        """
        if level is None:
            return self._last_is_speech
            
        return level > self.get_current_threshold()
    
    def is_calibrating(self) -> bool:
        """Check if the service is currently calibrating."""
        return self._is_calibrating
    
    # Event system methods
    
    def force_recalibration(self) -> None:
        """Force a recalibration of the audio analysis service."""
        self._start_calibration()
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """Update configuration parameters."""
        self._config.update(config)
        
        # Apply special parameters that need immediate effect
        if 'initial_sensitivity_factor' in config:
            self._sensitivity_factor = config['initial_sensitivity_factor']
    
    def add_event_listener(self, event: str, callback: Callable) -> None:
        """Add an event listener for the specified event."""
        if event in self._event_listeners:
            self._event_listeners[event].append(callback)
        else:
            raise ValueError(f"Unknown event type: {event}")
    
    def remove_event_listener(self, event: str, callback: Callable) -> None:
        """Remove an event listener for the specified event."""
        if event in self._event_listeners:
            if callback in self._event_listeners[event]:
                self._event_listeners[event].remove(callback)
        else:
            raise ValueError(f"Unknown event type: {event}")
    
    def _emit_event(self, event: str, data=None) -> None:
        """Emit an event to all registered listeners."""
        if event in self._event_listeners:
            for callback in self._event_listeners[event]:
                try:
                    callback(event, data)
                except Exception as e:
                    if self._config['debug']:
                        print(f"[AudioAnalysisService] Error in event listener: {e}")
    
    def get_debug_state(self) -> Optional[Dict[str, Any]]:
        """Get debug state information for troubleshooting."""
        if not self._config['debug']:
            return None
            
        return {
            'calibration_complete': self._calibration_complete,
            'is_calibrating': self._is_calibrating,
            'samples_count': len(self._samples),
            'noise_floor': self._noise_floor,
            'std_dev': self._std_dev,
            'sensitivity_factor': self._sensitivity_factor,
            'threshold': self.get_current_threshold(),
            'last_calibration_time': self._last_calibration_time,
            'last_speech_time': self._last_speech_time,
            'last_silence_time': self._last_silence_time,
            'last_is_speech': self._last_is_speech,
            'consecutive_speech_frames': self._consecutive_speech_frames,
            'consecutive_silence_frames': self._consecutive_silence_frames,
            'recent_samples': self._samples[-10:] if len(self._samples) >= 10 else self._samples
        }

def calculate_rms(samples: List[float]) -> float:
    """Calculate Root Mean Square of a list of samples."""
    if not samples:
        return 0.0
    return math.sqrt(sum(x * x for x in samples) / len(samples))

# Create a global instance for service-wide use
audio_analysis_service = AudioAnalysisService() 