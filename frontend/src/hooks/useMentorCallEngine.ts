import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useMicStream } from './useMicStream';
import { useSocketVad } from './useSocketVad';
import { useSessionStore } from '../state/sessionStore';
import { 
  createSystemPrompt, 
  streamChatCompletionWithOpenAI, 
  sanitizeResponse,
  ChatMessage,
  useDirectOpenAI
} from '../services/openaiService';
import { 
  generateSpeech,
  playAudio,
  stopAudio,
  VoiceOptions
} from '../services/ttsService';
import { MentorKey } from '../types';
import { generateResponse } from '../services/api';
import { MENTOR_PERSONALITIES, API_ENDPOINTS } from '../constants/app';
import { prepareMentorConversation, streamMentorCompletion, transcribeAudioWithBackend } from '../services/mentorService';
import { detectSpeechEmotion } from '../utils/emotionDetector';
import { EMOTION_VOICE_SETTINGS, VOICE_EMOTION_DEFAULTS } from '../constants/emotionSettings';

export interface MentorCallOptions {
  enableVoiceActivity?: boolean;    // Enable voice activity detection for interruptions
  autoStart?: boolean;              // Auto start listening when hook mounts
  maxSilenceMs?: number;            // Maximum silence before considering the user done speaking
  immediateTranscription?: boolean; // Transcribe immediately as user speaks
  historyWindowSize?: number;       // Number of previous exchanges to keep in context
  useSocketVad?: boolean;           // Whether to use WebSocket-based VAD instead of local processing
  adaptiveVoice?: boolean;          // Enable adaptive voice based on conversation context
}

export interface MentorCallState {
  userText: string;             // Current user transcription
  mentorText: string;           // Current mentor response
  isProcessing: boolean;        // Whether audio is being processed
  isError: boolean;             // Whether an error occurred
  errorMessage: string | null;  // Error message if any
}

// Extended voice options that includes user customization flag
export interface ExtendedVoiceOptions extends VoiceOptions {
  userCustomized?: boolean;     // Whether the user has manually customized voice settings
}

// Speech emotion types for adaptive voice
export type SpeechEmotion = 
  | 'neutral'
  | 'calm'
  | 'reflective'
  | 'passionate'
  | 'inspiring'
  | 'concerned';

// Default voice options for each emotion
const EMOTION_VOICE_SETTINGS: Record<SpeechEmotion, ExtendedVoiceOptions> = {
  neutral: {
    speed: 1.0,
    stability: 0.5,
    similarityBoost: 0.75,
    style: 0.0
  },
  calm: {
    speed: 0.9,
    stability: 0.7,
    similarityBoost: 0.8,
    style: 0.2
  },
  reflective: {
    speed: 0.85,
    stability: 0.6,
    similarityBoost: 0.7,
    style: 0.4
  },
  passionate: {
    speed: 1.15,
    stability: 0.4,
    similarityBoost: 0.6,
    style: 0.7
  },
  inspiring: {
    speed: 1.1,
    stability: 0.5,
    similarityBoost: 0.8,
    style: 0.6
  },
  concerned: {
    speed: 0.95,
    stability: 0.6,
    similarityBoost: 0.7,
    style: 0.5
  }
};

/**
 * Analyzes text content to determine the appropriate speech emotion
 */
