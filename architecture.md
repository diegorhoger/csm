# System Architecture: Stoic Voice Mentor App

## 📦 Code Organization

```
Project Root/
├── backend/
│   ├── api.py                # Main Flask/SocketIO API
│   ├── audio_analysis_service.py  # Audio analysis for VAD 
│   ├── socket_vad_service.py      # WebSocket VAD service
│   ├── static/               # Static assets and test files
│   ├── requirements.txt      # Backend dependencies
│   └── README.md             # Backend documentation
│
└── stoic-mentor/            # Frontend application
    ├── src/
    │   ├── components/       # UI components (reusable, composable)
    │   ├── hooks/            # Custom React hooks
    │   ├── services/         # API wrappers, models, TTS, Whisper, etc.
    │   ├── state/            # Global state stores
    │   ├── pages/            # Entry points per route
    │   ├── csm/              # Conversation State Machine logic (Sesame)
    │   ├── types/            # Shared types & interfaces
    │   ├── constants/        # App-wide configuration
    │   └── utils/            # Small reusable helpers
    ├── public/               # Static assets
    └── ...                   # Other frontend files
```

## 🎯 Architecture Overview

The system follows a clear client-server architecture:

1. **Backend** (Flask/SocketIO)
   - Handles all OpenAI API interactions (GPT, Whisper)
   - Provides WebSocket-based Voice Activity Detection
   - Serves API endpoints for mentor chat, transcription, etc.
   - Manages conversation sessions and state

2. **Frontend** (React/TypeScript)
   - Manages user interface and interactions
   - Handles audio recording and processing
   - Communicates with backend via REST APIs and WebSockets
   - Manages local state and conversation flow

## 🔄 Communication Flow

1. **Voice Input Flow**
   - User speaks → Browser records audio
   - Audio chunks sent to WebSocket VAD service
   - VAD detects speech start/end
   - Complete audio recording sent to backend transcription endpoint
   - Transcribed text displayed to user

2. **AI Response Flow**
   - Transcribed text sent to mentor chat endpoint
   - Backend calls OpenAI API with appropriate mentor context
   - Response streamed back to frontend
   - Frontend displays and plays back response

3. **WebSocket Communication**
   - Real-time voice activity detection
   - Connection status monitoring
   - Session management
   - Diagnostics and debugging

## 🧠 Core Hooks and Services

### Backend Services
- **API Layer** (`api.py`): Main Flask application with REST endpoints
- **Socket VAD Service** (`socket_vad_service.py`): WebSocket-based Voice Activity Detection
- **Audio Analysis** (`audio_analysis_service.py`): Audio processing and analysis

### Frontend Hooks
- **useMentorCallEngine**: Orchestrates the entire conversation flow
- **useMicStream**: Manages microphone access and audio recording
- **useSocketVad**: Connects to WebSocket VAD service for speech detection
- **useVoiceActivityDetection**: Coordinates voice activity state

### Frontend Services
- **mentorService.ts**: Handles backend API communication for mentor interactions
- **socketVadService.ts**: Manages WebSocket connection and events
- **openaiService.ts**: Utilities for OpenAI API integration (mostly deprecated in favor of backend)
- **ttsService.ts**: Manages text-to-speech playback

## 🔐 Security Considerations

1. **API Key Management**
   - All API keys stored securely on backend
   - No keys exposed to frontend
   - Usage monitoring and rate limiting

2. **Data Privacy**
   - Minimal audio storage (temporary files only)
   - No persistent storage of conversations without consent
   - Clear permissions model for microphone access

3. **Network Security**
   - CORS restrictions properly configured
   - WebSocket secure connection options
   - Input validation on all API endpoints

## 🔍 Diagnostic Tools

1. **WebSocket Test Page**
   - Available at `/test` endpoint
   - Tests WebSocket connections
   - Tests API endpoints
   - Tests audio recording and transcription

2. **Logging System**
   - Comprehensive logging in both frontend and backend
   - WebSocket connection diagnostics
   - Audio processing metrics
   - API call tracing

## 🚀 Performance Considerations

1. **WebSocket Optimization**
   - Efficient binary data transfer
   - Proper error handling and reconnection
   - Configurable VAD sensitivity

2. **Audio Processing**
   - Efficient audio blob handling
   - Format conversion as needed
   - Retry mechanisms for transcription

3. **Response Streaming**
   - Real-time streaming of API responses
   - Progressive rendering of mentor replies
   - Low-latency playback

## 📈 Scalability Design

The system is designed to scale through:

1. **Stateless API Design**
   - Each request contains necessary context
   - Sessions managed via identifiers
   - Minimal server-side state

2. **Efficient Resource Usage**
   - Audio processing optimized for size and quality
   - WebSocket connections properly closed when inactive
   - Temporary files cleaned up promptly

