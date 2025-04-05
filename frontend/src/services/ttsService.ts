import { API_ENDPOINTS } from '../constants/app';
import { audioCacheService } from './audioCacheService';

// Constants for progressive loading
const CHUNK_SIZE = 32 * 1024; // 32KB chunks
const BUFFER_THRESHOLD = 2; // Number of chunks to buffer ahead

/**
 * Interface for ElevenLabs Voice
 */
interface ElevenLabsVoice {
  voice_id: string;
  name: string;
  category?: string;
  description?: string;
  preview_url?: string;
  labels?: Record<string, string>;
  settings?: {
    stability: number;
    similarity_boost: number;
  };
}

/**
 * Voice customization options
 */
export interface VoiceOptions {
  speed?: number;         // Speed multiplier (0.5 to 2.0)
  stability?: number;     // Voice stability (0.0 to 1.0)
  similarityBoost?: number; // Voice similarity boost (0.0 to 1.0)
  style?: number;         // Style control (0.0 to 1.0) - ElevenLabs only
}

interface AudioProgress {
  loaded: number;
  total: number;
  buffered: TimeRanges | null;
  currentChunk: number;
  totalChunks: number;
}

let currentAudio: HTMLAudioElement | null = null;
let currentMessageId: string | null = null;
let progressCallback: ((progress: AudioProgress) => void) | null = null;

/**
 * Splits a large audio blob into smaller chunks
 */
const splitAudioIntoChunks = async (audioBlob: Blob): Promise<Blob[]> => {
  const chunks: Blob[] = [];
  let offset = 0;
  
  while (offset < audioBlob.size) {
    const chunk = audioBlob.slice(offset, offset + CHUNK_SIZE);
    chunks.push(chunk);
    offset += CHUNK_SIZE;
  }
  
  return chunks;
};

/**
 * Converts text to speech using either the ElevenLabs API or the mock API
 */
export const generateSpeech = async (
  text: string,
  speakerId: number,
  messageId?: string,
  onProgress?: (progress: AudioProgress) => void,
  context: Array<{
    text: string;
    speaker: number;
    audio: string;
  }> = [],
  voiceOptions?: VoiceOptions
): Promise<Blob> => {
  try {
    progressCallback = onProgress || null;
    const msgId = messageId || `msg_${Date.now()}`;

    // Check if we have cached audio for this message
    const cachedChunks = await audioCacheService.getAudioChunks(msgId);
    if (cachedChunks.length > 0) {
      console.log('🔄 Found cached audio chunks for message:', msgId);
      return new Blob(cachedChunks, { type: 'audio/mp3' });
    }

    // Check if we should use direct ElevenLabs integration
    const useDirectApi = import.meta.env.VITE_USE_DIRECT_TTS === 'true' || import.meta.env.VITE_USE_DIRECT_TTS === true;
    
    console.log('🔊 Generating speech...');
    console.log('🔧 Using direct ElevenLabs API:', useDirectApi);
    
    let audioBlob: Blob;
    if (useDirectApi) {
      try {
        console.log('🔌 Attempting to use ElevenLabs API directly');
        audioBlob = await generateSpeechWithElevenLabs(text, speakerId, voiceOptions);
      } catch (error) {
        console.error('❌ ElevenLabs API failed, falling back to mock API:', error);
        audioBlob = await generateSpeechWithMockApi(text, speakerId, context, voiceOptions);
      }
    } else {
      audioBlob = await generateSpeechWithMockApi(text, speakerId, context, voiceOptions);
    }

    // Split audio into chunks and cache them
    const chunks = await splitAudioIntoChunks(audioBlob);
    console.log(`Split audio into ${chunks.length} chunks`);

    // Cache each chunk
    for (let i = 0; i < chunks.length; i++) {
      await audioCacheService.cacheAudioChunk(msgId, chunks[i], i);
    }

    return audioBlob;
  } catch (error) {
    console.error('Error generating speech:', error);
    throw error;
  }
};

/**
 * Converts text to speech using the ElevenLabs API
 */