const detectSpeechEmotion = (text: string): SpeechEmotion => {
  // Keywords that indicate different emotions
  const emotionKeywords: Record<SpeechEmotion, string[]> = {
    calm: ['peace', 'tranquil', 'serene', 'quiet', 'relax', 'breathe', 'acceptance'],
    reflective: ['consider', 'reflect', 'think', 'contemplate', 'remember', 'imagine', 'perspective'],
    passionate: ['must', 'important', 'critical', 'essential', 'never', 'always', 'courage'],
    inspiring: ['potential', 'better', 'growth', 'improve', 'future', 'hope', 'strength'],
    concerned: ['worry', 'anxious', 'fear', 'trouble', 'problem', 'difficult', 'challenge'],
    neutral: []
  };

  // Count matches for each emotion
  const counts: Record<SpeechEmotion, number> = {
    calm: 0,
    reflective: 0,
    passionate: 0,
    inspiring: 0,
    concerned: 0,
    neutral: 0
  };

  // Normalize text to lowercase for better matching
  const lowercaseText = text.toLowerCase();

  // Count keyword matches
  Object.entries(emotionKeywords).forEach(([emotion, keywords]) => {
    keywords.forEach(keyword => {
      if (lowercaseText.includes(keyword)) {
        counts[emotion as SpeechEmotion]++;
      }
    });
  });

  // Check for specific punctuation patterns
  if ((text.match(/!/g) || []).length > 2) {
    counts.passionate += 2;
  }
  
  if ((text.match(/\?/g) || []).length > 2) {
    counts.reflective += 2;
  }

  // Determine the predominant emotion
  let predominantEmotion: SpeechEmotion = 'neutral';
  let maxCount = 0;

  Object.entries(counts).forEach(([emotion, count]) => {
    if (count > maxCount) {
      maxCount = count;
      predominantEmotion = emotion as SpeechEmotion;
    }
  });

  return predominantEmotion;
};

// Add voice emotion defaults
const VOICE_EMOTION_DEFAULTS = {
  speed: 1.0,
  stability: 0.5,
  similarityBoost: 0.75
};

/**
 * A hook that orchestrates the complete mentor call flow:
 * 1. Record user audio via microphone
 * 2. Transcribe audio to text using Whisper
 * 3. Generate mentor response using GPT
 * 4. Synthesize and play audio response
 * 
 */
