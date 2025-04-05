# 🧠 Council: Emotionally Intelligent Stoic Mentor System

## 1. Conversational Voice Interface

- Always-on voice listening with wake phrase or open-mic toggle
- Real-time speech-to-text (Whisper): Transcribes user's voice
- Context-aware streaming response from GPT-4 (or Claude/Solar): Emulates stoic mentors
- Streaming TTS response using ElevenLabs or similar with natural, expressive voice synthesis
- Interrupt detection: User can speak over the AI to cut it off (mimics natural turn-taking)
- Enhanced VAD using Silero integration for improved speech detection

## 2. Emotion Intelligence System

- Text-based emotion analysis using pre-trained models (DistilBERT)
- Hawkins Energy Scale tracking (5-7 tiered levels):
  - Shame → Anger → Neutral → Acceptance → Peace
- Emotion trajectory tracking over conversation
- Visualization of emotional state and progress
- Emotional state storage and retrieval
- Future: Audio-based emotion detection from paralinguistic features

## 3. Mentor Personality System

- Dynamic mentor selection based on user's emotional state
- Each mentor has:
  - Unique system prompt/personality style
  - Custom voice profile (TTS voice ID)
  - Mentor-specific tone control (calm, motivational, challenging)
  - Emotional triggers and specializations
  - Optimized prompts for different emotional contexts
- Architecture designed for future expansion to 100+ specialized mentors
- Emotion-adaptive response generation

## 4. Ethical Advisor & Safeguards

- Rule-based ethical filter implementing Council AI Constitution
- Validation system for all mentor responses
- Protection against manipulative or emotionally exploitative patterns
- Response refinement for non-compliant outputs
- Logging and monitoring of ethical interventions
- Alignment with stoic philosophical principles

## 5. Minimalist Interface

No chat bubbles, no keyboard unless requested.

Simple UI showing:
- Mic level or waveform
- Current speaker (User / Mentor)
- Emotion state visualization (Hawkins level)
- Option to switch mentors
- Controls: Start / Stop conversation, optionally Pause

## 6. Memory & Session Persistence

- Conversation history storage using Supabase
- Emotional trajectory recording
- Session summarization
- Quote and insight tracking
- Simple journaling functionality
- Future: Vector storage for semantic retrieval

## 7. Feedback System (RLHF Foundation)

- User feedback collection
- Emotional state delta tracking (before/after)
- Simple scoring for mentor effectiveness
- Data collection framework for future RLHF
- Basic analytics dashboard

## 8. Local Dev & Backend Architecture

Components:
- Backend API (Flask/SocketIO)
- WebSocket VAD with Silero enhancement
- Emotion analysis service
- Mentor selection engine
- Ethical filter middleware
- Supabase integration for persistence

Database models:
- user > sessions > messages
- user > emotional_states
- user > journal_entries
- mentors > prompts > voice_settings

## 9. Expandable Architecture

Council's architecture allows you to easily:
- Swap STT, LLM, or TTS provider
- Enhance emotion detection capabilities
- Add paralinguistic feature extraction
- Run components on-device (edge) with fast models
- Scale to 100+ mentor personalities
- Implement full RLHF in the future

---

## 🧱 Project Directory Structure

```
/src
├── components/
│   ├── UI/
│   │   ├── WaveformVisualizer.tsx
│   │   ├── EmotionVisualizer.tsx
│   │   └── VoiceCustomizationControls.tsx
│   ├── core/
│   │   ├── MentorCallUI.tsx
│   │   ├── MentorSwitcher.tsx
│   │   ├── EmotionTracker.tsx
│   │   └── JournalInterface.tsx
│   └── layout/
│       └── AppLayout.tsx
│
├── hooks/
│   ├── useMentorCallEngine.ts        # Core logic: whisper + GPT + TTS
│   ├── useMicStream.ts               # Gets microphone input
│   ├── useSocketVad.ts               # WebSocket VAD connection
│   ├── useVoiceActivityDetection.ts  # Local fallback VAD
│   ├── useEmotionAnalysis.ts         # Emotion detection and tracking
│   └── useSessionRecorder.ts         # Record/log conversations
│
├── services/
│   ├── mentorService.ts              # Backend API communication
│   ├── socketVadService.ts           # WebSocket connection management
│   ├── emotionService.ts             # Emotion analysis and tracking
│   ├── ethicsService.ts              # Ethical filter communication
│   ├── supabaseService.ts            # Database communication
│   └── ttsService.ts                 # Text-to-speech management
│
├── state/
│   ├── sessionStore.ts               # Conversation state
│   ├── emotionStore.ts               # Emotion tracking state
│   └── mentorStore.ts                # Mentor selection state
│
├── pages/
│   ├── index.tsx                     # Home / main conversation screen
│   ├── journal.tsx                   # Journal and insights
│   └── profile.tsx                   # User profile and settings
│
├── utils/
│   ├── emotionUtils.ts               # Emotion analysis helpers
│   ├── audioUtils.ts                 # Audio processing utilities
│   └── hawkinsScale.ts               # Hawkins mapping functions
│
├── constants/
│   ├── app.ts                        # App-wide constants
│   ├── emotions.ts                   # Emotion definitions
│   └── constitution.ts               # Ethical rules and constraints
│
├── types/
│   ├── index.ts                      # Shared types/interfaces
│   ├── emotion.ts                    # Emotion-related types
│   └── mentor.ts                     # Mentor configuration types
│
└── config/                           # Configuration files
    ├── mentors.ts                    # Mentor definitions and mappings
    └── hawkins.ts                    # Hawkins scale configuration
```

## 💡 Key Concepts

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

### Ethical Filter Implementation

```typescript
interface ValidationResult {
  isValid: boolean;
  violations: {
    rule: string;
    violatedPhrase: string;
  }[];
  suggestedRevision?: string;
}

async function validateResponse(response: string): Promise<ValidationResult> {
  // Check against all constitutional rules
  // Return validation result with any violations
}
```

### Emotion Tracking State

```typescript
interface EmotionState {
  currentLevel: HawkinsLevel;
  trajectory: {
    level: HawkinsLevel;
    timestamp: number;
    trigger?: string;
  }[];
  sessionStart: number;
  sessionEnd?: number;
}
```

## ✅ Future Modules

- `/services/audioEmotion.ts` – Paralinguistic emotion detection
- `/features/journaling/` – Advanced journaling system
- `/features/rlhf/` – Full reinforcement learning from human feedback
- `/mobile/` – React Native interface for mobile deployment