const generateSpeechWithElevenLabs = async (
  text: string, 
  speakerId: number, 
  voiceOptions?: VoiceOptions
): Promise<Blob> => {
  const apiKey = import.meta.env.VITE_ELEVENLABS_API_KEY;
  
  console.log('ElevenLabs API Key available:', !!apiKey);
  
  if (!apiKey) {
    throw new Error('ElevenLabs API key is not configured. Please add VITE_ELEVENLABS_API_KEY to your environment variables.');
  }
  
  // Map speaker ID to ElevenLabs voice ID and names
  // These are default voices available in all ElevenLabs accounts
  const voiceMap = [
    { id: 'ErXwobaYiN019PkySvjV', name: 'Antoni' },      // Marcus Aurelius - Antoni (deep authoritative male voice)
    { id: 'VR6AewLTigWG4xSOukaG', name: 'Arnold' },      // Seneca - Arnold (powerful male voice)
    { id: 'pNInz6obpgDQGcFmaJgB', name: 'Adam' }         // Epictetus - Adam (older male voice)
  ];
  
  // Check if we have cached voices from the user account
  let userVoices: ElevenLabsVoice[] = [];
  try {
    userVoices = await fetchElevenLabsVoices(apiKey);
    console.log(`Found ${userVoices.length} voices in your ElevenLabs account`);
    
    // Try to find voices by name as requested
    const marcusVoice = userVoices.find(v => v.name.toLowerCase().includes('clyde'));
    const senecaVoice = userVoices.find(v => 
      v.name.toLowerCase().includes('mark') && 
      (v.name.toLowerCase().includes('natural') || v.name.toLowerCase().includes('conversation'))
    );
    const epictetusVoice = userVoices.find(v => 
      v.name.toLowerCase().includes('grandpa') || 
      (v.name.toLowerCase().includes('spuds') && v.name.toLowerCase().includes('oxley'))
    );
    
    // Update voice map with found voices if they exist
    if (marcusVoice) {
      console.log(`Found custom voice for Marcus: ${marcusVoice.name} (${marcusVoice.voice_id})`);
      voiceMap[0] = { id: marcusVoice.voice_id, name: marcusVoice.name };
    }
    
    if (senecaVoice) {
      console.log(`Found custom voice for Seneca: ${senecaVoice.name} (${senecaVoice.voice_id})`);
      voiceMap[1] = { id: senecaVoice.voice_id, name: senecaVoice.name };
    }
    
    if (epictetusVoice) {
      console.log(`Found custom voice for Epictetus: ${epictetusVoice.name} (${epictetusVoice.voice_id})`);
      voiceMap[2] = { id: epictetusVoice.voice_id, name: epictetusVoice.name };
    }
  } catch (error) {
    console.warn('Could not fetch ElevenLabs voices, using default voices:', error);
  }
  
  if (speakerId < 0 || speakerId >= voiceMap.length) {
    throw new Error(`Invalid speaker ID: ${speakerId}. Must be between 0 and ${voiceMap.length - 1}.`);
  }
  
  const selectedVoice = voiceMap[speakerId];
  
  try {
    // ElevenLabs API endpoint for text-to-speech
    const endpoint = `https://api.elevenlabs.io/v1/text-to-speech/${selectedVoice.id}`;
    
    // Set voice settings with defaults or custom options
    const stability = voiceOptions?.stability !== undefined ? voiceOptions.stability : 0.5;
    const similarityBoost = voiceOptions?.similarityBoost !== undefined ? voiceOptions.similarityBoost : 0.75;
    const speed = voiceOptions?.speed !== undefined ? voiceOptions.speed : 1.0;
    const style = voiceOptions?.style !== undefined ? voiceOptions.style : 0.0;
    
    // Set up the request options
    const options = {
      method: 'POST',
      headers: {
        'Accept': 'audio/mpeg',
        'Content-Type': 'application/json',
        'xi-api-key': apiKey
      },
      body: JSON.stringify({
        text,
        model_id: 'eleven_monolingual_v1',
        voice_settings: {
          stability,
          similarity_boost: similarityBoost,
          style,
          use_speaker_boost: true
        },
        output_format: 'mp3_44100',
        speed
      })
    };
    
    console.log(`Making ElevenLabs API request using ${selectedVoice.name} voice (ID: ${selectedVoice.id})`);
    console.log(`Voice options: stability=${stability}, similarityBoost=${similarityBoost}, speed=${speed}, style=${style}`);
    
    const response = await fetch(endpoint, options);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('ElevenLabs API error:', errorText);
      
      // Check if the error is related to credit limits
      if (response.status === 429 || errorText.includes('credit') || errorText.includes('limit')) {
        console.log('⚠️ ElevenLabs credits may have run out, falling back to OpenAI TTS');
        return await generateSpeechWithOpenAI(text, voiceOptions);
      }
      
      throw new Error(`ElevenLabs API error: ${response.status} ${response.statusText}`);
    }
    
    return await response.blob();
  } catch (error) {
    console.error('Error with ElevenLabs TTS:', error);
    
    // If any error occurs, try OpenAI's TTS as a fallback
    console.log('⚠️ Error with ElevenLabs, falling back to OpenAI TTS');
    return await generateSpeechWithOpenAI(text, voiceOptions);
  }
};

