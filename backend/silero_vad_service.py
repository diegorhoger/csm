"""
Silero Voice Activity Detection (VAD) Service

This module provides integration with the Silero VAD model for improved
voice activity detection. It complements the existing VAD systems by
providing deep learning-based speech detection capabilities.

References:
- Silero VAD: https://github.com/snakers4/silero-vad
"""

import os
import torch
import numpy as np
import time
from typing import Dict, Any, Optional, List, Tuple, Union
import warnings
from dataclasses import dataclass

# Default configuration
DEFAULT_SILERO_VAD_CONFIG = {
    'sample_rate': 16000,  # Silero works with 8000, 16000 Hz
    'use_onnx': False,     # Whether to use ONNX version (faster but less accurate)
    'threshold': 0.5,      # Default threshold for voice detection
    'min_speech_duration_ms': 250,  # Minimum speech segment duration
    'min_silence_duration_ms': 100, # Minimum silence segment duration
    'window_size_samples': 512,     # Number of samples per window (must be 512 for 16kHz)
    'speech_pad_ms': 30,            # Additional padding
    'device': 'cpu',               # Device to run the model on ('cpu' or 'cuda')
    'model_path': 'models/silero_vad',  # Local path to save the model
    'cache_model': True,           # Whether to cache the model in memory
    'debug': False                 # Debug mode
}

