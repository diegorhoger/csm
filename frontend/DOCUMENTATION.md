# Council: Emotionally Intelligent Stoic Mentor Documentation

## Project Overview

Council is an emotionally intelligent, voice-first AI mentor designed to guide users through an inner journey of growth using real-time emotion recognition, stoic philosophy, and advanced conversational intelligence. The application enables users to select a mentor from a list of famous stoic philosophers, engage in voice conversations, and receive philosophical guidance that adapts to their emotional state.

## Design Decisions

### Architecture

The project is structured as a client-server application:

1. **Frontend**: React application built with Vite and styled with Tailwind CSS
2. **Backend**: Flask API server that provides endpoints for:
   - Health checking
   - Mentor information retrieval
   - Text-to-speech conversion
   - Speech-to-text transcription
   - AI-powered mentor responses via OpenAI integration
   - Emotion analysis and Hawkins Scale mapping
   - WebSocket-based Voice Activity Detection (VAD)
   - Ethical filtering based on the Council AI Constitution

### API Design

The API is designed to be RESTful with WebSocket components:

- `GET /api/health`: Check if the API server is running
- `GET /api/mentors`: Retrieve available mentor personalities
- `POST /api/transcribe`: Transcribe speech to text using OpenAI Whisper
- `POST /api/mentor-chat`: Generate mentor responses based on emotional state
- `POST /api/tts`: Convert text to speech with voice profiles matched to mentors
- `WebSocket`: Real-time voice activity detection and audio processing

### Database Integration

The application integrates with Supabase for:
- User authentication and profiles
- Conversation history persistence
- Emotional state tracking
- Journal entries and insights
- Vector storage for semantic retrieval
- Row-level security for data protection

### Emotion Intelligence System

A core feature of Council is its emotion intelligence system:

1. **Text-Based Emotion Analysis**: Uses pre-trained models (DistilBERT) to detect emotions from text
2. **Hawkins Energy Scale**: Maps emotions to a 5-7 tiered scale from shame to peace
3. **Dynamic Mentor Selection**: Chooses the appropriate mentor based on emotional state
4. **Emotion Trajectory Tracking**: Records emotional changes during conversations
5. **Ethical Filtering**: Ensures responses align with the Council AI Constitution

## Technical Challenges & Solutions

### Existing Challenges (Previously Documented)

#### Challenge 1: CSM Model Dependencies

**Problem**: The original CSM model had complex dependencies including Triton, which caused import errors and tensor shape mismatches.

**Solution**: Created a mock implementation that:
- Disables Triton dependencies through environment variables
- Implements a `TritonMock` class to handle import attempts
- Creates simplified mock classes that match the CSM API

#### Challenge 2: Port Conflicts

**Problem**: Default port 5000 was occupied by AirPlay Receiver on macOS.

**Solution**: Changed API server to run on port 5001 and updated API endpoints accordingly.

#### Challenge 3: Tailwind CSS Configuration

**Problem**: PostCSS error occurred due to incorrect configuration with ES modules.

**Solution**: 
- Updated configuration to use ES module syntax (export default)
- Reinstalled packages with correct versions
- Updated import statements to use @tailwindcss/postcss

### New Challenges & Solutions

#### Challenge 4: Implementing Emotion Analysis

**Problem**: Detecting user emotions accurately from text requires sophisticated NLP capabilities.

**Solution**: 
- Integrated pre-trained DistilBERT model for sentiment and emotion classification
- Created mapping system to translate detected emotions to the Hawkins Energy Scale
- Implemented confidence thresholds to avoid misclassification
- Added context-aware emotion tracking that considers conversation history

#### Challenge 5: Silero VAD Integration

**Problem**: The existing VAD system, while functional, needed enhancement for more accurate speech detection.

**Solution**:
- Integrated Silero VAD as an enhancement to the current audio analysis service
- Maintained existing WebSocket infrastructure and session management
- Implemented as an enhancement rather than replacement to retain local VAD as fallback
- Added performance monitoring to compare Silero vs RMS approaches

