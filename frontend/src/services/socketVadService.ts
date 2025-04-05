/**
 * Socket-based Voice Activity Detection (VAD) Service
 * 
 * This service manages WebSocket connections to the backend VAD service,
 * handling audio streaming, speech detection events, and configuration.
 */

import { io, Socket } from 'socket.io-client';
import { API_ENDPOINTS } from '../constants/app';

// Event types
export enum SocketVadEvent {
  CONNECTED = 'connected',
  VAD_INITIALIZED = 'vad_initialized',
  VAD_RESULT = 'vad_result',
  SPEECH_START = 'speech_start',
  SPEECH_END = 'speech_end',
  CALIBRATION_STARTED = 'calibration_started',
  CALIBRATION_COMPLETE = 'calibration_complete',
  CONFIG_UPDATED = 'config_updated',
  DEBUG_STATE = 'debug_state',
  DEBUG_RESPONSE = 'debug_response',
  ERROR = 'error'
}

// Types for event data
export interface NoiseProfile {
  noiseFloor: number;
  stdDev: number;
  samples: number[];
  sensitivityFactor: number;
  lastCalibrationTime: number;
  calibrationComplete: boolean;
}

export interface DebugResponseData {
  server_time: number;
  sid: string;
  origin: string;
  transport: string;
  async_mode: string;
  active_sessions: number;
}

export interface VadResult {
  is_speech: boolean;
  rms_level: number;
  threshold: number;
  timestamp: number;
  session_id: string;
}

export interface SpeechStartEvent {
  event: 'speech_start';
  timestamp: number;
  confidence: number;
  session_id: string;
}

export interface SpeechEndEvent {
  event: 'speech_end';
  timestamp: number;
  duration_ms: number;
  session_id: string;
}

export interface CalibrationStartedEvent {
  session_id: string;
  timestamp: number;
}

export interface CalibrationCompleteEvent {
  session_id: string;
  noise_profile: NoiseProfile;
}

export interface ConfigUpdatedEvent {
  session_id: string;
  config: Record<string, unknown>;
}

export interface ErrorEvent {
  message: string;
}

export interface VadConfig {
  debug?: boolean;
  sample_rate?: number;
  frame_duration_ms?: number;
  use_webrtc_vad?: boolean;
  use_rms_vad?: boolean;
  aggressiveness?: number;
  webrtc_weight?: number;
  rms_weight?: number;
  rms_vad_config?: {
    initial_sensitivity_factor?: number;
    calibration_duration_ms?: number;
    recalibration_interval_ms?: number;
    silence_duration_for_recal_ms?: number;
    consecutive_frames_threshold?: number;
  };
}

export interface VadInitializedEvent {
  session_id: string;
  noise_profile: NoiseProfile;
  config: VadConfig;
}

// Type for event handlers
type EventHandler<T> = (data: T) => void;

class SocketVadService {
  private socket: Socket | null = null;
  private sessionId: string | null = null;
  private eventHandlers: Map<string, Set<EventHandler<unknown>>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second
  private autoReconnect = true;
  private audioChunkSize = 4096; // Size of audio chunks to send
  private isConnected = false;
  private isSpeaking = false;
  private debug = false;
  private connectionStartTime = 0;

