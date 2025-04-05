# Council Frontend

An emotionally intelligent, voice-first AI mentor designed to guide users through an inner journey of growth using real-time emotion recognition, stoic philosophy, and advanced conversational intelligence.

## Description

Council is a web application that enables users to engage in voice conversations with AI mentors representing stoic philosophers. The application transcribes user speech, analyzes emotional content using the Hawkins Energy Scale, selects the appropriate mentor, and provides philosophical guidance that adapts to the user's emotional state.

## Features

- **Emotion Intelligence**: Text-based emotion analysis with Hawkins Energy Scale mapping
- **Dynamic Mentor Selection**: Chooses the appropriate mentor based on emotional state
- **Three Stoic Mentors**: Marcus Aurelius, Seneca, and Epictetus, each specializing in different emotional states
- **Natural Conversation**: Voice-first interface with spoken responses
- **Speech-to-Text**: Audio transcription through OpenAI Whisper
- **Advanced Voice Activity Detection**: Silero VAD for accurate speech detection
- **Ethical Filtering**: Ensures responses align with the Council AI Constitution
- **Responsive Design**: Works on desktop and mobile devices
- **Persistent Storage**: Conversation history and emotional journey tracking with Supabase

## Technology Stack

- **Frontend**: React 19.0.0, Vite 6.2.0, TailwindCSS 4.1.1
- **State Management**: Zustand 5.0.3, TanStack Query 5.71.3
- **Backend**: Flask 2.3.3, Flask-SocketIO 5.3.6
- **Audio Processing**: WebAudio API and MediaRecorder
- **Speech Recognition**: OpenAI Whisper API
- **Database**: Supabase (PostgreSQL)
- **ML Models**: Silero VAD, DistilBERT (emotion analysis)

## Getting Started

### Prerequisites

- Node.js (v18+)
- Backend server running (see [Backend README](../backend/README.md))
- Docker and Docker Compose (for running with containers)

### Installation

1. Install frontend dependencies:
   ```
   npm install
   ```

2. Create a `.env` file with necessary configuration:
   ```
   # API endpoints
   VITE_API_URL=http://localhost:5002
   VITE_WEBSOCKET_VAD_URL=http://localhost:5003
   
   # Feature flags
   VITE_USE_SOCKET_VAD=true
   
   # Supabase configuration
   VITE_SUPABASE_URL=http://localhost:54321
   VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
   
   # OpenAI (for production)
   VITE_OPENAI_API_KEY=your-openai-key
   ```

### Running the Application

#### Development Mode

1. Ensure the backend services are running:
   ```
   cd ../backend
   python api.py --port 5002
   ```

2. Start the frontend development server:
   ```
   npm run dev
   ```

3. Open your browser and navigate to `http://localhost:5173`

#### Docker Mode

For a complete containerized setup:

1. Start all services with Docker Compose:
   ```
   docker-compose up
   ```

2. Open your browser and navigate to `http://localhost:5173`

See [DOCKER_README.md](DOCKER_README.md) for more details on the Docker setup.

## Usage

1. Start the application and either:
   - Select a mentor manually, or
   - Let the system choose based on your emotional state
2. Click the microphone button to start a conversation
3. Speak your question or concern
4. The system will detect when you stop speaking
5. Your speech will be transcribed and analyzed for emotional content
6. The appropriate mentor will respond with guidance tailored to your emotional state
7. Your emotional journey is tracked and visualized on the Hawkins Energy Scale
8. The conversation history is saved for future reference

## Troubleshooting

### Common Issues

- **Audio Issues**: Ensure browser microphone permissions are granted
- **WebSocket Issues**: Check that all backend services are running correctly
- **Emotion Analysis Errors**: Verify the emotion service is running (`docker-compose logs emotion-analysis`)
- **Database Connection Issues**: Check Supabase connection (`docker-compose logs supabase-local`)

For detailed debugging information, visit the diagnostic page at http://localhost:5002/debug

## Development Notes

- Emotion analysis is performed on the backend using a pre-trained DistilBERT model
- The Hawkins Energy Scale maps emotions to a 5-7 tiered scale (Shame → Fear → Anger → Neutral → Acceptance → Reason → Peace)
- Each mentor specializes in different emotional states according to the mentorMap configuration
- The Council AI Constitution ensures responses are ethical and constructive

## License

[MIT License](LICENSE)

## Documentation

See the [docs](../docs) directory for detailed documentation:

- [ARCHITECTURE.md](../docs/ARCHITECTURE.md) - System architecture
- [PLAN.md](../docs/PLAN.md) - Implementation plan
- [PRD.md](../docs/PRD.md) - Product requirements
- [Council AI Constitution V1.md](../docs/Council%20AI%20Constitution%20V1.md) - Ethical principles
