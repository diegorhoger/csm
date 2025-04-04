# Development Ruleset for Stoic Voice Mentor App

## 📦 Code Organization

Follow this directory structure:

```
src/
├── components/        // UI components (reusable, composable)
├── hooks/             // Custom React hooks
├── services/          // API wrappers, models, TTS, Whisper, etc.
├── state/             // Global state stores
├── pages/             // Entry points per route
├── csm/               // Conversation State Machine logic (Sesame)
├── types/             // Shared types & interfaces
├── constants/         // App-wide configuration
└── utils/             // Small reusable helpers
```

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