/**
 * Fetches available voices from ElevenLabs account
 */
const fetchElevenLabsVoices = async (apiKey: string): Promise<ElevenLabsVoice[]> => {
  try {
    const response = await fetch('https://api.elevenlabs.io/v1/voices', {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'xi-api-key': apiKey
      }
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch voices: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    return data.voices || [];
  } catch (error) {
    console.error('Error fetching ElevenLabs voices:', error);
    return [];
  }
};

/**
 * Fallback to OpenAI's TTS API (using Ash voice) when ElevenLabs is unavailable
 */
const generateSpeechWithOpenAI = async (text: string, voiceOptions?: VoiceOptions): Promise<Blob> => {
  const apiKey = import.meta.env.VITE_OPENAI_API_KEY;
  
  console.log('OpenAI API Key available for TTS fallback:', !!apiKey);
  
  if (!apiKey) {
    throw new Error('OpenAI API key is not configured for TTS fallback.');
  }
  
  // OpenAI TTS endpoint
  const endpoint = 'https://api.openai.com/v1/audio/speech';
  
  // Map voice options to OpenAI format
  // OpenAI only supports speed adjustment
  const speed = voiceOptions?.speed !== undefined ? voiceOptions.speed : 1.0;
  
  // Voice mapping for different speakers
  const voiceMap = ['echo', 'fable', 'onyx', 'nova', 'shimmer', 'alloy'];
  const defaultVoice = 'onyx';
  
  // Select appropriate voice based on speaker ID or use default
  const voice = voiceMap[0] || defaultVoice;
  
  // Set up the request options
  const options = {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
      'OpenAI-Organization': 'org-q2FnHJDFUAA89gSEDNw4uTgi',
    },
    body: JSON.stringify({
      model: 'tts-1',
      voice: voice,
      input: text,
      speed: speed
    })
  };
  
  console.log(`Using OpenAI TTS with ${voice} voice as fallback (speed: ${speed})`);
  
  const response = await fetch(endpoint, options);
  
  if (!response.ok) {
    const errorText = await response.text();
    console.error('OpenAI TTS API error:', errorText);
    throw new Error(`OpenAI TTS API error: ${response.status} ${response.statusText}`);
  }
  
  return await response.blob();
};

/**
 * Converts text to speech using the mock API endpoint
 */
