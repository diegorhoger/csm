# Stoic Mentor → Council Implementation Plan

## Project Overview
Council is an emotionally intelligent, voice-first AI mentor designed to guide users through an inner journey of growth using real-time emotion recognition, stoic philosophy, and advanced conversational intelligence. The application enables natural, human-like conversations with different mentors who adapt to the user's emotional state.

## Core Components (Completed)
- ✅ React/TypeScript project setup with Vite
- ✅ Component architecture and state management
- ✅ Basic UI/UX implementation
- ✅ Audio recording and playback system
- ✅ WebSocket-based Voice Activity Detection (VAD)
- ✅ OpenAI integration for transcription and responses
- ✅ Initial text-to-speech implementation

## Priority 0: Backend Architectural Refactoring (COMPLETED)
- ✅ Move OpenAI integration from frontend to backend
- ✅ Create dedicated mentor conversation API endpoints
- ✅ Implement conversation session management on server
- ✅ Secure API keys and implement usage monitoring
- ✅ Set up streaming response mechanism for real-time feedback

## Priority 1: WebSocket VAD Integration (COMPLETED)
- ✅ Fix WebSocket connection issues with proper CORS configuration
- ✅ Implement proper error handling for WebSocket connections
- ✅ Create diagnostic and testing tools for WebSocket VAD
- ✅ Add connection health checks and automatic recovery
- ✅ Optimize audio data transfer between client and server

## Priority 2: Audio Processing & Silero VAD Enhancement (COMPLETED)
- ✅ Fix audio blob handling and processing in frontend
- ✅ Implement retry mechanism for transcription failures
- ✅ Add proper MIME type handling for audio files
- ✅ Integrate Silero VAD as enhancement to current audio analysis service
- ✅ Maintain existing WebSocket infrastructure and session management
- ✅ Implement performance monitoring to compare Silero vs RMS approaches
- 🔲 Add spectral analysis for better noise/speech differentiation
- 🔲 Implement frequency band filtering for human voice isolation

## Priority 3: Emotion Intelligence & Hawkins Tracking
- 🔲 Implement text-based emotion analysis using pre-trained model (DistilBERT)
- 🔲 Create Hawkins Energy Scale mapping (5-7 levels: Shame → Anger → Neutral → Acceptance → Peace)
- 🔲 Develop emotion trajectory tracking over conversation sessions
- 🔲 Add emotion visualization component in UI
- 🔲 Implement backend storage for emotion state tracking
- 🔲 Create API endpoints for emotion state retrieval and updates

## Priority 4: Mentor Selection System
- 🔲 Expand mentor profiles with deeper philosophical nuance
- 🔲 Implement emotion-based mentor selection logic
- 🔲 Create system prompts optimized for different emotional states
- 🔲 Build mentor switching mechanism based on Hawkins level
- 🔲 Design architecture for future expansion to 100+ mentors
- 🔲 Implement voice profile mapping for each mentor

## Priority 5: Ethical Advisor & Safeguards
- 🔲 Implement rule-based ethical filter using Council AI Constitution
- 🔲 Create validation middleware for all mentor responses
- 🔲 Add violation detection and response refinement
- 🔲 Build logging system for ethical interventions
- 🔲 Implement response sanitization for alignment with Stoic principles

## Priority 6: Memory & Session Persistence
- 🔲 Implement Supabase integration for authentication and storage
- 🔲 Create conversation history persistence
- 🔲 Implement simple journaling functionality
- 🔲 Add session summarization capabilities
- 🔲 Build quote and insight tracking system

## Priority 7: Feedback System (RLHF Foundation)
- 🔲 Implement user feedback collection mechanism
- 🔲 Create emotion delta tracking (before/after conversation)
- 🔲 Develop simple scoring system for mentor effectiveness
- 🔲 Build data collection framework for future RLHF
- 🔲 Implement basic analytics dashboard

## Technical Implementation Details

### Silero VAD Integration
1. **Implementation Status (COMPLETED)**
   - Integrated Silero VAD model via PyTorch Hub with custom audio buffer handling
   - Implemented as complementary system alongside WebRTC and RMS-based VAD approaches
   - Created weighted ensemble approach with configurable thresholds for each detection method
   - Added performance metrics and debugging tools for accuracy comparison
   - Successfully tested with various audio sample rates and chunk sizes

2. **Performance Optimizations (COMPLETED)**
   - Implemented singleton pattern for model loading to minimize memory usage
   - Added buffering system to handle small audio chunks (as small as 10ms)
   - Optimized processing for streaming audio with variable chunk sizes
   - Added overlap in processed chunks to improve detection reliability
   - Created statistics tracking to monitor inference time and detection rates
   - Ensured compatibility with WebSocket streaming architecture

3. **Next Enhancement Areas**
   - Consider implementing spectral analysis for better noise filtering
   - Add frequency band filtering to focus on human voice frequencies
   - Evaluate using TensorRT/ONNX for faster inference
   - Explore fine-tuning options for specific use cases