3. **Modular Architecture**
   - Clear separation between components
   - Well-defined interfaces
   - Isolated responsibilities

## 🧪 Testing Approach

1. **Unit Testing**
   - Individual services and hooks tested in isolation
   - Mock implementations for external dependencies

2. **Integration Testing**
   - API endpoint tests
   - WebSocket communication tests
   - Full conversation flow tests

3. **Manual Testing**
   - Test page for direct API interaction
   - Real-world testing with actual speech input
   - Cross-browser compatibility testing

## 🎯 Design Principles

- **KISS**: Keep interfaces, functions, and abstractions minimal. Avoid overengineering early.
- **SRP**: One component/hook/service = one responsibility.
- **Reusability First**: Design everything with reuse in mind.
- **Composition over Inheritance**: Especially in React patterns.
- **Fail Gracefully**: All async flows (mic, TTS, GPT) should have timeouts, fallbacks, and logs.

## 📘 Naming & Style

- Use **camelCase** for variables, functions, and constants.
- Use **PascalCase** for components and classes.
- Keep files under 150 lines whenever possible.
- Use function components and React Hooks only (no class components).
- Place all interface, type, enum in `/types`.

## 🧠 Conversation Engine (Mentor Calls)

- Use `useMentorCallEngine` hook as the orchestration center.
- Integrate Whisper → GPT → TTS with stream-to-stream handling.
- Ensure latency under 200ms for response-to-speech loop.
- Use `AbortController` for interruption detection and control.
- Use CSM (from Sesame) for managing conversation flow and mentor state transitions.

## 🧩 Micro-modules

Each feature is self-contained:

- **Hooks**: `useMicStream`, `useVoiceActivityDetection`, `useWakeWord`
- **Services**: `whisper.ts`, `openai.ts`, `tts.ts`
- **Personalities**: `mentors.ts` maps name → prompt + voice + style
- Core logic lives in `useMentorCallEngine.ts` and `graph.ts` (CSM)

## 🛠️ Tools & Frameworks

- React + TypeScript
- Vite or Next.js (depending on full app needs)
- Zustand (or Jotai) for lightweight global state
- Tailwind CSS (optional, for clean styling)
- ffmpeg.wasm for audio manipulation (if needed)
- Deepgram, OpenAI, ElevenLabs for whisper, GPT, and TTS

## 🧪 Testing

- Use Vitest or Jest for unit testing.
- Mock services (tts, gpt, whisper) with stubs/mocks in tests.
- Use Storybook for visual testing of components.

## 📈 Scalability

- Build everything as loosely coupled modules
- Follow feature-first design (folders per feature if needed)
- Support local-first dev (recorded audio/transcripts/logs)
- Plan for multi-mentor extensibility and multi-user sessions
- Define all personality traits in `services/mentors.ts` for easy override
- Prepare for edge-streaming via CSM or Cloudflare Workers (future)

## 🔐 Security & Privacy

- Handle mic permissions cleanly
- Log and store audio transcripts only with consent
- Ensure Whisper + GPT API tokens are secured (in .env or serverless)
- CORS-safe backend interaction

## ✅ Development Rituals

- Every PR includes tests, typing, and isolated functionality.
- Never hardcode mentor prompts or voice settings outside `mentors.ts`.
- Keep AI stream, TTS, transcription functions pure and composable.
- Validate latency regularly — aim <200ms from user stop to response start.
- Document decisions in `/docs/architecture.md` if changes are non-trivial.

## 🧠 Cursor Prompting Guidelines

For Cursor AI, you can prompt:

```
"Generate a React hook that integrates Whisper mic stream, passes result to GPT with mentor personality prompt, and streams response to ElevenLabs TTS in real time. Use abort controller to cancel if user interrupts."
```

Or for a modular helper:

```
"Create a service that handles GPT streaming with a given system prompt and a user message. Return an async generator of tokens."
```

## Consolidated Architecture

The project has been updated to a consolidated architecture:

```
CSM/
├── backend/               # Consolidated backend API
│   ├── api.py             # Main Flask/SocketIO API
│   ├── audio_analysis_service.py  # Audio analysis for VAD 
│   ├── socket_vad_service.py      # WebSocket VAD service
│   ├── requirements.txt   # Backend dependencies
│   └── README.md          # Backend documentation
│
└── stoic-mentor/          # Frontend application
    ├── src/               # React/Vue.js source code
    ├── public/            # Static assets
    └── ...                # Other frontend files
```

The backend has been consolidated to include all functionality in a single API:

1. **Voice Activity Detection (VAD)**: Detects when a user is speaking via audio analysis
2. **WebSocket Communication**: Real-time bidirectional communication
3. **OpenAI Integration**: Text generation, text-to-speech, and transcription capabilities

The frontend connects to the backend via HTTP APIs and WebSockets to provide a seamless user experience.