#### Challenge 6: Ethical Filtering System

**Problem**: Ensuring AI responses maintain alignment with stoic philosophical principles without introducing manipulative patterns or reinforcing negative emotions.

**Solution**:
- Implemented the Council AI Constitution as a validation system
- Created a rule-based filtering middleware for all mentor responses
- Added violation detection and response refinement
- Implemented logging system for ethical interventions

## Dependencies

### Frontend
- React 19.0.0
- TypeScript
- Vite 6.2.0
- Tailwind CSS 4.1.1
- Zustand 5.0.3 (State Management)
- TanStack Query 5.71.3 (Data Fetching)
- Web Audio API

### Backend
- Flask 2.3.3
- Flask-SocketIO 5.3.6
- Flask-CORS 4.0.0
- OpenAI API
- NumPy
- Silero VAD
- Supabase (PostgreSQL + GraphQL)

## Core Components

### Hawkins Energy Scale

The Hawkins Scale measures emotional energy levels:

```typescript
export enum HawkinsLevel {
  Shame = 0,      // 0-199: Deep negativity, worthlessness
  Fear = 1,       // 200-299: Anxiety, worry, insecurity
  Anger = 2,      // 300-399: Frustration, resentment
  Neutral = 3,    // 400-499: Neither positive nor negative
  Acceptance = 4, // 500-599: Openness, tolerance
  Reason = 5,     // 600-699: Clarity, rationality
  Peace = 6       // 700+: Equanimity, wisdom, presence
}
```

### Emotion-Based Mentor Selection

```typescript
export const mentorMap = {
  [HawkinsLevel.Shame]: 'seneca',     // Seneca excels at addressing shame
  [HawkinsLevel.Fear]: 'epictetus',   // Epictetus addresses fear directly
  [HawkinsLevel.Anger]: 'seneca',     // Seneca helps with anger management
  [HawkinsLevel.Neutral]: 'marcus',   // Marcus is balanced for neutral states
  [HawkinsLevel.Acceptance]: 'marcus', // Marcus reinforces acceptance
  [HawkinsLevel.Reason]: 'epictetus', // Epictetus strengthens reason
  [HawkinsLevel.Peace]: 'marcus'      // Marcus deepens peace
};
```

### Enhanced Mentor Definitions

```typescript
export const mentors = {
  marcus: {
    name: 'Marcus Aurelius',
    prompt: 'You are Marcus Aurelius...',
    voiceId: 'marcus-v1',
    style: 'calm',
    specializations: [HawkinsLevel.Acceptance, HawkinsLevel.Peace],
    emotionalTriggers: {
      // Specific emotional words that trigger this mentor
      positive: ['gratitude', 'acceptance', 'duty'],
      negative: ['obligation', 'responsibility', 'burden']
    }
  },
  seneca: {
    name: 'Seneca',
    prompt: 'You are Seneca...',
    voiceId: 'seneca-v1',
    style: 'motivational',
    specializations: [HawkinsLevel.Shame, HawkinsLevel.Anger],
    emotionalTriggers: {
      positive: ['healing', 'growth', 'change'],
      negative: ['failure', 'shame', 'anger']
    }
  },
  epictetus: {
    name: 'Epictetus',
    prompt: 'You are Epictetus...',
    voiceId: 'epictetus-v1',
    style: 'firm',
    specializations: [HawkinsLevel.Fear, HawkinsLevel.Reason],
    emotionalTriggers: {
      positive: ['control', 'choice', 'freedom'],
      negative: ['victim', 'fear', 'anxiety']
    }
  }
};
```

## UI Components

### Core Components
- **MentorCallUI**: Main interface orchestrating the conversation
- **EmotionTracker**: Displays and tracks emotional state using the Hawkins Scale
- **MentorSwitcher**: Interface for switching between mentors
- **JournalInterface**: Displays conversation history and insights
- **ConversationUI**: Main interface for the conversation experience
- **TranscriptBox**: Displays user and mentor text with appropriate styling

