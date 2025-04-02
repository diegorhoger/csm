# VITA AI – Implementation Roadmap 🧠✨

**Project Scope:** Stoic Mentor Voice Companion  
**Platforms:** Web (React), Mobile (React Native / Expo)  
**Goal:** Seamless, human-like real-time AI mentorship

## 🔹 PHASE 1: FOUNDATION

- ✅ Setup monorepo with Turborepo or Nx
- ✅ Setup CI/CD for web (Vercel) and mobile (Expo)
- ✅ Configure TypeScript, ESLint, Prettier
- ✅ Setup folder structure: /components, /hooks, /services, /utils
- ✅ Setup GitHub project board + issues
- ✅ Setup environment variables & API keys management
- ✅ Create mock services for local development

## 🔹 PHASE 2: UI/UX & COMPONENTS

- ✅ VoiceButton.tsx – tap to speak / stop
- ✅ MentorSelector.tsx – choose Marcus, Seneca, Epictetus
- ✅ TranscriptBox.tsx – live display of user text
- 🔲 AnimatedAvatar.tsx – optional visual feedback
- ✅ Minimalist UX based on Sesame.ai design
- 🔲 Add dark/light theme support
- ✅ Implement error boundary components
- 🔲 Add accessibility features (ARIA, keyboard navigation)
- 🔲 Create user onboarding/tutorial components

## 🔹 PHASE 3: AUDIO / STREAMING

- ✅ useMicStream.ts – mic input as stream
- ✅ services/whisperService.ts – OpenAI Whisper integration
- ✅ services/openaiService.ts – GPT stream with systemPrompt
- ✅ services/ttsService.ts – ElevenLabs voice stream
- ✅ hooks/useMentorCallEngine.ts – glue logic
- ✅ Add fallback for no-mic/browser support
- 🔲 Implement audio buffering strategy for low latency
- 🔲 Add offline fallback mechanisms
- ✅ Create browser compatibility detection

## 🔹 PHASE 4: MENTOR SYSTEM

- ✅ mentors.ts – Marcus, Seneca, Epictetus profile
- ✅ systemPrompt tuned per voice/style
- 🔲 Add Claude / Gemini model option
- 🔲 Add profile: Aurelia (female stoic voice)

## 🔹 PHASE 5: STATE & STORAGE

- ✅ store/mentors.ts – selected mentor state
- 🔲 store/history.ts – log of previous calls
- 🔲 LocalStorage or SQLite persistence layer
- 🔲 Supabase / Firebase integration (sync)
- 🔲 Implement conversation history display component

## 🔹 PHASE 6: MOBILE ADAPTATION

- 🔲 Configure mic permissions (iOS + Android)
- 🔲 Expo background audio / stop listener
- 🔲 React Native waveform visual
- 🔲 Mobile navigation + session list view

## 🔹 PHASE 7: PERFORMANCE

- 🔲 Sub-200ms TTS latency buffer (chunked)
- 🔲 Preload voices + warm GPT stream
- 🔲 Silence detector: `utils/vad.ts`
- 🔲 Cache audio / resume partial replies
- 🔲 Implement progressive loading strategies

## 🔹 PHASE 8: TESTING & QA

- 🔲 unit tests: `useMentorCallEngine.test.ts`
- 🔲 e2e tests: `playwright.config.ts` (web), Detox (mobile)
- ✅ stress test GPT + TTS pipelines
- 🔲 test iOS Safari / Android Chrome mic behavior
- 🔲 Cross-browser compatibility testing
- 🔲 Performance benchmarking tools

## 🔹 PHASE 9: DEPLOYMENT

- 🔲 Deploy web to Vercel
- 🔲 Expo build to TestFlight / Google Beta
- 🔲 Add monitoring: LogRocket, Sentry, Supabase Logs
- 🔲 Enable Stripe if monetization planned
- 🔲 Setup content delivery network (CDN) for audio assets

## 🔹 PHASE 10: POST-LAUNCH & ADD-ONS

- 🔲 Add journaling/log to GPT output
- 🔲 Daily Stoic challenges
- 🔲 Emotion tracking + sentiment
- 🔲 "Interrupt-to-ask" inside TTS playback
- 🔲 Community & content system (MML Ethos Room)
- 🔲 Implement usage analytics dashboard

## 🔹 Bonus Tools

- ✅ /utils/debug.ts – verbose error tracking
- ✅ /constants/audioThresholds.ts
- ✅ /types/mentor.ts
- ✅ /components/ErrorBoundary.tsx – graceful error handling
- ✅ /utils/browserDetection.ts – feature detection utilities

---

**LAST UPDATED:** 2023-04-02

## 🔹 CURRENT PROGRESS SUMMARY

We have successfully implemented:

