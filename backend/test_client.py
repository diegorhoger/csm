#!/usr/bin/env python3
"""
Simple test client for the CSM Backend API.
Tests the basic API endpoints and WebSocket functionality.
"""

import sys
import requests
import socketio
import time
import json
import argparse

def test_rest_api(base_url):
    """Test the REST API endpoints."""
    print("Testing REST API...")
    
    # Health check
    try:
        response = requests.get(f"{base_url}/api/health")
        if response.status_code == 200:
            print("✅ Health check successful")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Get mentors
    try:
        response = requests.get(f"{base_url}/api/mentors")
        if response.status_code == 200:
            mentors = response.json().get('mentors', [])
            print(f"✅ Mentors API successful: {len(mentors)} mentors found")
        else:
            print(f"❌ Mentors API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Mentors API error: {e}")
    
    # Audio analysis threshold
    try:
        response = requests.get(f"{base_url}/api/audio-analysis/threshold")
        if response.status_code == 200:
            threshold = response.json().get('threshold', 0)
            print(f"✅ Audio threshold API successful: threshold={threshold}")
        else:
            print(f"❌ Audio threshold API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Audio threshold API error: {e}")

def test_socketio(base_url):
    """Test the SocketIO functionality."""
    print("\nTesting Socket.IO...")
    
    # Initialize Socket.IO client
    sio = socketio.Client()
    
    # Define event handlers
    @sio.event
    def connect():
        print("✅ Socket.IO connected")
    
    @sio.event
    def disconnect():
        print("Socket.IO disconnected")
    
    @sio.event
    def connected(data):
        print(f"✅ Connected event: {data}")
        
        # Initialize VAD session
        sio.emit('init_vad', {})
    
    @sio.event
    def vad_initialized(data):
        print(f"✅ VAD initialized: session_id={data.get('session_id')}")
        
        # Test sending audio level
        session_id = data.get('session_id')
        sio.emit('process_audio', {
            'session_id': session_id,
            'level': 0.5  # Dummy audio level
        })
        
        # Force recalibration
        sio.emit('force_recalibration', {
            'session_id': session_id
        })
        
        # Test debug state
        sio.emit('get_debug_state', {
            'session_id': session_id
        })
        
        # Schedule disconnect
        print("Waiting for responses...")
        sio.sleep(2)
        sio.disconnect()
    
    @sio.event
    def vad_result(data):
        print(f"✅ VAD result received: is_speech={data.get('is_speech')}")
    
    @sio.event
    def recalibration_started(data):
        print(f"✅ Recalibration started: {data.get('session_id')}")
    
    @sio.event
    def debug_state(data):
        if data:
            samples_count = data.get('samples_count', 0)
            print(f"✅ Debug state received: {samples_count} samples")
        else:
            print("❌ Empty debug state received")
    
    @sio.event
    def error(data):
        print(f"❌ Socket.IO error: {data.get('message')}")
    
    # Connect to the server
    try:
        sio.connect(base_url)
        sio.wait()
    except Exception as e:
        print(f"❌ Socket.IO connection error: {e}")

def main():
    parser = argparse.ArgumentParser(description='Test client for CSM Backend API')
    parser.add_argument('--url', default='http://localhost:5000', 
                        help='Base URL of the backend API (default: http://localhost:5000)')
    args = parser.parse_args()
    
    print(f"Testing backend at {args.url}")
    
    # Test REST API
    test_rest_api(args.url)
    
    # Test Socket.IO
    test_socketio(args.url)
    
    print("\nTest complete!")

if __name__ == '__main__':
    main() 