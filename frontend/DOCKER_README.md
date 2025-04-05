# Running Council with Docker

This guide explains how to run the Council emotionally intelligent AI mentor application using Docker for the backend services.

## Prerequisites

- [Docker](https://www.docker.com/get-started) installed on your system
- [Docker Compose](https://docs.docker.com/compose/install/) (usually included with Docker Desktop)

## Setup

1. **Clone the repository** (if you haven't already):
   ```bash
   git clone <repository_url>
   cd council
   ```

2. **Build and start the Docker containers**:
   ```bash
   cd frontend
   docker-compose up --build
   ```
   This will build the Docker images for all services and start them. The first build might take some time as it downloads models and installs dependencies.

3. **Run the frontend** (in a separate terminal):
   ```bash
   cd frontend
   npm install  # Only needed on first run
   npm run dev
   ```

4. **Access the application**:
   - The frontend will be available at `http://localhost:5173` (or the port shown in your terminal)
   - The backend API will be available at `http://localhost:5002`
   - The WebSocket VAD service will be available at `http://localhost:5003`

## Docker Compose Services

The application uses multiple containers:

1. **Backend API**: Core REST API service for mentor conversations and TTS
2. **Supabase Local**: Local development instance of Supabase for data storage
3. **WebSocket VAD**: Voice Activity Detection service with Silero VAD
4. **Emotion Analysis**: Text-based emotion detection service

## Configuration

Make sure your `.env` file has:
```
VITE_API_URL=http://localhost:5002
VITE_WEBSOCKET_VAD_URL=http://localhost:5003
VITE_USE_SOCKET_VAD=true
VITE_SUPABASE_URL=http://localhost:54321
VITE_SUPABASE_ANON_KEY=<your-supabase-anon-key>
```

Additional environment variables needed in the Docker Compose setup:
```
OPENAI_API_KEY=<your-openai-api-key>
SILERO_MODEL_PATH=/app/models/silero_vad.onnx
EMOTION_MODEL_PATH=/app/models/emotion_classifier
```

## Container Volumes

The Docker setup uses several volumes to persist data:

- `models-volume`: Stores downloaded ML models
- `supabase-data`: Stores Supabase database contents
- `emotion-models`: Stores emotion detection models

## Stopping the Application

1. Press `Ctrl+C` in the terminal running the Docker containers
2. To completely stop and remove containers:
   ```bash
   docker-compose down
   ```
3. To stop and remove containers plus volumes (will erase all data):
   ```bash
   docker-compose down -v
   ```

## Development with Docker

### Rebuilding Single Services

To rebuild and restart only a specific service:

```bash
docker-compose up -d --build backend
```

### Viewing Logs

To view logs for a specific service:

```bash
docker-compose logs -f websocket-vad
```

## Troubleshooting

- **Backend not responding**: Check Docker logs with `docker-compose logs backend`
- **WebSocket issues**: Ensure ports 5003 is not blocked by firewalls
- **Supabase connection issues**: Verify that the Supabase container is running with `docker ps`
- **TTS not working**: Check the backend logs for model loading issues
- **Emotion analysis errors**: Check the emotion service logs with `docker-compose logs emotion`
- **Permissions issues**: You might need to run docker commands with `sudo` on some systems 