export function useMentorCallEngine(options: MentorCallOptions = {}) {
  
  // Default options
  const defaultOptions: Required<MentorCallOptions> = {
    enableVoiceActivity: true,
    autoStart: false,
    maxSilenceMs: 1500,
    immediateTranscription: false,
    historyWindowSize: 3,
    useSocketVad: true,
    adaptiveVoice: true,  // Enable adaptive voice by default
  };
  
  const opts = { ...defaultOptions, ...options };
  
  // Custom voice options
  const [voiceOptions, setVoiceOptions] = useState<ExtendedVoiceOptions>({
    speed: 1.0,
    stability: 0.5,
    similarityBoost: 0.75,
    style: 0.0,
    userCustomized: false
  });
  
  // Current speech emotion
  const [speechEmotion, setSpeechEmotion] = useState<SpeechEmotion>('neutral');
  
  // Global state
  const { 
    currentMentor, 
    isSpeaking, 
    isListening, 
    setIsSpeaking, 
    setIsListening, 
    addMessage, 
    history 
  } = useSessionStore();
  
  // Audio recording
  const { 
    isRecording, 
    audioLevel: micAudioLevel, 
    startRecording, 
    stopRecording, 
    getAudioBlob 
  } = useMicStream();
  
  // Initialize the useSocketVad hook with our settings
  const {
    isConnected: isSocketVadConnected,
    isSessionActive: isSocketVadSessionActive,
    isSpeaking: isSocketVadDetectingSpeech,
    audioLevel: socketVadAudioLevel,
    threshold: socketVadThreshold,
    connect: connectSocketVad,
    startAudioProcessing: startSocketVadProcessing,
    stopAudioProcessing: stopSocketVadProcessing,
    forceRecalibration: recalibrateSocketVad,
    disconnect: disconnectSocketVad
  } = useSocketVad({
    autoConnect: false,  // We'll manage the connection ourselves
    autoInit: false,     // We'll initialize when needed
    debug: true,
    onSpeakingChange: (isSpeaking) => {
      console.log(`[VAD] Speech state changed: ${isSpeaking ? 'SPEAKING' : 'SILENT'}`);
    }
  });
  
  // Combine audio levels
  const audioLevel = opts.useSocketVad ? socketVadAudioLevel : micAudioLevel;
  
  // Track VAD state
  const [isVADActive, setIsVADActive] = useState(false);
  
  // Debug state
  const [debugState, setDebugState] = useState({
    vadConnectionStatus: false,
    vadSessionStatus: false,
    vadActive: false,
    vadSpeakingStatus: false,
  });
  
  // Local state
  const [state, setState] = useState<MentorCallState>({
    userText: '',
    mentorText: '',
    isProcessing: false,
    isError: false,
    errorMessage: null,
  });
  
  // Add session ID for conversation tracking
  const sessionId = useRef<string>(`session_${Date.now()}`);
  
  // Determine if we should use direct API or backend
  const shouldUseDirectApi = useDirectOpenAI();
  
  // Refs to maintain state between renders
  const abortControllerRef = useRef<AbortController | null>(null);
  const silenceTimeoutRef = useRef<number | null>(null);
  const responseTimeoutRef = useRef<number | null>(null);
  const isGeneratingResponseRef = useRef(false);
  const isStreamingTTSRef = useRef(false);
  const previousSilenceStateRef = useRef(false);
  
  // Cleanup function
  const cleanupResources = useCallback(() => {
    // Clear timeouts
    if (silenceTimeoutRef.current) {
      clearTimeout(silenceTimeoutRef.current);
      silenceTimeoutRef.current = null;
    }
    
    if (responseTimeoutRef.current) {
      clearTimeout(responseTimeoutRef.current);
      responseTimeoutRef.current = null;
    }
    
    // Abort any ongoing requests
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    
    // Stop VAD processing if using socket VAD
    if (opts.useSocketVad) {
      stopSocketVadProcessing();
    }
  }, [opts.useSocketVad, stopSocketVadProcessing]);
  
  // Function to end a call completely
  const endCall = useCallback(() => {
    stopRecording();
    cleanupResources();
    
    // If using socket VAD, disconnect it
    if (opts.useSocketVad) {
      disconnectSocketVad();
    }
    
    setIsVADActive(false);
    setIsListening(false);
    setIsSpeaking(false);
  }, [cleanupResources, disconnectSocketVad, opts.useSocketVad, setIsListening, setIsSpeaking, stopRecording]);
  
  // Update listening state based on recording state
  useEffect(() => {
    setIsListening(isRecording);
  }, [isRecording, setIsListening]);
  
  // Start listening for audio
  const startListening = useCallback(async () => {
    try {
      // Reset state
      setState(prev => ({
        ...prev,
        userText: '',
        isError: false,
        errorMessage: null,
      }));
      
      // Create a new abort controller
      abortControllerRef.current = new AbortController();
      
      // Connect and initialize VAD if using WebSocket VAD
      if (opts.useSocketVad) {
        console.log('[useMentorCallEngine] Connecting to WebSocket VAD');
        const connected = await connectSocketVad();
        if (!connected) {
          throw new Error("Failed to connect to WebSocket VAD service");
        }
        
        // Start audio processing with the WebSocket VAD
        console.log('[useMentorCallEngine] Starting WebSocket VAD audio processing');
        const started = await startSocketVadProcessing();
        if (!started) {
          throw new Error("Failed to start microphone recording for WebSocket VAD");
        }
        
        setIsVADActive(true);
      }
      
      // Start recording
      const success = await startRecording();
      if (!success) {
        // Handle microphone permission errors
        if (navigator.permissions) {
          const micPermission = await navigator.permissions.query({ name: 'microphone' as PermissionName });
          if (micPermission.state === 'denied') {
            throw new Error("Microphone access was denied. Please allow microphone access in your browser settings.");
          }
        }
        
        // Generic microphone error
        throw new Error("Could not start microphone. It may be in use by another application.");
      }
    } catch (error) {
      console.error('Error starting listening:', error);
      setState(prev => ({
        ...prev,
        isError: true,
        errorMessage: error instanceof Error 
          ? error.message 
          : 'Failed to access microphone',
      }));
      
      // Clean up if there was an error
      cleanupResources();
    }
  }, [startRecording, connectSocketVad, startSocketVadProcessing, opts.useSocketVad, cleanupResources]);
  
  // Stop listening and process audio
  const stopListening = useCallback(async () => {
    try {
      // Stop recording
      stopRecording();
      
      // Also stop socket VAD processing if using it
      if (opts.useSocketVad) {
        console.log('[useMentorCallEngine] Stopping WebSocket VAD audio processing');
        stopSocketVadProcessing();
        setIsVADActive(false);
      }
      
      // Start processing
      setState(prev => ({ ...prev, isProcessing: true }));
      
      // Get the recorded audio
      const audioBlob = await getAudioBlob();
      
      if (!audioBlob) {
        throw new Error('No audio recorded');
      }
      
      // Process the audio
      await processAudio();
    } catch (error) {
      console.error('Error stopping listening:', error);
      setState(prev => ({
        ...prev,
        isProcessing: false,
        isError: true,
        errorMessage: error instanceof Error 
          ? error.message 
          : 'Failed to process audio',
      }));
    }
  }, [stopRecording, getAudioBlob, opts.useSocketVad, stopSocketVadProcessing]);
  
  // Helpers for TTS
  const updateAudioProgress = useCallback((progress: { loaded: number; total: number; currentChunk: number; totalChunks: number }) => {
    // Optional audio progress callback
    console.log('Audio progress:', progress);
  }, []);

  const getHistoryContext = useCallback((count: number) => {
    // Get recent conversation context for TTS
    return history.slice(-count).map(msg => ({
      text: msg.content,
      speaker: msg.role === 'user' ? 1 : 0,
      audio: ''
    }));
  }, [history]);
  
  // Process the audio (transcribe and generate response)
  const processAudio = useCallback(async () => {
    try {
      console.log('[processAudio] Starting audio processing');
      setState(prev => ({ ...prev, isProcessing: true }));

      // Stop recording
      await stopRecording();
      console.log('[processAudio] Stopped recording');

      // Get the audio blob
      const audioBlob = await getAudioBlob();
      if (!audioBlob) {
        console.warn('[processAudio] Failed to get audio blob');
        setState(prev => ({ 
          ...prev, 
          isProcessing: false,
          isError: true,
          errorMessage: 'Failed to get audio recording. Please try again.'
        }));
        return;
      }
      
      console.log('[processAudio] Got audio blob, size:', audioBlob.size, 'type:', audioBlob.type);

      // Make sure we have a valid audio blob with sufficient data
      if (audioBlob.size < 1000) {
        console.warn('[processAudio] Audio blob too small, skipping');
        setState(prev => ({ 
          ...prev, 
          isProcessing: false,
          isError: false,  // Don't show as error to user
          errorMessage: null
        }));
        return;
      }

      // If the blob is not a WAV file, convert it
      let transcriptionBlob = audioBlob;
      if (audioBlob.type !== 'audio/wav' && audioBlob.type !== 'audio/wave') {
        console.log('[processAudio] Converting blob to WAV format');
        try {
          // Use the blob as is, backend will handle conversion
          console.log('[processAudio] Proceeding with original format:', audioBlob.type);
        } catch (conversionError) {
          console.error('[processAudio] Error converting audio format:', conversionError);
          // Continue with original blob
        }
      }

      // Stop VAD if active
      if (opts.useSocketVad) {
        stopSocketVadProcessing();
        console.log('[processAudio] Stopped VAD processing');
      }

      console.log('[processAudio] Transcribing audio...', transcriptionBlob.size, 'bytes');
      
      // Use our backend transcription function
      let transcription = '';
      let transcriptionAttempts = 0;
      const maxTranscriptionAttempts = 2;
      
      while (transcriptionAttempts < maxTranscriptionAttempts) {
        transcriptionAttempts++;
        try {
          console.log(`[processAudio] Transcription attempt ${transcriptionAttempts}/${maxTranscriptionAttempts}`);
          transcription = await transcribeAudioWithBackend(transcriptionBlob);
          console.log('[processAudio] Transcription received:', transcription);
          break; // Success, exit the loop
        } catch (error) {
          console.error('[processAudio] Transcription error:', error);
          if (transcriptionAttempts >= maxTranscriptionAttempts) {
            setState(prev => ({
              ...prev,
              isProcessing: false,
              isError: true,
              errorMessage: 'Failed to transcribe audio. Please check your connection and try again.'
            }));
            return;
          }
          // Wait before retrying
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      }

      if (!transcription || transcription.trim() === '') {
        console.warn('[processAudio] Empty transcription received');
        setState(prev => ({
          ...prev,
          isProcessing: false,
          isError: true,
          errorMessage: 'No speech detected. Please try speaking more clearly.'
        }));
        return;
      }

      // ===================================================================================
      // Generate a response using the mentor service
      // ===================================================================================
      try {
        console.log(`🔍 FLOW TRACE [generateMentorResponse] - Starting response generation`);
        
        setState(prev => ({ ...prev, mentorText: '' }));
        console.log(`🔍 FLOW TRACE [generateMentorResponse] - Reset mentor text`);
        
        // Create a new AbortController for this request
        abortControllerRef.current = new AbortController();
        console.log(`🔍 FLOW TRACE [generateMentorResponse] - Created new AbortController`);
        
        // Ensure we have a session ID for the conversation
        if (!sessionId.current) {
          sessionId.current = `session_${Date.now()}`;
          console.log(`🔍 FLOW TRACE [generateMentorResponse] - Created new session ID: ${sessionId.current}`);
        }
        
        // Update state with transcription
        setState(prev => ({ ...prev, userText: transcription }));
        console.log('🔎 PROCESS AUDIO DEBUGGING - Updated state with user text');
        
        // Add user message to history
        addMessage({
          role: 'user',
          content: transcription,
          timestamp: Date.now(),
        });
        console.log('🔎 PROCESS AUDIO DEBUGGING - Added user message to history');
        
        console.log('🔎 PROCESS AUDIO DEBUGGING - *** CRITICAL HANDOFF POINT ***');
        console.log('🔎 PROCESS AUDIO DEBUGGING - About to call generateMentorResponse with text:', transcription);
        
        // Generate mentor response
        console.log('🔎 PROCESS AUDIO DEBUGGING - Calling generateMentorResponse now');
        
        // INLINE DEFINITION OF generateMentorResponse - This ensures we always use the current value of currentMentor
        // ============================================================================================
        // Get the latest mentor information directly from the store
        const sessionState = useSessionStore.getState(); 
        const mentorKey = sessionState.currentMentor as MentorKey;
        console.log(`🔍 CRITICAL DEBUG - Using mentor key from store: ${mentorKey}`);
        
        if (!transcription) {
          console.log(`🔍 FLOW TRACE [generateMentorResponse] - Empty text, skipping`);
          return;
        }

        if (isGeneratingResponseRef.current) {
          console.log(`🔍 FLOW TRACE [generateMentorResponse] - Already generating, skipping`);
          return;
        }

        try {
          isGeneratingResponseRef.current = true;
          console.log(`🔍 FLOW TRACE [generateMentorResponse] - Set isGeneratingResponse = true`);
          
          // Force checking current mentor from the store again
          const freshSessionState = useSessionStore.getState();
          const freshMentorKey = freshSessionState.currentMentor as MentorKey;
          console.log(`🔍 CRITICAL DEBUG - Double-checked mentor key: ${freshMentorKey}`);
          
          // Get the full mentor name and details from the constants
          const mentorDetails = MENTOR_PERSONALITIES[freshMentorKey];
          if (!mentorDetails) {
            console.error(`🔍 FLOW TRACE [generateMentorResponse] - Invalid mentor key: ${freshMentorKey}`);
            return;
          }
          
          const mentorName = mentorDetails.name; // This will be the full name like "Marcus Aurelius"
          console.log(`🔍 FLOW TRACE [generateMentorResponse] - Selected mentor key: ${freshMentorKey}, full name: ${mentorName}`);

          if (!freshMentorKey) {
            console.error(`🔍 FLOW TRACE [generateMentorResponse] - No mentor selected!`);
            return;
          }

          setIsSpeaking(true);
          console.log(`🔍 FLOW TRACE [generateMentorResponse] - Set isSpeaking = true`);

          // Record user message
          const userMessage: ChatMessage = {
            role: 'user',
            content: transcription,
          };
          console.log(`🔍 FLOW TRACE [generateMentorResponse] - Created user message: ${userMessage.content.substring(0, 30)}...`);

          let mentorResponseContent = '';

          // Get conversation history
          const conversationHistory: ChatMessage[] = history
            .slice(-opts.historyWindowSize * 2) // Get the last n exchanges (2 messages per exchange)
            .map(msg => ({
              role: msg.role === 'user' ? 'user' : 'assistant',
              content: msg.content
            })) as ChatMessage[];
          
          console.log(`🔍 FLOW TRACE [generateMentorResponse] - Created conversation history with ${conversationHistory.length} messages`);

          // Determine speech emotion for adaptive voice if enabled
          if (opts.adaptiveVoice) {
            const detectedEmotion = detectSpeechEmotion(transcription);
            setSpeechEmotion(detectedEmotion);
            console.log(`🔍 FLOW TRACE [generateMentorResponse] - Detected speech emotion: ${detectedEmotion}`);
            
            // Apply adaptive voice settings if not overridden by manual settings
            if (!voiceOptions.userCustomized) {
              const emotionSettings = EMOTION_VOICE_SETTINGS[detectedEmotion];
              setVoiceOptions(prev => ({
                ...emotionSettings,
                userCustomized: prev.userCustomized
              }));
              console.log(`🔍 FLOW TRACE [generateMentorResponse] - Applied adaptive voice settings for ${detectedEmotion} emotion`);
            }
          }

          // Create messages array with system prompt
          const systemPrompt = createSystemPrompt(mentorName);
          const messages = [
            { role: 'system', content: systemPrompt },
            ...conversationHistory,
            userMessage
          ] as ChatMessage[];

          // Stream the response from the backend
          const stream = await streamMentorCompletion(
            messages,
            { 
              signal: abortControllerRef.current?.signal,
              conversation_id: sessionId.current 
            }
          );

          for await (const chunk of stream) {
            mentorResponseContent += chunk;
            
            // Sanitize the response to ensure better formatting
            const sanitizedContent = sanitizeResponse(mentorResponseContent);
            
            setState(prev => ({ ...prev, mentorText: sanitizedContent }));
          }
          
          console.log(`🔍 FLOW TRACE [generateMentorResponse] - Generated mentor response: "${mentorResponseContent.substring(0, 50)}..."`);
          
          // Add assistant message to history
          addMessage({
            role: 'assistant',
            content: mentorResponseContent,
            timestamp: Date.now(),
          });
          console.log(`🔍 FLOW TRACE [generateMentorResponse] - Added assistant message to history`);
          
          // Generate speech from the response
          isStreamingTTSRef.current = true;
          console.log(`🔍 FLOW TRACE [generateMentorResponse] - Set isStreamingTTS = true`);
          
          const messageId = `msg_${Date.now()}`;
          
          try {
            console.log(`🔍 FLOW TRACE [generateMentorResponse] - Starting TTS generation`);
            console.log(`🔍 FLOW TRACE [generateMentorResponse] - Using voice options:`, voiceOptions);
            
            // Map mentor key to speaker ID
            const speakerMap: Record<MentorKey, number> = {
              marcus: 0,
              seneca: 1,
              epictetus: 2
            };
            
            const speakerId = speakerMap[freshMentorKey] || 0;
            
            // Get final voice options by combining defaults with any emotion-based changes
            const finalVoiceOptions = {
              ...VOICE_EMOTION_DEFAULTS,
              ...voiceOptions
            };
            
            const audioBlob = await generateSpeech(
              mentorResponseContent,
              speakerId,
              messageId,
              updateAudioProgress,
              getHistoryContext(3),
              finalVoiceOptions  // Pass voice options to TTS generator
            );
            
            console.log(`🔍 FLOW TRACE [generateMentorResponse] - TTS generation complete, playing audio`);
            
            // Start playing the audio
            await playAudio(audioBlob, messageId);
            
            setIsSpeaking(false);
            console.log(`🔍 FLOW TRACE [generateMentorResponse] - Set isSpeaking = false`);
          } catch (error) {
            console.error(`🔍 FLOW TRACE [generateMentorResponse] - TTS or playback error:`, error);
            
            isStreamingTTSRef.current = false;
            setIsSpeaking(false);
            console.log(`🔍 FLOW TRACE [generateMentorResponse] - Set isStreamingTTS = false, isSpeaking = false`);
          }
          
        } catch (error) {
          console.error(`🔍 FLOW TRACE [generateMentorResponse] - Error generating response:`, error);
          
          setState(prev => ({
            ...prev,
            isError: true,
            errorMessage: error instanceof Error 
              ? error.message 
              : 'Failed to generate response'
          }));
          
          setIsSpeaking(false);
          isStreamingTTSRef.current = false;
          console.log(`🔍 FLOW TRACE [generateMentorResponse] - Set isSpeaking = false, isStreamingTTS = false`);
        } finally {
          isGeneratingResponseRef.current = false;
          console.log(`🔍 FLOW TRACE [generateMentorResponse] - Set isGeneratingResponse = false`);
        }
        // ============================================================================================
        
      } catch (error) {
        console.error('Error in processAudio:', error);
        setState(prev => ({
          ...prev,
          isProcessing: false,
          isError: true,
          errorMessage: error instanceof Error 
            ? error.message 
            : 'Failed to process audio'
        }));
      }
    } catch (error) {
      console.error('Error in processAudio:', error);
      setState(prev => ({
        ...prev,
        isProcessing: false,
        isError: true,
        errorMessage: error instanceof Error 
          ? error.message 
          : 'Failed to process audio'
      }));
    }
  }, [stopRecording, getAudioBlob, opts.useSocketVad, stopSocketVadProcessing, opts.historyWindowSize, opts.adaptiveVoice, history, addMessage, setIsSpeaking, setState, voiceOptions, updateAudioProgress, getHistoryContext]);
  
  // Helper function to detect acknowledgment phrases
  const hasAcknowledgmentPhrases = (text: string): boolean => {
    const lowerText = text.toLowerCase();
    const phrases = [
      "i understand what you're saying",
      "i understand what you are saying",
      "i see what you're saying",
      "i see what you are saying",
      "i understand your question",
      "let me think about that",
      "i appreciate your question",
      "thank you for your question",
      "i understand you're asking",
      "i understand you are asking"
    ];
    
    return phrases.some(phrase => lowerText.includes(phrase));
  };
  
  // Toggle listening (start/stop)
  const toggleListening = useCallback(async () => {
    if (isRecording) {
      await stopListening();
    } else {
      await startListening();
    }
  }, [isRecording, startListening, stopListening]);
  
  // Interrupt the current mentor response
  const interruptMentor = useCallback(() => {
    // Only interrupt if mentor is speaking
    if (!isSpeaking) return;
    
    console.log('Interrupting mentor response');
    
    // Abort current operations
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    // Reset speaking state
    setIsSpeaking(false);
    
    // Reset flags
    isGeneratingResponseRef.current = false;
    isStreamingTTSRef.current = false;
    
    // Clean up
    cleanupResources();
  }, [isSpeaking, setIsSpeaking, cleanupResources]);
  
  // Auto-start if enabled
  useEffect(() => {
    if (opts.autoStart) {
      startListening();
    }
    
    return cleanupResources;
  }, [opts.autoStart, startListening, cleanupResources]);
  
  // Monitor WebSocket VAD for silence detection
  useEffect(() => {
    // Only set up silence detection if using socket VAD and currently recording
    if (!opts.useSocketVad || !isRecording) return;
    
    // Check if we have a change from speaking to silent
    const isSilent = !isSocketVadDetectingSpeech;
    const wasSpokenBefore = !previousSilenceStateRef.current;
    const silenceJustStarted = isSilent && wasSpokenBefore;
    
    console.log(`[VAD] Current state - isSilent: ${isSilent}, wasSpokenBefore: ${wasSpokenBefore}, silenceJustStarted: ${silenceJustStarted}, isRecording: ${isRecording}`);
    
    // Update the previous silence state
    previousSilenceStateRef.current = isSilent;
    
    // If silence just started, set a timer to stop recording after configured timeout
    if (silenceJustStarted && isRecording) {
      console.log(`[VAD] Silence detected, waiting ${opts.maxSilenceMs}ms before stopping...`);
      
      // Clear any existing timeout
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current);
      }
      
      // Set new timeout to stop listening after silence threshold
      silenceTimeoutRef.current = window.setTimeout(() => {
        console.log('[VAD] Silence timeout reached, stopping recording');
        if (isRecording) {
          stopListening();
        }
        silenceTimeoutRef.current = null;
      }, opts.maxSilenceMs);
    }
    
    // If the user was silent and now is speaking again, cancel any pending silence timeout
    if (!isSilent && silenceTimeoutRef.current) {
      console.log('[VAD] Speech detected, canceling silence timeout');
      clearTimeout(silenceTimeoutRef.current);
      silenceTimeoutRef.current = null;
    }
    
    // Cleanup timeout on unmount or dependency change
    return () => {
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current);
        silenceTimeoutRef.current = null;
      }
    };
  }, [
    opts.useSocketVad, 
    opts.maxSilenceMs, 
    isRecording, 
    isSocketVadDetectingSpeech, 
    stopListening
  ]);
  
  // Log and respond to mentor changes
  useEffect(() => {
    console.log(`🔍 MENTOR CHANGE DETECTED - Current mentor is now: ${currentMentor}`);
    
    // Reset state when mentor changes to ensure fresh conversations
    setState(prev => ({
      ...prev,
      userText: '',
      mentorText: '',
      isError: false,
      errorMessage: null,
    }));
    
    // Abort any ongoing operations
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    // Reset flags
    isGeneratingResponseRef.current = false;
    isStreamingTTSRef.current = false;
    
  }, [currentMentor]);
  
  // Listen for custom mentor-changed events
  useEffect(() => {
    const handleMentorChanged = (event: Event) => {
      const customEvent = event as CustomEvent;
      const newMentor = customEvent.detail?.mentor;
      console.log(`🔍 MENTOR-CHANGED EVENT - Detected mentor change to: ${newMentor}`);
      
      // Force check against the store
      const storeState = useSessionStore.getState();
      console.log(`🔍 MENTOR-CHANGED EVENT - Current store state has mentor: ${storeState.currentMentor}`);
    };
    
    window.addEventListener('mentor-changed', handleMentorChanged);
    
    return () => {
      window.removeEventListener('mentor-changed', handleMentorChanged);
    };
  }, []);
  
  // Update debug state
  useEffect(() => {
    setDebugState({
      vadConnectionStatus: isSocketVadConnected,
      vadSessionStatus: isSocketVadSessionActive, 
      vadActive: isVADActive,
      vadSpeakingStatus: isSocketVadDetectingSpeech,
    });
    
    console.log(`[VAD DEBUG] Connection: ${isSocketVadConnected ? 'YES' : 'NO'}, ` +
                `Session: ${isSocketVadSessionActive ? 'ACTIVE' : 'INACTIVE'}, ` + 
                `VAD Active: ${isVADActive ? 'YES' : 'NO'}, ` +
                `Speaking: ${isSocketVadDetectingSpeech ? 'YES' : 'SILENT'}`);
                
  }, [isSocketVadConnected, isSocketVadSessionActive, isVADActive, isSocketVadDetectingSpeech]);
  
  // Initialize WebSocket VAD when the component mounts
  useEffect(() => {
    if (opts.useSocketVad) {
      console.log('[useMentorCallEngine] Initializing WebSocket VAD on mount');
      connectSocketVad().then(connected => {
        console.log(`[useMentorCallEngine] WebSocket VAD connection ${connected ? 'successful' : 'failed'}`);
      });
    }
    
    return () => {
      if (opts.useSocketVad) {
        disconnectSocketVad();
      }
    };
  }, [opts.useSocketVad, connectSocketVad, disconnectSocketVad]);
  
  // Return the API
  return {
    ...state,
    audioLevel,
    isRecording,
    isSpeaking,
    isListening,
    isVADActive,
    startListening,
    stopListening,
    toggleListening,
    interruptMentor,
    endCall,
    // Debug info for WebSocket VAD
    vadDebugState: debugState,
    isSocketVadConnected,
    isSocketVadSessionActive,
    isSocketVadDetectingSpeech,
    voiceOptions,
    setVoiceOptions,
    speechEmotion
  };
} 