### Emotion Intelligence System
1. **Text-Based Emotion Analysis**
   - Implement using pre-trained DistilBERT model
   - Extract sentiment and emotion classifications from transcribed text
   - Map detected emotions to Hawkins Energy Scale
   - Store emotion state in session data

2. **Hawkins Scale Implementation**
   - Create 5-7 tiered system from negative to positive states
   - Implement tracking mechanism for emotional trajectory
   - Develop visualization component for emotional state
   - Enable filtering and retrieval of past emotional states

### Mentor Selection System
1. **Core Implementation**
   - Define emotional triggers for each mentor
   - Create mapping between emotional states and mentor selection
   - Implement prompts optimized for different emotional contexts
   - Build dynamic system prompt generation based on emotion

2. **Scalable Architecture**
   - Design for eventual expansion to 100+ mentors
   - Implement mentor registry and configuration system
   - Create modular prompt structure with emotional adaptivity
   - Develop testing framework for mentor effectiveness

### Ethical Advisor Implementation
1. **Rule-Based Filter**
   - Implement Council AI Constitution as validation system
   - Create pre-processing middleware for all responses
   - Develop violation detection and reporting
   - Implement refinement requests for non-compliant responses

2. **Integration Points**
   - Add as pre-response filter in API backend
   - Implement logging system for validation results
   - Create feedback loop for improvement
   - Build UI indicators for ethical alignments

## Testing Strategy
1. **VAD Testing**
   - Compare Silero vs current RMS system accuracy
   - Benchmark in different noise environments
   - Test with various accents and speech patterns
   - Measure false positive/negative rates

2. **Emotion Detection Testing**
   - Create test suite with diverse emotional inputs
   - Validate Hawkins mapping accuracy
   - Test emotion trajectory tracking
   - Assess mentor selection appropriateness

3. **Ethical Filter Testing**
   - Create tests for each constitutional rule
   - Validate violation detection
   - Test refinement quality
   - Measure impact on response latency

## Updated Timeline

### Phase 1: Core MVP (Weeks 1-4)
1. **Text-based Emotion Engine** (3-5 days)
   - 🔲 Implement text-based sentiment/emotion classifier
   - 🔲 Create Hawkins mapping (5-7 levels)

2. **Mentor Selector** (3-5 days)
   - 🔲 Map 3 personas to emotional states
   - 🔲 Implement selection logic

3. **Voice Pipeline Enhancement** (7-10 days)
   - ✅ Integrate Silero VAD
   - ✅ Enhance audio processing
   - 🔲 Connect emotion analysis

4. **Basic State Tracking** (5-7 days)
   - 🔲 Set up Supabase integration
   - 🔲 Implement session persistence
   - 🔲 Add basic quote logging

5. **Ethical Filter** (4-6 days)
   - 🔲 Implement Council AI Constitution
   - 🔲 Add response validation

### Phase 2: Growth Layer (Weeks 5-8)
1. **Journaling Timeline** (5-7 days)
   - 🔲 Create emotion replay visualization
   - 🔲 Implement journal entry system

2. **Memory Enhancement** (5-7 days)
   - 🔲 Add vector storage
   - 🔲 Implement session summarization

3. **Feedback System** (7-10 days)
   - 🔲 Build emotion delta tracking
   - 🔲 Implement feedback collection

4. **Mobile Optimization** (7-10 days)
   - 🔲 Create responsive design
   - 🔲 Optimize for offline mode

## Progress Tracking
We'll continue to use GitHub issues and project boards to track implementation progress, with weekly reviews to adjust priorities based on development velocity and user feedback.

## Recent Key Technical Achievements

### Silero VAD Integration (August 2024)
We successfully integrated the Silero Voice Activity Detection system into our existing audio processing pipeline. This enhancement brings several important improvements:

1. **Multi-Method VAD Ensemble:**
   - Combined three complementary approaches (RMS-based, WebRTC, and Silero) into a weighted ensemble
   - Each method provides different strengths: RMS for simplicity, WebRTC for speed, Silero for accuracy
   - Configurable weights allow tuning for different environments and use cases

2. **Audio Buffering Solution:**
   - Implemented a robust buffering system to handle variable chunk sizes from WebSocket streams
   - Solved the key challenge of processing small audio chunks (10ms) when the model requires larger segments (512 samples)
   - Added intelligent overlap between processing windows to avoid missing speech at chunk boundaries

3. **Performance Monitoring:**
   - Created a monitoring dashboard for VAD performance metrics
   - Added detailed statistics on each detection method
   - Implemented tools for comparing detection accuracy and latency

4. **Integration with Frontend:**
   - Extended the existing WebSocket infrastructure to include Silero detection results
   - Added visualization of detection confidence in the UI
   - Maintained backward compatibility with existing systems

This integration significantly improves our speech detection accuracy while maintaining low latency, which is crucial for the conversational experience. The ensemble approach gives us resilience against different audio conditions and speaking patterns.

**Last Updated: 2024-08-15**