### UI Components
- **WaveformVisualizer**: Visual representation of audio levels during recording and playback
- **EmotionVisualizer**: Visual representation of Hawkins Energy Scale
- **VoiceCustomizationControls**: Controls for voice customization
- **VoiceButton**: Interactive button for recording with visual feedback

## Recent Changes

### Council Vision Implementation

**Change**: Transformed Stoic Mentor into Council, an emotionally intelligent AI mentor system with Hawkins Energy Scale tracking, dynamic mentor selection, and ethical safeguards.

**Rationale**: While the original Stoic Mentor provided valuable philosophical guidance, the Council vision enhances this with emotion intelligence that enables more personalized mentorship adapted to the user's emotional state.

**Implementation Details**:
- Added text-based emotion analysis using pre-trained DistilBERT model
- Created Hawkins Energy Scale mapping (5-7 levels: Shame → Anger → Neutral → Acceptance → Peace)
- Implemented emotion trajectory tracking over conversation sessions
- Added dynamic mentor selection based on emotional state
- Integrated ethical filter based on the Council AI Constitution
- Set up Supabase integration for authentication and persistent storage

**Impact**: Users now experience:
- Mentorship that adapts to their emotional state
- More personalized guidance tailored to their needs
- Visual tracking of their emotional journey
- Ethical safeguards that ensure helpful, non-manipulative responses

### Silero VAD Integration

**Change**: Enhanced the existing WebSocket VAD system with Silero VAD.

**Rationale**: While our WebSocket VAD system was functional, integrating Silero VAD provides more accurate speech detection using ML-based techniques while maintaining the robustness of our existing architecture.

**Implementation Details**:
- Added Silero VAD as a module behind existing audio analysis layer
- Maintained current WebSocket architecture and session management
- Implemented as an enhancement rather than replacement
- Retained local VAD as fallback system
- Added performance monitoring to compare approaches

**Impact**: Users experience:
- More accurate speech detection across different environments
- Better handling of background noise
- Improved silence detection for natural conversation flow
- Consistent performance across different devices and browsers

### Enhanced Mentor Voice System with Customization and Emotion Detection

**Change**: Enhanced the voice system with customization options, adaptive emotion detection, and improved fallback mechanisms.

**Rationale**: The original voice system provided basic text-to-speech conversion but lacked customization options and the ability to adapt to different conversation contexts. This enhancement makes the Stoic mentors' voices more natural and expressive.

**Implementation Details**:
- Added voice customization controls (speed, stability, clarity, style) to the UI
- Implemented speech emotion detection to adapt voice characteristics to conversation context
- Enhanced fallback mechanisms using OpenAI's TTS when ElevenLabs is unavailable
- Created profiles for different emotional states to dynamically adjust voice parameters
- Improved voice caching for better performance and reduced API calls
- Added support for multiple voice providers with graceful degradation

**Technical Approach**:
1. Created a new `VoiceCustomizationControls` component for the UI
2. Enhanced `ttsService.ts` to support customization parameters in API requests
3. Implemented emotion detection algorithm to analyze text sentiment
4. Created emotion-specific voice profiles that adjust parameters automatically
5. Updated `useMentorCallEngine` to incorporate adaptive voice based on conversation context
6. Added a flag for user customization to ensure preferences are respected

**Impact**: Users now experience:
- More natural and expressive Stoic mentor voices that adapt to conversation
- Ability to customize voice characteristics to their preference
- Improved voice quality and reliability with better fallback systems
- Voices that respond emotionally to different philosophical topics
- Seamless integration with their chosen mentor's personality

### Fixed WebSocket VAD Integration for Silence Detection

**Change**: Fixed WebSocket VAD integration to properly handle silence detection and improve cross-origin resource sharing (CORS).

**Rationale**: The WebSocket VAD system was experiencing connection issues and CORS errors that prevented proper silence detection, which is crucial for a natural conversation flow where the system needs to detect when the user has stopped speaking.