class SileroVADService:
    """
    Service for voice activity detection using Silero VAD model.
    Implemented as a singleton to ensure model is loaded only once.
    """
    _instance = None
    
    def __new__(cls, config: Optional[Dict[str, Any]] = None):
        if cls._instance is None:
            cls._instance = super(SileroVADService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if self._initialized:
            return
            
        self.config = DEFAULT_SILERO_VAD_CONFIG.copy()
        if config:
            self.config.update(config)
            
        self._initialized = True
        self.model = None
        self.get_speech_timestamps = None
        self.vad_iterator = None
        self.model_loaded = False
        
        # Audio buffer for small chunks
        self.audio_buffer = np.array([], dtype=np.float32)
        
        # The model requires exactly 512 samples for 16kHz (or 256 for 8kHz)
        self.required_samples = 512 if self.config['sample_rate'] == 16000 else 256
        
        # Stats
        self.total_predictions = 0
        self.positive_predictions = 0
        self.load_time_ms = 0
        self.avg_inference_time_ms = 0
        
        # Load model if cache is enabled
        if self.config['cache_model']:
            self._load_model()
    
    def _load_model(self) -> bool:
        """
        Load the Silero VAD model.
        
        Returns:
            bool: True if model loaded successfully, False otherwise
        """
        start_time = time.time()
        
        try:
            # Create model directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config['model_path']), exist_ok=True)
            
            # Suppress warnings during model loading
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                if self.config['use_onnx']:
                    # ONNX implementation (not implemented in this version)
                    raise NotImplementedError("ONNX support not implemented yet")
                else:
                    # PyTorch implementation
                    result = torch.hub.load(
                        repo_or_dir='snakers4/silero-vad',
                        model='silero_vad',
                        force_reload=False,
                        onnx=False,
                        verbose=self.config['debug']
                    )
                    
                    # Unpack model and utils
                    if isinstance(result, tuple) and len(result) == 2:
                        # Standard format: (model, utils)
                        model, utils = result
                        
                        # Unpack utils
                        if isinstance(utils, tuple) and len(utils) == 5:
                            (self.get_speech_timestamps, 
                             save_audio,
                             read_audio,
                             self.vad_iterator,
                             _) = utils
                        else:
                            raise ValueError(f"Unexpected utils format: {utils}")
                    else:
                        raise ValueError(f"Unexpected result format: {result}")
                        
                    # Move model to specified device
                    self.model = model.to(self.config['device'])
                    
                    # Set model to evaluation mode
                    self.model.eval()
            
            self.model_loaded = True
            self.load_time_ms = (time.time() - start_time) * 1000
            
            if self.config['debug']:
                print(f"[SileroVAD] Model loaded in {self.load_time_ms:.2f}ms on {self.config['device']}")
            
            return True
            
        except Exception as e:
            if self.config['debug']:
                print(f"[SileroVAD] Error loading model: {e}")
            self.model_loaded = False
            return False
    
    def ensure_model_loaded(self) -> bool:
        """
        Ensure the model is loaded before inference.
        
        Returns:
            bool: True if model is loaded, False otherwise
        """
        if not self.model_loaded:
            return self._load_model()
        return True
    
    def _add_to_buffer(self, audio_np: np.ndarray) -> np.ndarray:
        """
        Add audio to the buffer and return the combined buffer.
        
        Args:
            audio_np: Audio data as numpy array
            
        Returns:
            Combined audio buffer
        """
        # Append to buffer
        self.audio_buffer = np.concatenate([self.audio_buffer, audio_np])
        
        # Return copy of current buffer
        return self.audio_buffer.copy()
    
    def _trim_buffer(self, used_samples: int) -> None:
        """
        Trim the buffer after processing.
        
        Args:
            used_samples: Number of samples that were used
        """
        if used_samples >= len(self.audio_buffer):
            # If all samples were used, clear the buffer
            self.audio_buffer = np.array([], dtype=np.float32)
        else:
            # Keep the unused samples
            self.audio_buffer = self.audio_buffer[used_samples:]
    
    def _prepare_exact_size_input(self, audio_np: np.ndarray) -> Tuple[np.ndarray, int]:
        """
        Prepare input of exact size required by the model.
        
        Args:
            audio_np: Audio data as numpy array
            
        Returns:
            Tuple of (prepared audio array, samples used)
        """
        # Get the required number of samples
        if len(audio_np) < self.required_samples:
            # Not enough samples, pad with zeros
            padding = np.zeros(self.required_samples - len(audio_np), dtype=np.float32)
            prepared = np.concatenate([audio_np, padding])
            samples_used = len(audio_np)  # We used all available samples
        else:
            # Take exactly the required number of samples
            prepared = audio_np[:self.required_samples]
            samples_used = self.required_samples
            
        return prepared, samples_used
    
    def process_audio(self, audio_data: Union[bytes, np.ndarray]) -> Dict[str, Any]:
        """
        Process an audio chunk to detect speech.
        
        Args:
            audio_data: Audio data as bytes or numpy array
            
        Returns:
            Dict with detection results and stats
        """
        # Track prediction stats
        self.total_predictions += 1
        
        # Ensure model is loaded
        if not self.ensure_model_loaded():
            return {
                'error': 'Model not loaded',
                'is_speech': False,
                'confidence': 0.0
            }
            
        start_time = time.time()
        
        try:
            # Convert bytes to numpy array if needed
            if isinstance(audio_data, bytes):
                audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0  # Normalize to [-1, 1]
            else:
                audio_np = audio_data.astype(np.float32)
            
            # Add to buffer
            combined_audio = self._add_to_buffer(audio_np)
            
            # Check if we have enough audio data
            if len(combined_audio) < self.required_samples:
                # Not enough data yet, return default confidence
                return {
                    'is_speech': False,
                    'confidence': 0.0,
                    'buffering': True,
                    'buffer_samples': len(combined_audio),
                    'required_samples': self.required_samples
                }
            
            # Prepare exact size input
            processed_audio, samples_used = self._prepare_exact_size_input(combined_audio)
                
            # Convert to torch tensor
            tensor = torch.tensor(processed_audio)
            
            # Ensure the tensor is on the correct device
            tensor = tensor.to(self.config['device'])
            
            # Get speech probabilities
            with torch.no_grad():
                speech_probs = self.model(tensor, self.config['sample_rate'])
                
            # Get confidence score (mean of speech probabilities)
            confidence = float(speech_probs.mean().item())
            
            # Determine if speech based on threshold
            is_speech = confidence > self.config['threshold']
            
            # Track positive predictions
            if is_speech:
                self.positive_predictions += 1
            
            # Trim the buffer - keep some overlap for continuity
            half_buffer = samples_used // 2
            self._trim_buffer(half_buffer)
                
            # Calculate average inference time
            inference_time_ms = (time.time() - start_time) * 1000
            self.avg_inference_time_ms = (
                (self.avg_inference_time_ms * (self.total_predictions - 1) + inference_time_ms) / 
                self.total_predictions
            )
            
            return {
                'is_speech': is_speech,
                'confidence': confidence,
                'inference_time_ms': inference_time_ms,
                'buffer_samples': len(self.audio_buffer)
            }
            
        except Exception as e:
            if self.config['debug']:
                print(f"[SileroVAD] Error processing audio: {e}")
            return {
                'error': str(e),
                'is_speech': False,
                'confidence': 0.0
            }
    
    def get_speech_timestamps_from_buffer(self, audio_buffer: np.ndarray) -> List[Dict[str, int]]:
        """
        Get exact speech timestamps from an audio buffer.
        
        Args:
            audio_buffer: Audio buffer as numpy array
            
        Returns:
            List of speech segments with start and end sample indices
        """
        if not self.ensure_model_loaded():
            return []
            
        try:
            # Check if buffer is large enough
            if len(audio_buffer) < self.required_samples:
                return []
            
            # Make sure buffer length is a multiple of required_samples
            remainder = len(audio_buffer) % self.required_samples
            if remainder > 0:
                # Pad with zeros to reach exact multiple
                padding = np.zeros(self.required_samples - remainder, dtype=np.float32)
                audio_buffer = np.concatenate([audio_buffer, padding])
                
            # Convert to torch tensor
            tensor = torch.tensor(audio_buffer)
            
            # Ensure the tensor is on the correct device
            tensor = tensor.to(self.config['device'])
            
            # Get speech timestamps
            speech_timestamps = self.get_speech_timestamps(
                tensor,
                self.model,
                threshold=self.config['threshold'],
                sampling_rate=self.config['sample_rate'],
                min_speech_duration_ms=self.config['min_speech_duration_ms'],
                min_silence_duration_ms=self.config['min_silence_duration_ms'],
                window_size_samples=self.config['window_size_samples'],
                speech_pad_ms=self.config['speech_pad_ms'],
                return_seconds=False
            )
            
            return speech_timestamps
            
        except Exception as e:
            if self.config['debug']:
                print(f"[SileroVAD] Error getting speech timestamps: {e}")
            return []
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update the configuration."""
        if new_config:
            old_sample_rate = self.config.get('sample_rate', 16000)
            self.config.update(new_config)
            
            # Update required_samples if sample rate changes
            new_sample_rate = self.config.get('sample_rate', 16000)
            if old_sample_rate != new_sample_rate:
                self.required_samples = 512 if new_sample_rate == 16000 else 256
                self.audio_buffer = np.array([], dtype=np.float32)  # Clear buffer on sample rate change
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the VAD service."""
        positive_rate = (
            (self.positive_predictions / self.total_predictions * 100) 
            if self.total_predictions > 0 else 0
        )
        
        return {
            'total_predictions': self.total_predictions,
            'positive_predictions': self.positive_predictions,
            'positive_rate': positive_rate,
            'load_time_ms': self.load_time_ms,
            'avg_inference_time_ms': self.avg_inference_time_ms,
            'model_loaded': self.model_loaded,
            'device': self.config['device'],
            'threshold': self.config['threshold'],
            'buffer_size': len(self.audio_buffer),
            'required_samples': self.required_samples
        } 