1. Core infrastructure with React and TypeScript
   - Vite build system with proper configuration
   - TypeScript with strong typing throughout the codebase
   - Tailwind CSS for styling with proper configuration
   - Environment variable management

2. Basic UI components:
   - TranscriptBox component for displaying conversation
   - MentorSwitcher for selecting between stoic mentors
   - WaveformVisualizer for audio feedback
   - VoiceButton for intuitive recording interaction
   - ConversationUI that combines these components
   - AppLayout for consistent UI structure

3. Audio handling:
   - useMicStream hook for microphone input and recording
   - Microphone permissions management
   - Audio level visualization
   - Streaming audio processing

4. Backend integration:
   - Flask API with endpoints for:
     - /api/health (health check)
     - /api/mentors (mentor profiles)
     - /api/tts (text-to-speech using mock generator)
     - /api/transcribe (transcription)
     - /api/gpt (mentor responses)
   - Mock implementation for development without model dependencies
   - OpenAI integration for authentic stoic responses

5. State management with Zustand for conversational state

6. Service layer with:
   - whisperService for transcription
   - ttsService for speech generation
   - mentorService for mentor data
   - openaiService for GPT integration
   - api.ts for backend communication

7. Complete conversation flow with useMentorCallEngine:
   - Integration of mic input, transcription, LLM response, and TTS
   - Support for interruptions and conversation history
   - Error handling and state management

8. Documentation:
   - Comprehensive DOCUMENTATION.md with technical decisions
   - Architecture guidelines in ARCHITECTURE.md
   - README.md with setup instructions
   - Inline code comments

## 🔹 IMPLEMENTATION CHANGES

1. **Backend Approach:**
   - Original plan assumed edge-first computation
   - Implemented a Flask backend with REST API instead
   - Allows for easier development and testing cycle

2. **Speech Model:**
   - Original plan used CSM (Conversational Speech Model)
   - Implemented mock TTS with fallback options instead
   - Created a simplified API that mimics the original functionality

3. **Storage Strategy:**
   - Original plan included Firebase/Supabase integration
   - Current implementation is entirely local-first
   - Simplified for initial version while maintaining expansion possibilities

4. **Mentor Personalities:**
   - Enhanced with detailed prompts and improved conversation context
   - Added dedicated mentor prompt system for authentic voices
   - Implemented improved sanitization of responses

5. **Project Structure:**
   - Consolidated into a single source directory in stoic-mentor/src
   - Added backend directory for API services
   - Improved organization following component-based architecture

## 🔹 NEXT STEPS (PRIORITY ORDER)

1. **Implement Voice Activity Detection (VAD):**
   - Create useVoiceActivityDetection hook
   - Add silence detection to automatically stop recording
   - Integrate with useMicStream and conversation flow

2. **Add Conversation History Persistence:**
   - Implement localStorage for session continuity
   - Create UI for viewing past conversations
   - Add export/import functionality

3. **Improve TTS Latency:**
   - Implement audio buffering strategies
   - Work toward 200ms latency goal
   - Add preloading for mentor voices

4. **Add Mobile Responsiveness:**
   - Ensure UI works well on mobile devices
   - Add touch-specific interactions
   - Test on various screen sizes

5. **Create AnimatedAvatar Component:**
   - Provide visual feedback for mentor speaking
   - Add subtle animations for different emotional states
   - Ensure it's lightweight and optimized for performance

6. **Implement Wake Word Detection:**
   - Create useWakeWord hook (optional activation)
   - Test with various wake phrases
   - Ensure low false positive rate

7. **Add Testing Infrastructure:**
   - Unit tests for core hooks and services
   - Integration tests for conversation flow
   - End-to-end testing for complete user journey

8. **Prepare for Deployment:**
   - Setup CI/CD for reliable deployments
   - Configure web deployment to Vercel
   - Set up proper environment variables for production

## 🔹 FUTURE ENHANCEMENTS

1. **Stoic Practice Layer:**
   - Implement reflection prompts and exercises
   - Add breathing technique guidance
   - Create quote recommendation system
   - Build journaling integration

2. **Enhanced Mentor Personalities:**
   - Add Aurelia (female stoic voice)
   - Consider additional philosophical mentors
   - Improve emotional resonance in responses

3. **Multi-language Support:**
   - Add support for languages beyond English
   - Translate mentor prompts and UI elements

4. **Offline Mode:**
   - Implement local fallbacks when API is unavailable
   - Cache common responses for better performance

5. **Accessibility Improvements:**
   - Add keyboard navigation throughout the app
   - Implement proper screen reader support
   - Provide alternative interaction methods

6. **User Preferences & Customization:**
   - Allow customization of response length and style
   - Save favorite mentors and conversations
   - Adjust audio and visual settings

7. **Analytics & Progress Tracking:**
   - Track stoic practice completion
   - Show user growth and engagement over time
   - Add optional gamification elements