**Implementation Details**:
- Modified Socket.io client configuration to use both WebSocket and polling transports for better fallback support
- Added explicit path, timeout, and connection options to ensure robust WebSocket connections
- Enhanced the useSocketVad hook to better handle speaking/silent states with dedicated event handlers
- Added comprehensive debugging tools and UI elements to monitor VAD state
- Improved the Flask backend's CORS configuration to accept connections from all required origins
- Added a dedicated OPTIONS route handler for Socket.io to properly handle preflight requests
- Enhanced silence detection logic in useMentorCallEngine to respond more reliably to VAD events

**Technical Approach**:
1. Identified CORS issues through browser console analysis and addressed each with proper headers
2. Implemented a more robust Socket.io client configuration with appropriate error handling
3. Added dedicated event handlers for VAD_RESULT, SPEECH_START, and SPEECH_END events
4. Created a debug panel in the UI to display real-time WebSocket VAD status
5. Enhanced logging both client-side and server-side to trace connection issues

**Impact**: Users now experience:
- More reliable silence detection that properly ends recording when they stop speaking
- Fewer connection errors and more stable WebSocket connections
- Better cross-browser and cross-origin compatibility
- Improved debug information to troubleshoot any remaining issues
- A more natural conversation flow with the Stoic mentors

### Implemented OpenAI API Integration for Authentic Stoic Responses

**Change**: Enhanced the backend to forward requests to the OpenAI API instead of generating mock responses.

**Rationale**: While the mock backend provided reliable responses, integrating with OpenAI's GPT-4 model offers more dynamic, contextually aware responses that can address a wider range of philosophical questions while maintaining the authentic voice of each Stoic mentor.

**Implementation Details**:
- Added OpenAI Python library integration in the Flask backend
- Created detailed system prompts for each Stoic philosopher that capture their unique voice and teaching style
- Implemented proper conversation history handling for contextual awareness
- Added robust error handling with fallback to mock responses when API calls fail
- Maintained the sanitization pipeline to remove unwanted acknowledgment phrases
- Added comprehensive logging to trace the request/response flow

**Impact**: Users now experience:
- More dynamic and nuanced philosophical responses from each Stoic mentor
- Contextually aware conversations that reference previous exchanges
- Authentic Stoic wisdom that maintains the distinctive voice of each philosopher
- Seamless fallback to reliable mock responses if API issues occur

### Enhanced Stoic Mentor Prompts

**Change**: Reimplemented the mentor prompt system to provide more immersive, emotionally supportive responses that authentically reflect the distinct voices of each Stoic mentor.

**Rationale**: The previous system used simple static prompts that didn't fully capture the unique personalities and teaching styles of the Stoic mentors. The new implementation:
1. Creates a dedicated module for mentor prompts with more nuanced character guidance
2. Provides both verbose and concise prompt options for different use cases
3. Includes specific tone guides for each mentor to ensure authentic role-playing

**Implementation Details**:
- Created a new `mentorPrompts.ts` file with enhanced prompt templates
- Updated the `openaiService.ts` to use the new mentor prompts system
- Modified the `createSystemPrompt` function to accept a mentor name rather than a prompt string
- Updated the API service to generate responses using the new prompt system
- Removed static prompt strings from the mentor personalities in constants

**Impact**: The application now provides more authentic and personality-driven responses from each Stoic mentor. Users will experience:
- More emotionally resonant guidance tailored to each mentor's unique perspective
- Responses that better reflect the historical teaching style of each philosopher
- Interactions that feel like true mentorship rather than generic philosophical advice

## Development Roadmap

### Phase 1: Core MVP (Weeks 1-4)
- Text-based Emotion Engine
- Mentor Selection System
- Silero VAD Integration
- Basic Supabase Integration
- Constitutional Ethical Filter

### Phase 2: Growth Layer (Weeks 5-8)
- Journal & Memory Features
- Vector Storage & Retrieval
- RLHF Foundation
- Mobile Optimization