  /**
   * Connect to the WebSocket server
   */
  async connect(): Promise<boolean> {
    if (this.socket) {
      console.log('[SocketVAD] Already connected');
      return true;
    }

    try {
      this.connectionStartTime = Date.now();
      const socketUrl = API_ENDPOINTS.socketVadUrl;
      console.log(`[SocketVAD] Connecting to ${socketUrl}`);

      // Add verbose debugging for network issues
      console.log('[SocketVAD] Current API endpoints:', {
        baseUrl: API_ENDPOINTS.baseUrl,
        socketVadUrl: API_ENDPOINTS.socketVadUrl
      });

      // Test the server connectivity first with a simple fetch
      try {
        const healthResponse = await fetch(`${API_ENDPOINTS.baseUrl}/api/health`, { 
          method: 'GET',
          headers: { 'Content-Type': 'application/json' }
        });
        
        if (healthResponse.ok) {
          const healthData = await healthResponse.json();
          console.log('[SocketVAD] Health check successful:', healthData);
        } else {
          console.warn('[SocketVAD] Health check failed, status:', healthResponse.status);
        }
      } catch (healthError) {
        console.error('[SocketVAD] Health check error:', healthError);
        // Continue anyway since the WebSocket might still work
      }

      // Try polling first to confirm connection works
      try {
        console.log('[SocketVAD] Testing basic Socket.IO connection with polling');
        const testConnection = await fetch(`${API_ENDPOINTS.socketVadUrl}/socket.io/?EIO=4&transport=polling`);
        const testResult = await testConnection.text();
        console.log('[SocketVAD] Socket.IO polling test:', testResult ? 'Success' : 'Failed');
      } catch (pollError) {
        console.error('[SocketVAD] Polling test failed:', pollError);
      }

      // Configure Socket.IO options
      const socketOptions = {
        transports: ['polling', 'websocket'], // Start with polling first to establish connection
        reconnection: this.autoReconnect,
        reconnectionAttempts: this.maxReconnectAttempts,
        reconnectionDelay: this.reconnectDelay,
        reconnectionDelayMax: 5000,
        path: '/socket.io/',  // Explicitly specify the Socket.IO path
        forceNew: true,       // Force a new connection
        timeout: 20000,       // Increase timeout to 20 seconds for slow connections
        extraHeaders: {       // Add extra headers for debugging
          'X-Client-Version': '1.0.0',
          'X-Connection-Time': new Date().toISOString()
        }
      };
      
      console.log('[SocketVAD] Connecting with options:', socketOptions);
      this.socket = io(socketUrl, socketOptions);

      // Set up event listeners
      this.setupSocketEvents();

      return new Promise((resolve) => {
        // Set a timeout for connection
        const timeout = setTimeout(() => {
          console.error('[SocketVAD] Connection timeout after 15 seconds');
          if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
          }
          resolve(false);
        }, 15000);

        // Listen for connection success
        this.once(SocketVadEvent.CONNECTED, () => {
          clearTimeout(timeout);
          this.isConnected = true;
          const connectionTime = Date.now() - this.connectionStartTime;
          console.log(`[SocketVAD] Connected successfully in ${connectionTime}ms`);
          
          // Log transport being used
          if (this.socket && this.socket.io && this.socket.io.engine) {
            const transportName = this.socket.io.engine.transport.name as string;
            console.log(`[SocketVAD] Using transport: ${transportName}`);
          }
          
          // Run a diagnostic test
          this.runConnectionDiagnostic();
          
          resolve(true);
        });

        // Listen for connection error
        this.socket!.on('connect_error', (err) => {
          console.error(`[SocketVAD] Connection error: ${err.message}`);
          console.error('[SocketVAD] Connection details:', {
            url: socketUrl,
            transportOptions: this.socket?.io?.opts?.transports,
            reconnection: this.autoReconnect,
            attempts: this.reconnectAttempts
          });
          
          clearTimeout(timeout);
          resolve(false);
        });
      });
    } catch (error) {
      console.error('[SocketVAD] Error connecting:', error);
      return false;
    }
  }

  /**
   * Run a connection diagnostic test
   */
  async runConnectionDiagnostic(): Promise<void> {
    if (!this.socket || !this.isConnected) {
      console.error('[SocketVAD] Cannot run diagnostic - not connected');
      return;
    }

    try {
      console.log('[SocketVAD] Running connection diagnostic');
      
      // Send a debug connection event
      this.socket.emit('debug_connection', {
        clientTime: Date.now(),
        userAgent: navigator.userAgent,
        url: window.location.href,
        socketId: this.socket.id,
        transportType: this.socket.io.engine.transport.name
      });
      
      // Set up a handler for the response
      this.once(SocketVadEvent.DEBUG_RESPONSE, (data: DebugResponseData) => {
        console.log('[SocketVAD] Debug diagnostic results:', data);
        
        // Calculate round-trip time
        const rtt = Date.now() - data.server_time;
        console.log(`[SocketVAD] WebSocket RTT: ${rtt}ms`);
        
        if (rtt > 500) {
          console.warn('[SocketVAD] High latency detected');
        }
      });
    } catch (error) {
      console.error('[SocketVAD] Error running diagnostic:', error);
    }
  }

  /**
   * Setup socket event handlers
   */
  private setupSocketEvents(): void {
    if (!this.socket) return;

    // Basic Socket.IO events
    this.socket.on('connect', () => {
      console.log(`[SocketVAD] Connected, socket ID: ${this.socket?.id}`);
      this.isConnected = true;
      this.reconnectAttempts = 0;
    });

    this.socket.on('disconnect', (reason) => {
      console.log(`[SocketVAD] Disconnected: ${reason}`);
      this.isConnected = false;
      
      // Handle various disconnect reasons
      if (reason === 'io server disconnect') {
        // Server disconnected us, need to reconnect manually
        if (this.autoReconnect) {
          this.reconnect();
        }
      }
    });

    // Custom VAD events
    this.socket.on(SocketVadEvent.CONNECTED, (data) => {
      console.log('[SocketVAD] Received connected event:', data);
      this.emit(SocketVadEvent.CONNECTED, data);
    });

    this.socket.on(SocketVadEvent.VAD_INITIALIZED, (data) => {
      console.log('[SocketVAD] VAD initialized:', data);
      if (data && data.session_id) {
        this.sessionId = data.session_id;
      }
      this.emit(SocketVadEvent.VAD_INITIALIZED, data);
    });

    this.socket.on(SocketVadEvent.VAD_RESULT, (data) => {
      if (this.debug) {
        console.log('[SocketVAD] VAD result:', data);
      }
      this.emit(SocketVadEvent.VAD_RESULT, data);
    });

    this.socket.on(SocketVadEvent.SPEECH_START, (data) => {
      console.log('[SocketVAD] Received speech_start:', data);
      this.isSpeaking = true;
      this.emit(SocketVadEvent.SPEECH_START, data);
    });

    this.socket.on(SocketVadEvent.SPEECH_END, (data) => {
      console.log('[SocketVAD] Received speech_end:', data);
      this.isSpeaking = false;
      this.emit(SocketVadEvent.SPEECH_END, data);
    });

    this.socket.on(SocketVadEvent.CALIBRATION_STARTED, (data) => {
      console.log('[SocketVAD] Calibration started:', data);
      this.emit(SocketVadEvent.CALIBRATION_STARTED, data);
    });

    this.socket.on(SocketVadEvent.CALIBRATION_COMPLETE, (data) => {
      console.log('[SocketVAD] Calibration complete:', data);
      this.emit(SocketVadEvent.CALIBRATION_COMPLETE, data);
    });

    this.socket.on(SocketVadEvent.CONFIG_UPDATED, (data) => {
      console.log('[SocketVAD] Config updated:', data);
      this.emit(SocketVadEvent.CONFIG_UPDATED, data);
    });

    this.socket.on(SocketVadEvent.DEBUG_RESPONSE, (data) => {
      console.log('[SocketVAD] Debug response:', data);
      this.emit(SocketVadEvent.DEBUG_RESPONSE, data);
    });

    this.socket.on(SocketVadEvent.ERROR, (data) => {
      console.error('[SocketVAD] Error from server:', data);
      this.emit(SocketVadEvent.ERROR, data);
    });

    // Connection error events
    this.socket.on('connect_error', (error) => {
      console.error('[SocketVAD] Connection error:', error.message);
    });

    this.socket.on('connect_timeout', () => {
      console.error('[SocketVAD] Connection timeout');
    });

    this.socket.on('reconnect', (attemptNumber) => {
      console.log(`[SocketVAD] Reconnected after ${attemptNumber} attempts`);
      this.isConnected = true;
    });

    this.socket.on('reconnect_attempt', (attemptNumber) => {
      console.log(`[SocketVAD] Reconnect attempt ${attemptNumber}`);
    });

    this.socket.on('reconnect_error', (error) => {
      console.error('[SocketVAD] Reconnection error:', error.message);
    });

    this.socket.on('reconnect_failed', () => {
      console.error('[SocketVAD] Failed to reconnect after maximum attempts');
      this.isConnected = false;
    });

    // Add a general error handler
    this.socket.on('error', (error) => {
      console.error('[SocketVAD] Socket error:', error);
    });
  }

  /**
   * Initialize a VAD session
   */
  async initVad(existingSessionId?: string): Promise<string | null> {
    if (!this.socket || !this.isConnected) {
      const connected = await this.connect();
      if (!connected) {
        return null;
      }
    }

    return new Promise((resolve) => {
      // Set a timeout for initialization
      const timeout = setTimeout(() => {
        console.error('[SocketVAD] VAD initialization timeout');
        resolve(null);
      }, 5000);

      // Listen for initialization response
      this.once(SocketVadEvent.VAD_INITIALIZED, (data: VadInitializedEvent) => {
        clearTimeout(timeout);
        this.sessionId = data.session_id;
        console.log(`[SocketVAD] VAD session initialized: ${this.sessionId}`);
        
        // Store the initial speaking state
        this.isSpeaking = false;
        
        resolve(this.sessionId);
      });

      // Send initialization request
      this.socket!.emit('init_vad', {
        session_id: existingSessionId
      });
    });
  }

  /**
   * Process an audio chunk
   * @param audioData Base64-encoded PCM audio data
   */
  processAudio(audioData: string): void {
    if (!this.socket || !this.isConnected || !this.sessionId) {
      console.error('[SocketVAD] Cannot process audio: not connected or no session');
      return;
    }

    this.socket.emit('process_audio', {
      session_id: this.sessionId,
      audio: audioData
    });
  }

  /**
   * Update VAD configuration
   * @param config Configuration options
   */
  updateConfig(config: VadConfig): void {
    if (!this.socket || !this.isConnected || !this.sessionId) {
      console.error('[SocketVAD] Cannot update config: not connected or no session');
      return;
    }

    this.socket.emit('update_vad_config', {
      session_id: this.sessionId,
      config
    });
  }

  /**
   * Force recalibration of the VAD system
   */
  forceRecalibration(): void {
    if (!this.socket || !this.isConnected || !this.sessionId) {
      console.error('[SocketVAD] Cannot force recalibration: not connected or no session');
      return;
    }

    this.socket.emit('force_recalibration', {
      session_id: this.sessionId
    });
  }

  /**
   * Get debug state
   */
  getDebugState(): void {
    if (!this.socket || !this.isConnected || !this.sessionId) {
      console.error('[SocketVAD] Cannot get debug state: not connected or no session');
      return;
    }

    this.socket.emit('get_debug_state', {
      session_id: this.sessionId
    });
  }

  /**
   * Process audio from AudioBuffer
   * @param audioBuffer Web Audio API AudioBuffer
   */
  processAudioBuffer(audioBuffer: AudioBuffer): void {
    // Convert to the format expected by the backend
    const pcmData = this.convertAudioBufferToPCM(audioBuffer);
    
    // Encode as base64
    const base64Data = btoa(String.fromCharCode(...new Uint8Array(pcmData)));
    
    // Send to the server
    this.processAudio(base64Data);
  }

  /**
   * Process audio from Float32Array
   * @param audioData Float32Array audio data
   */
  processAudioData(audioData: Float32Array): void {
    // Convert to the format expected by the backend
    const pcmData = this.convertFloat32ToPCM(audioData);
    
    // Encode as base64
    const base64Data = btoa(String.fromCharCode(...new Uint8Array(pcmData)));
    
    // Send to the server
    this.processAudio(base64Data);
  }

  /**
   * Convert AudioBuffer to PCM format
   * @param buffer Web Audio API AudioBuffer
   * @returns ArrayBuffer containing PCM data
   */
  private convertAudioBufferToPCM(buffer: AudioBuffer): ArrayBuffer {
    // Get the first channel (mono)
    const samples = buffer.getChannelData(0);
    return this.convertFloat32ToPCM(samples);
  }

  /**
   * Convert Float32Array to PCM format
   * @param samples Float32Array audio samples (-1.0 to 1.0)
   * @returns ArrayBuffer containing PCM data
   */
  private convertFloat32ToPCM(samples: Float32Array): ArrayBuffer {
    // Convert to 16-bit PCM
    const pcmData = new Int16Array(samples.length);
    
    // Convert Float32 (-1.0 to 1.0) to Int16 (-32768 to 32767)
    for (let i = 0; i < samples.length; i++) {
      const s = Math.max(-1, Math.min(1, samples[i]));
      pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    
    return pcmData.buffer;
  }

  /**
   * Check if connected to the server
   */
  isSocketConnected(): boolean {
    return this.isConnected && this.socket !== null;
  }

  /**
   * Check if a VAD session is active
   */
  hasActiveSession(): boolean {
    return this.isSocketConnected() && this.sessionId !== null;
  }

  /**
   * Get the current session ID
   */
  getSessionId(): string | null {
    return this.sessionId;
  }

  /**
   * Get the current speaking state
   */
  getIsSpeaking(): boolean {
    return this.isSpeaking;
  }

  /**
   * Disconnect from the server
   */
  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.sessionId = null;
    this.isConnected = false;
    this.isSpeaking = false;
  }

  /**
   * Attempt to reconnect to the server
   */
  private reconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error(`[SocketVAD] Max reconnect attempts (${this.maxReconnectAttempts}) reached`);
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectDelay * this.reconnectAttempts, 5000);
    
    console.log(`[SocketVAD] Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
    
    setTimeout(() => {
      this.connect().then(connected => {
        if (connected && this.sessionId) {
          // Try to reuse the previous session
          this.initVad(this.sessionId);
        }
      });
    }, delay);
  }

  /**
   * Register an event handler
   * @param event Event type
   * @param handler Handler function
   */
  on<T>(event: SocketVadEvent, handler: EventHandler<T>): void {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, new Set());
    }
    this.eventHandlers.get(event)!.add(handler as EventHandler<unknown>);
  }

  /**
   * Register a one-time event handler
   * @param event Event type
   * @param handler Handler function
   */
  once<T>(event: SocketVadEvent, handler: EventHandler<T>): void {
    const onceHandler: EventHandler<T> = (data: T) => {
      this.off(event, onceHandler);
      handler(data);
    };
    this.on(event, onceHandler);
  }

  /**
   * Remove an event handler
   * @param event Event type
   * @param handler Handler function
   */
  off<T>(event: SocketVadEvent, handler: EventHandler<T>): void {
    if (this.eventHandlers.has(event)) {
      this.eventHandlers.get(event)!.delete(handler as EventHandler<unknown>);
    }
  }

  /**
   * Emit an event to registered handlers
   * @param event Event type
   * @param data Event data
   */
  private emit<T>(event: string, data: T): void {
    if (this.eventHandlers.has(event)) {
      for (const handler of this.eventHandlers.get(event)!) {
        try {
          handler(data);
        } catch (error) {
          console.error(`[SocketVAD] Error in event handler for ${event}:`, error);
        }
      }
    }

    // Special handling for speech state events
    if (event === SocketVadEvent.SPEECH_START) {
      this.isSpeaking = true;
    } else if (event === SocketVadEvent.SPEECH_END) {
      this.isSpeaking = false;
    }
  }

  /**
   * Set debug mode
   * @param enabled Whether debug logging should be enabled
   */
  setDebug(enabled: boolean): void {
    this.debug = enabled;
  }
}

// Create a singleton instance
export const socketVadService = new SocketVadService();

// Export the default instance and the class for testing
export default socketVadService; 