# System Architecture: Council App (Emotion-Intelligent Stoic Mentor)

## 📦 Code Organization

```
Project Root/
├── backend/
│   ├── api.py                    # Main Flask/SocketIO API
│   ├── audio_analysis_service.py # Audio analysis for VAD 
│   ├── socket_vad_service.py     # WebSocket VAD service
│   ├── silero_vad_service.py     # Silero ML-based VAD enhancement
│   ├── emotion_service.py        # Text-based emotion analysis
│   ├── mentor_service.py         # Mentor selection and management
│   ├── ethics_service.py         # Constitutional ethical filter
│   ├── static/                   # Static assets and test files
│   ├── requirements.txt          # Backend dependencies
│   └── README.md                 # Backend documentation
│
└── frontend/               # Frontend application (Council)
    ├── src/
    │   ├── components/         # UI components (reusable, composable)
    │   │   ├── UI/             # Visual interface components
    │   │   ├── core/           # Core application components
    │   │   └── layout/         # Layout and structure components
    │   ├── hooks/              # Custom React hooks
    │   ├── services/           # API wrappers, models, TTS, Whisper, etc.
    │   ├── state/              # Global state stores
    │   ├── pages/              # Entry points per route
    │   ├── utils/              # Small reusable helpers
    │   ├── types/              # Shared types & interfaces
    │   ├── constants/          # App-wide configuration
    │   └── config/             # Configuration files
    ├── public/                 # Static assets
    └── ...                     # Other frontend files
```

## 🎯 Architecture Overview

The system follows a client-server architecture with enhanced emotion intelligence:

1. **Backend** (Flask/SocketIO + Supabase)
   - Handles all OpenAI API interactions (GPT, Whisper)
   - Provides WebSocket-based Voice Activity Detection with Silero enhancement
   - Performs text-based emotion analysis
   - Implements Hawkins Energy Scale mapping
   - Provides mentor selection based on emotional state
   - Filters responses through ethical advisor
   - Manages conversation sessions and state
   - Stores data in Supabase (PostgreSQL)

2. **Frontend** (React/TypeScript)
   - Manages user interface and interactions
   - Handles audio recording and processing
   - Visualizes emotional state and trajectory
   - Communicates with backend via REST APIs and WebSockets
   - Manages local state and conversation flow
   - Provides journaling and memory interfaces

## 🔄 Communication Flow

1. **Voice Input & Emotion Analysis Flow**
   - User speaks → Browser records audio
   - Audio chunks sent to WebSocket VAD service (enhanced with Silero)
   - VAD detects speech start/end
   - Complete audio recording sent to backend transcription endpoint
   - Transcribed text analyzed for emotional content
   - Emotion mapped to Hawkins Energy Scale
   - Emotional state stored and tracked
   - Transcribed text displayed to user

2. **Mentor Selection & Response Flow**
   - Current emotional state determines optimal mentor
   - Selected mentor's prompt and configuration retrieved
   - User message and emotional context sent to mentor chat endpoint
   - Ethical filter validates and ensures response compliance
   - Backend calls OpenAI API with appropriate mentor context
   - Response streamed back to frontend
   - Frontend displays and plays back response
   - Emotional impact assessed for feedback system

3. **Session & Memory Flow**
   - Conversation and emotional states persisted to Supabase
   - Session summarization for journaling
   - Quote extraction and categorization
   - Vector embeddings for future retrieval
   - Emotional trajectory visualization

## 🧠 Core Components

### Backend Services

- **API Layer** (`api.py`): Main Flask application with REST endpoints
- **Socket VAD Service** (`socket_vad_service.py`): WebSocket-based Voice Activity Detection
- **Silero VAD Service** (`silero_vad_service.py`): ML-based voice detection
- **Audio Analysis** (`audio_analysis_service.py`): Audio processing and analysis
- **Emotion Service** (`emotion_service.py`): Text-based emotion detection and Hawkins mapping
- **Mentor Service** (`mentor_service.py`): Mentor selection and configuration
- **Ethics Service** (`ethics_service.py`): Constitutional rule-based filtering
- **Supabase Integration**: Database and authentication services

### Frontend Components

#### Core Components
- **MentorCallUI**: Main interface orchestrating the conversation
- **EmotionTracker**: Displays and tracks emotional state
- **MentorSwitcher**: Interface for switching between mentors
- **JournalInterface**: Displays conversation history and insights

#### UI Components
- **WaveformVisualizer**: Visual representation of audio
- **EmotionVisualizer**: Visual representation of Hawkins level
- **VoiceCustomizationControls**: Controls for voice customization

### Frontend Hooks
- **useMentorCallEngine**: Orchestrates the entire conversation flow
- **useMicStream**: Manages microphone access and audio recording
- **useSocketVad**: Connects to WebSocket VAD service for speech detection
- **useVoiceActivityDetection**: Coordinates voice activity state
- **useEmotionAnalysis**: Tracks and analyzes emotional state

### Frontend Services
- **mentorService.ts**: Handles backend API communication for mentor interactions
- **socketVadService.ts**: Manages WebSocket connection and events
- **emotionService.ts**: Handles emotion tracking and analysis
- **ethicsService.ts**: Communicates with ethics filter
- **supabaseService.ts**: Handles database operations
- **ttsService.ts**: Manages text-to-speech playback

## 🔐 Security Considerations

1. **API Key Management**
   - All API keys stored securely on backend
   - No keys exposed to frontend
   - Usage monitoring and rate limiting