### Phase 3: Advanced Features (Future)
- Audio-based Emotion Detection
- Full 100+ Mentor Architecture
- Complete RLHF System
- Edge/Offline Deployment

## Project Documentation Structure

All project documentation is now located in the `/docs` directory:

- `ARCHITECTURE.md`: System architecture and component organization
- `PLAN.md`: Implementation plan with priorities and timeline
- `PRD.md`: Product requirements and feature specifications
- `Council AI Constitution V1.md`: Ethical principles and guidelines

## API Endpoints

The following API endpoints are available:

- `GET /api/health`: Health check endpoint
- `GET /api/mentors`: Get available mentor personalities
- `POST /api/tts`: Convert text to speech with mentor-specific voices
- `POST /api/transcribe`: Transcribe speech to text using OpenAI Whisper
- `POST /api/mentor-chat`: Generate mentor response using OpenAI API with emotional context
- `WebSocket`: Real-time voice activity detection and emotion tracking

## TTS Implementation

The application implements a multi-tier system for text-to-speech:

1. **Primary TTS Engine**: Using voice profiles matched to each mentor
2. **Emotion-Adaptive Voice Parameters**: Adjusting voice characteristics based on emotional context
3. **Fallback Mechanisms**: Ensuring audio output even if primary systems fail

## Future Enhancements

- **Paralinguistic Emotion Detection**: Add audio-based emotion analysis
- **Advanced Journaling**: Enhance the journaling system with AI insights
- **Full RLHF Implementation**: Complete the reinforcement learning from human feedback system
- **Multi-Modal Interface**: Add visual emotion recognition
- **Expanded Mentor Database**: Implement the full 100+ mentor architecture

## WebSocket-Based Voice Activity Detection (VAD)

**Change**: Implemented WebSocket-based Voice Activity Detection

**Rationale**: The previous approach to Voice Activity Detection (VAD) relied on client-side processing only, which led to inconsistent results across different devices and browsers. By moving to a WebSocket-based architecture, we gain several advantages:

1. More consistent and reliable speech detection across devices and browsers
2. Access to more powerful audio processing libraries (like WebRTC VAD) on the backend
3. Adaptive thresholding and noise floor calibration
4. Ensemble approach combining multiple detection methods
5. Reduced client-side computational requirements

**Implementation Details**:

1. **Backend VAD Service**
   - Created a Socket.IO-based WebSocket service in Flask
   - Implemented a session-based architecture to maintain user state
   - Combined RMS-based adaptive thresholding with WebRTC VAD
   - Added dynamic calibration and configuration options
   - Provided fine-tuning parameters for sensitivity and aggressiveness

2. **Frontend Integration**
   - Developed `socketVadService.ts` for WebSocket communication with the backend
   - Created `useSocketVad` React hook for easy integration with components
   - Implemented audio processing and streaming pipeline
   - Added event-based architecture for speech detection events
   - Built robust reconnection and error handling

3. **Demo Component**
   - Created `WebSocketVadDemo.tsx` to demonstrate the WebSocket VAD capabilities
   - Added visual feedback for audio levels and thresholds
   - Implemented controls for configuring VAD parameters
   - Added debug information display

**Impact**: Users now experience:
   - More reliable and consistent speech detection
   - Better handling of different noise environments
   - Reduced false positives and negatives in speech detection
   - More natural conversation flow
   - Adaptive behavior that works across different microphones and devices

**Usage Example**:
```typescript
// Using the WebSocket VAD hook in a component
const {
  isSpeaking,
  audioLevel,
  threshold,
  startAudioProcessing,
  stopAudioProcessing
} = useSocketVad({
  autoConnect: true,
  autoInit: true,
  onSpeakingChange: (speaking) => {
    console.log('Speaking state changed:', speaking);
    // Handle speaking state changes
  }
});

// Start audio processing when needed
useEffect(() => {
  if (isListening) {
    startAudioProcessing();
    return () => stopAudioProcessing();
  }
}, [isListening]);
``` 