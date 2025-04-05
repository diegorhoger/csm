import { API_ENDPOINTS } from '../constants/app';
import { createSystemPrompt } from './openaiService';

// Types
export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface MentorChatOptions {
  model?: string;
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
  signal?: AbortSignal;
  conversation_id?: string;
}

export interface MentorProfile {
  id: string;
  name: string;
  style: string;
  title: string;
  years: string;
  image: string;
  description: string;
  voiceId: string;
  voice: string;
}

/**
 * Fetch available mentors from the backend
 */
export const fetchMentors = async (): Promise<MentorProfile[]> => {
  try {
    const response = await fetch(`${API_ENDPOINTS.baseUrl}${API_ENDPOINTS.mentors}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch mentors: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching mentors:', error);
    throw error;
  }
};

/**
 * Generate a chat completion using the backend API
 */
export const generateMentorCompletion = async (
  messages: ChatMessage[],
  options: MentorChatOptions = {}
): Promise<{ content: string; conversation_id: string }> => {
  try {
    const response = await fetch(`${API_ENDPOINTS.baseUrl}${API_ENDPOINTS.mentorChat}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        messages,
        model: options.model || 'gpt-4o',
        temperature: options.temperature || 0.7,
        max_tokens: options.max_tokens || 1000,
        stream: false,
        conversation_id: options.conversation_id
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to generate mentor response');
    }

    return await response.json();
  } catch (error) {
    console.error('Error generating mentor chat completion:', error);
    throw error;
  }
};

/**
 * Stream a chat completion from the backend API
 */
export async function* streamMentorCompletion(
  messages: ChatMessage[],
  options: MentorChatOptions = {}
): AsyncGenerator<string> {
  try {
    console.log('Streaming mentor chat from backend:', messages.length, 'messages');
    
    const response = await fetch(`${API_ENDPOINTS.baseUrl}${API_ENDPOINTS.mentorChat}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        messages,
        model: options.model || 'gpt-4o',
        temperature: options.temperature || 0.7,
        max_tokens: options.max_tokens || 1000,
        stream: true,
        conversation_id: options.conversation_id
      }),
      signal: options.signal,
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend API error:', errorText);
      throw new Error(`Error streaming from backend: ${response.status}`);
    }

    if (!response.body) {
      throw new Error('Response body is null');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      
      if (done) {
        console.log('Stream complete');
        break;
      }

      const chunk = decoder.decode(value, { stream: true });
      buffer += chunk;

      // Process complete SSE lines
      let lineEnd;
      while ((lineEnd = buffer.indexOf('\n\n')) !== -1) {
        const line = buffer.slice(0, lineEnd).trim();
        buffer = buffer.slice(lineEnd + 2);

        if (line.startsWith('data: ')) {
          const data = line.slice(5).trim();
          
          try {
            const parsed = JSON.parse(data);
            
            if (parsed.done) {
              console.log('Stream done marker received');
              return;
            }
            
            if (parsed.error) {
              throw new Error(parsed.error);
            }
            
            if (parsed.content) {
              yield parsed.content;
            }
          } catch (error) {
            console.error('Error parsing JSON from stream:', error, 'Line:', line);
          }
        }
      }
    }
  } catch (error) {
    console.error('Error streaming mentor chat:', error);
    throw error;
  }
}

/**
 * Transcribe audio using the backend API
 */
export const transcribeAudioWithBackend = async (audioBlob: Blob): Promise<string> => {
  console.log('🎤 Transcribing audio with backend API...');
  console.log('📦 Audio blob size:', audioBlob.size);
  
  try {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'audio.wav');

    console.log(`🎤 Sending request to ${API_ENDPOINTS.baseUrl}${API_ENDPOINTS.transcribe}`);
    
    const response = await fetch(`${API_ENDPOINTS.baseUrl}${API_ENDPOINTS.transcribe}`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend transcription error:', errorText);
      throw new Error(`Failed to transcribe audio with backend API: ${response.status}`);
    }

    const result = await response.json();
    console.log('🎤 Transcription result:', result);
    
    // Handle both formats for backward compatibility
    return result.text || result.transcription || '';
  } catch (error) {
    console.error('Error with backend transcription:', error);
    throw error;
  }
};

/**
 * Prepare a conversation with a mentor
 */
export const prepareMentorConversation = (
  mentorId: string,
  userMessage: string,
  conversationContext?: string
): ChatMessage[] => {
  // Create the system prompt for the mentor
  const systemPrompt = createSystemPrompt(mentorId, conversationContext);
  
  // Return the messages array with system prompt and user message
  return [
    { role: 'system', content: systemPrompt },
    { role: 'user', content: userMessage }
  ];
};

/**
 * Check if a service is available by testing the health endpoint
 */
export const checkMentorServiceHealth = async (): Promise<boolean> => {
  try {
    const response = await fetch(`${API_ENDPOINTS.baseUrl}${API_ENDPOINTS.health}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    return response.ok;
  } catch (error) {
    console.error('Error checking mentor service health:', error);
    return false;
  }
}; 