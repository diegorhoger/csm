@app.route('/api/audio-analysis', methods=['OPTIONS'])
def audio_analysis_options():
    """Handle CORS preflight requests for audio-analysis endpoint."""
    response = jsonify({"status": "ok"})
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@app.route('/api/audio-analysis/calibrate', methods=['OPTIONS'])
def audio_analysis_calibrate_options():
    """Handle CORS preflight requests for audio-analysis/calibrate endpoint."""
    response = jsonify({"status": "ok"})
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@app.route('/api/audio-analysis', methods=['POST'])
def audio_analysis():
    """Process audio level data for speech detection."""
    try:
        data = request.json
        if not data or 'level' not in data:
            return jsonify({"error": "Missing 'level' in request"}), 400
        
        # Process the audio sample
        timestamp = data.get('timestamp')
        result = audio_analysis_service.add_audio_sample(data['level'], timestamp)
        
        # Add CORS headers to the response
        response = jsonify(result)
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    except Exception as e:
        print(f"Error in audio analysis: {e}")
        print(traceback.format_exc())
        response = jsonify({"error": str(e)}), 500
        response[0].headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response[0].headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response[0].headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response[0].headers.add('Access-Control-Allow-Credentials', 'true')
        return response

@app.route('/api/audio-analysis/calibrate', methods=['POST'])
def force_calibration():
    """Force recalibration of the audio analysis service."""
    try:
        audio_analysis_service.force_recalibration()
        response = jsonify({"status": "success", "message": "Recalibration started"})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    except Exception as e:
        print(f"Error in force calibration: {e}")
        print(traceback.format_exc())
        response = jsonify({"error": str(e)}), 500
        response[0].headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response[0].headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response[0].headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response[0].headers.add('Access-Control-Allow-Credentials', 'true')
        return response 