2. **Data Privacy**
   - Emotion data stored with user consent only
   - Clear opt-in for data collection
   - User ability to delete emotional history
   - End-to-end encryption for sensitive data

3. **Network Security**
   - CORS restrictions properly configured
   - WebSocket secure connection options
   - Input validation on all API endpoints
   - Supabase row-level security policies

## 🔍 Diagnostic Tools

1. **WebSocket Test Page**
   - Available at `/test` endpoint
   - Tests WebSocket connections
   - Tests API endpoints
   - Tests audio recording and transcription
   - Tests emotion detection accuracy

2. **Logging System**
   - Comprehensive logging in both frontend and backend
   - WebSocket connection diagnostics
   - Audio processing metrics
   - Emotion detection verification
   - Ethical filter interventions

## 🚀 Performance Considerations

1. **WebSocket Optimization**
   - Efficient binary data transfer
   - Proper error handling and reconnection
   - Configurable VAD sensitivity
   - Silero VAD for improved accuracy

2. **Emotion Analysis Performance**
   - Lightweight models for real-time analysis
   - Caching of emotion detection results
   - Batched processing for efficiency
   - Progressive enhancement based on capability

3. **Response Streaming**
   - Real-time streaming of API responses
   - Progressive rendering of mentor replies
   - Low-latency playback
   - Emotion-adaptive response generation

## 📈 Scalability Design

The system is designed to scale through:

1. **Stateless API Design**
   - Each request contains necessary context
   - Sessions managed via identifiers
   - Minimal server-side state
   - Supabase for persistent storage

2. **Efficient Resource Usage**
   - Audio processing optimized for size and quality
   - WebSocket connections properly closed when inactive
   - Temporary files cleaned up promptly
   - Caching of frequent operations

3. **Modular Architecture**
   - Clear separation between components
   - Well-defined interfaces
   - Isolated responsibilities
   - Ability to scale individual services

## 🧪 Testing Approach

1. **Unit Testing**
   - Individual services and hooks tested in isolation
   - Mock implementations for external dependencies
   - Emotion detection accuracy testing

2. **Integration Testing**
   - API endpoint tests
   - WebSocket communication tests
   - Full conversation flow tests
   - Emotion tracking verification

3. **Ethical Testing**
   - Constitutional rule adherence tests
   - Edge case handling for ethical dilemmas
   - Rejection of manipulative responses

## 🧠 Emotion Intelligence Architecture

1. **Text-Based Emotion Detection**
   - Uses pre-trained DistilBERT model
   - Identifies emotions from transcribed text
   - Extracts sentiment scores and categories
   - Maps to Hawkins Energy Scale
   - Stores trajectory for tracking
   
2. **Hawkins Scale Implementation**
   - 5-7 tiered system from negative to positive states
   - Numerical mapping for granular tracking
   - Visualization components for frontend display
   - Trajectory tracking over time
   
3. **Emotion-Mentor Mapping**
   - Defines which mentors are optimal for which emotional states
   - Creates dynamic prompt modifications based on emotional context
   - Guides mentor switching decisions
   - Provides feedback mechanism for effectiveness

## 🧩 Mentor Selection System

1. **Mentor Registry**
   - Defines mentor characteristics, specializations, and triggers
   - Maps prompts to emotional states
   - Configures voice settings per mentor
   - Defines selection criteria

2. **Selection Algorithm**
   - Takes current Hawkins level as input
   - Considers emotional trajectory
   - Weighs mentor specializations
   - Returns optimal mentor ID and configuration

3. **Prompt Generation**
   - Dynamically generates system prompts based on:
     - Selected mentor
     - Current emotional state
     - Conversation history
     - Ethical guidelines

## ⚖️ Ethical Advisor System

1. **Constitutional Rules**
   - Implements Council AI Constitution
   - Defines rules against manipulation, victimhood, etc.
   - Provides stoic philosophical guidance
   - Ensures response alignment

2. **Filter Pipeline**
   - Pre-processes all mentor responses
   - Identifies rule violations
   - Suggests alternative phrasing
   - Logs intervention rationale

3. **Integration Points**
   - Sits between GPT response and client delivery
   - Provides real-time validation
   - Offers metrics on ethical quality
   - Improves with feedback

## 🗄️ Data Architecture

1. **Supabase Schema**
   - Users: Authentication and profiles
   - Sessions: Conversation instances
   - Messages: Individual exchanges
   - EmotionalStates: Hawkins levels and trajectory
   - Journals: User reflections and insights
   - Quotes: Notable mentor statements

2. **Vector Storage**
   - Embeddings of conversation segments
   - Semantic search capabilities
   - Similarity matching for related insights
   - Retrieval for context enhancement

## 🧠 Conversation Engine (Mentor Calls)

The core conversation flow is orchestrated through:

1. **Audio Capture & Processing**
   - Microphone access and recording
   - VAD with Silero enhancement
   - Audio level visualization
   - Speech end detection

2. **Transcription & Emotion Analysis**
   - Whisper-based transcription
   - Text-based emotion detection
   - Hawkins mapping and tracking
   - Emotional trajectory visualization

3. **Mentor Selection & Response**
   - Dynamic mentor selection based on emotion
   - System prompt generation with context
   - GPT response generation
   - Ethical filtering and validation

4. **Response Delivery & Feedback**
   - TTS conversion with voice matching
   - Audio playback with visualization
   - Emotional impact assessment
   - Feedback collection for RLHF

## 📈 Development Roadmap

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