const generateSpeechWithMockApi = async (
  text: string,
  speakerId: number,
  context: Array<{
    text: string;
    speaker: number;
    audio: string;
  }> = [],
  voiceOptions?: VoiceOptions
): Promise<Blob> => {
  const response = await fetch(`${API_ENDPOINTS.baseUrl}${API_ENDPOINTS.tts}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      text,
      speaker: speakerId,
      context,
      voiceOptions
    }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to generate speech with mock API');
  }

  return await response.blob();
};

/**
 * Plays audio from a blob with progressive loading and caching support
 */
export const playAudio = async (audioBlob: Blob, messageId: string): Promise<void> => {
  return new Promise((resolve, reject) => {
    try {
      // Stop any currently playing audio and save its state
      if (currentAudio && currentMessageId) {
        const currentTime = currentAudio.currentTime;
        audioCacheService.saveConversationState(
          currentMessageId,
          messageId,
          currentTime,
          'paused'
        );
        currentAudio.pause();
      }

      // Split audio into chunks if needed
      splitAudioIntoChunks(audioBlob).then(async chunks => {
        // Create new audio element
        const audio = new Audio();
        currentAudio = audio;
        currentMessageId = messageId;

        let currentChunkIndex = 0;
        const totalChunks = chunks.length;

        // Set up progress tracking
        audio.addEventListener('timeupdate', () => {
          if (progressCallback) {
            progressCallback({
              loaded: audio.currentTime,
              total: audio.duration || 0,
              buffered: audio.buffered,
              currentChunk: currentChunkIndex,
              totalChunks
            });
          }
        });

        // Check for previous playback position
        const state = await audioCacheService.getConversationState(messageId);
        if (state && state.lastAudioPosition > 0) {
          audio.currentTime = state.lastAudioPosition;
          currentChunkIndex = Math.floor((state.lastAudioPosition / (audio.duration || 1)) * totalChunks);
        }

        // Set up event listeners
        audio.addEventListener('ended', () => {
          currentAudio = null;
          currentMessageId = null;
          audioCacheService.saveConversationState(
            messageId,
            messageId,
            0,
            'completed'
          );
          resolve();
        });

        audio.addEventListener('error', (error) => {
          console.error('Error playing audio:', error);
          reject(error);
        });

        // Buffer management
        audio.addEventListener('progress', async () => {
          const buffered = audio.buffered.length > 0 ? 
            audio.buffered.end(audio.buffered.length - 1) : 0;
          
          // Load more chunks if buffer is running low
          if (currentChunkIndex < totalChunks && 
              buffered - audio.currentTime < BUFFER_THRESHOLD * CHUNK_SIZE) {
            try {
              // Load next chunk
              const nextChunk = chunks[currentChunkIndex++];
              if (nextChunk) {
                const chunkUrl = URL.createObjectURL(nextChunk);
                // Append to audio source
                if (audio.src) {
                  const existingBlob = await fetch(audio.src).then(r => r.blob());
                  const newBlob = new Blob([existingBlob, nextChunk], { type: 'audio/mp3' });
                  URL.revokeObjectURL(audio.src);
                  audio.src = URL.createObjectURL(newBlob);
                } else {
                  audio.src = chunkUrl;
                }
              }
            } catch (error) {
              console.error('Error loading next chunk:', error);
            }
          }
        });

        // Start with first chunk
        if (chunks.length > 0) {
          audio.src = URL.createObjectURL(chunks[0]);
          currentChunkIndex = 1;
          
          // Start playback
          audio.play().catch(error => {
            console.error('Error starting audio playback:', error);
            reject(error);
          });

          // Save initial state
          audioCacheService.saveConversationState(
            messageId,
            messageId,
            0,
            'playing'
          );
        }
      }).catch(error => {
        console.error('Error splitting audio into chunks:', error);
        reject(error);
      });
    } catch (error) {
      console.error('Error in playAudio:', error);
      reject(error);
    }
  });
};

/**
 * Stops currently playing audio and saves state
 */
export const stopAudio = async (): Promise<void> => {
  if (currentAudio && currentMessageId) {
    const currentTime = currentAudio.currentTime;
    await audioCacheService.saveConversationState(
      currentMessageId,
      currentMessageId,
      currentTime,
      'paused'
    );
    currentAudio.pause();
    currentAudio = null;
    currentMessageId = null;
  }
};

/**
 * Helper function to convert a Blob to base64 string
 */
export const blobToBase64 = (blob: Blob): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      if (typeof reader.result === 'string') {
        resolve(reader.result);
      } else {
        reject(new Error('Failed to convert blob to base64'));
      }
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}; 