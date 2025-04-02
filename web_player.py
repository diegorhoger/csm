from flask import Flask, render_template, send_file, abort, send_from_directory
import os

app = Flask(__name__)

AUDIO_FOLDER = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def index():
    # Check if the audio file exists
    audio_exists = os.path.exists(os.path.join(AUDIO_FOLDER, 'full_conversation.wav'))
    return render_template('index.html', audio_exists=audio_exists)

@app.route('/audio/<filename>')
def serve_audio(filename):
    try:
        return send_from_directory(AUDIO_FOLDER, filename, mimetype='audio/wav')
    except FileNotFoundError:
        abort(404, description="Audio file not found. Please generate the audio first by running run_csm.py")

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Create the HTML template
    with open('templates/index.html', 'w') as f:
        f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>CSM Audio Player</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .audio-player {
            width: 100%;
            margin: 20px 0;
        }
        .controls {
            display: flex;
            gap: 10px;
            margin-top: 20px;
            justify-content: center;
        }
        button {
            padding: 10px 20px;
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background-color: #0056b3;
        }
        .error-message {
            color: #dc3545;
            text-align: center;
            margin: 20px 0;
            padding: 10px;
            background-color: #f8d7da;
            border-radius: 4px;
        }
        .instructions {
            background-color: #e9ecef;
            padding: 15px;
            border-radius: 4px;
            margin: 20px 0;
        }
    </style>
    <link rel="icon" href="data:,">
</head>
<body>
    <div class="container">
        <h1>CSM Audio Player</h1>
        {% if not audio_exists %}
        <div class="error-message">
            Audio file not found! Please follow these steps:
        </div>
        <div class="instructions">
            <ol>
                <li>Open a terminal</li>
                <li>Navigate to the project directory</li>
                <li>Run: <code>python run_csm.py</code></li>
                <li>Wait for the audio to be generated</li>
                <li>Refresh this page</li>
            </ol>
        </div>
        {% else %}
        <audio id="audioPlayer" class="audio-player" controls>
            <source src="/audio/full_conversation.wav" type="audio/wav">
            Your browser does not support the audio element.
        </audio>
        <div class="controls">
            <button onclick="document.getElementById('audioPlayer').play()">Play</button>
            <button onclick="document.getElementById('audioPlayer').pause()">Pause</button>
            <button onclick="document.getElementById('audioPlayer').currentTime = 0">Reset</button>
        </div>
        {% endif %}
    </div>
</body>
</html>
        ''')
    
    # Run the Flask app
    app.run(debug=True, port=5000) 