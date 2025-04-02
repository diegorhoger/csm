# 🧠 Summary of Functionalities for Your Stoic Mentor System (with CSM)

## 1. Conversational Voice Interface

- Always-on voice listening with wake phrase or open-mic toggle.
- Real-time speech-to-text (Whisper): Transcribes user's voice.
- Context-aware streaming response from GPT-4 (or Claude/Solar): Emulates Marcus Aurelius, Seneca, or Epictetus.
- Streaming TTS response using ElevenLabs or Bark with natural, expressive voice synthesis.
- Interrupt detection: User can speak over the AI to cut it off (mimics natural turn-taking).

## 2. Mentor Personality System

Each mentor has:

- Unique system prompt/personality style
- Custom voice profile (TTS voice ID)
- Mentor-specific tone control (calm, motivational, challenging)
- Future: dynamic emotion/mood adjustment (e.g., gentler if user is sad)

## 3. Minimalist Interface Like Sesame Demo

No chat bubbles, no keyboard unless requested.

Simple UI showing:

- Mic level or waveform
- Current speaker (User / Mentor)
- Option to switch mentors (Marcus / Seneca / Epictetus)
- Controls: Start / Stop conversation, optionally Pause.

## 4. Real-Time Feedback Loop

- Streaming Whisper input
- Streaming GPT response with async generator
- Streaming TTS output with interrupt support
- 200ms latency goal: parallelizing transcription → generation → speech

## 5. Session Memory

- Light memory in context window (e.g., last 3 exchanges)
- Local conversation log (per mentor)
- Option to mark reflections for journaling or later review

## 6. Stoic Practice Layer
(Optional for V2 — but architect early)

After or during conversations, mentors might suggest:

- Reflection prompts
- Breathing techniques
- Quotes to remember
- Auto-tag journal entries based on themes/emotions

## 7. Local Dev & Backend Plan

For now: all runs locally on your machine

Components:

- `useMicStream` (or vad): listens to audio
- `startWhisperStream`: transcribes
- `startGPTStream`: responds
- `streamTTS`: speaks

Future backend:

- Firebase or Supabase for saving sessions
- DB model: user > mentor > session > message[]

## 8. Expandable Architecture

CSM lets you easily:

- Swap STT, LLM, or TTS provider
- Plug in emotion detection
- Add eye/contact detection (for mobile/AR later)
- Run on-device (edge) with fast models

---

## 🧱 Project Directory Structure

```
/src
├── components/
│   ├── UI/
│   │   └── WaveformVisualizer.tsx
│   ├── core/
│   │   ├── MentorCallUI.tsx
│   │   └── MentorSwitcher.tsx
│   └── layout/
│       └── AppLayout.tsx
│
├── hooks/
│   ├── useMentorCallEngine.ts        # Core logic: whisper + GPT + TTS
│   ├── useMicStream.ts               # Gets microphone input
│   ├── useVoiceActivityDetection.ts  # Detects user speaking (for interruption)
│   ├── useWakeWord.ts                # (Optional) Trigger phrase "Hey Marcus"
│   └── useSessionRecorder.ts         # Record/log conversations
│
├── services/
│   ├── whisper.ts                    # Transcription service wrapper
│   ├── openai.ts                     # GPT streaming wrapper
│   ├── tts.ts                        # Text-to-speech streaming
│   ├── mentors.ts                    # Mentor personalities (prompts + voices)
│   └── emotion.ts                    # (Optional) Sentiment/emotion detection
│
├── state/
│   └── sessionStore.ts               # Store for conversation state (Zustand, Jotai, etc.)
│
├── pages/
│   └── index.tsx                     # Home / main conversation screen
│
├── utils/
│   ├── throttle.ts
│   ├── debounce.ts
│   └── audioUtils.ts
│
├── constants/
│   └── app.ts                        # App-wide constants (latency target, etc.)
│
├── types/
│   └── index.ts                      # Shared types/interfaces
│
└── csm/                              # Sesame CSM integration
    ├── graph.ts                      # Conversation state machine logic
    └── hooks.ts                      # CSM-powered React helpers
```

## 💡 Key Concepts

### useMentorCallEngine.ts

Central orchestrator:

- Handles mic input → Whisper
- Feeds into GPT stream (based on selected mentor's prompt)
- Sends TTS chunks
- Switches between speaking/listening states
- Integrates CSM transitions

### services/mentors.ts

Encodes Stoic mentor personalities:

```typescript
export const mentors = {
  marcus: {
    name: 'Marcus Aurelius',
    prompt: 'You are Marcus Aurelius. Speak calmly and with quiet strength...',
    voiceId: 'marcus-v1',
    style: 'calm'
  },
  seneca: {
    name: 'Seneca',
    prompt: 'You are Seneca. Speak with eloquence and motivation...',
    voiceId: 'seneca-v1',
    style: 'motivational'
  },
  epictetus: {
    name: 'Epictetus',
    prompt: 'You are Epictetus. Speak bluntly and challenge assumptions...',
    voiceId: 'epictetus-v1',
    style: 'firm'
  }
};
```

### components/core/MentorCallUI.tsx

Main interactive conversation interface:

- Big mic button (start/stop)
- Visual feedback (waveform, transcription)
- Optional log pane (transcript + mentor response)

### state/sessionStore.ts

Session memory state:

```typescript
interface Message {
  role: 'user' | 'mentor';
  content: string;
  timestamp: number;
}

interface SessionState {
  currentMentor: MentorKey;
  history: Message[];
  isSpeaking: boolean;
  isListening: boolean;
}
```

## ✅ Optional Modules (Future)

- `/tasks/stoicPractices.ts` – Assign suggested Stoic reflections
- `/api/feedback.ts` – Send logs or feedback to backend
- `/mobile/` – Build React Native interface using same logic