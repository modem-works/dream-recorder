// Make socket and DOM elements available globally
window.socket = io();
window.statusDiv = document.getElementById('status');
window.messageDiv = document.getElementById('message');
window.transcriptionDiv = document.getElementById('transcription');
window.videoPromptDiv = document.getElementById('videoPrompt');
window.loadingDiv = document.getElementById('loading');
window.videoContainer = document.getElementById('videoContainer');
window.generatedVideo = document.getElementById('generatedVideo');
window.videoPrompt = document.getElementById('videoPrompt');

// Initialize video player
window.generatedVideo.loop = true;

// Socket event handlers
window.socket.on('connect', () => {
    console.log('Connected to server');
    window.messageDiv.textContent = '';
    if (window.StateManager) {
        // Don't update state if we're in startup sequence
        if (window.StateManager.currentState === window.StateManager.STATES.STARTUP) {
            console.log('Ignoring connect state update during startup sequence');
            return;
        }
        window.StateManager.updateState(window.StateManager.STATES.CLOCK);
    } else {
        window.statusDiv.textContent = 'Connected';
    }
});

window.socket.on('disconnect', () => {
    console.log('Disconnected from server');
    window.messageDiv.textContent = 'Disconnected from server';
    if (window.StateManager) {
        window.StateManager.updateState(window.StateManager.STATES.ERROR, 'Disconnected from server');
    } else {
        window.statusDiv.textContent = 'Disconnected';
    }
});

window.socket.on('state_update', (state) => {
    console.log('Received state_update:', state);
    updateUI(state);
    
    // Show or hide errorDiv based on state
    if (window.errorDiv) {
        if (state.status === 'error' && state.error_message) {
            window.errorDiv.textContent = state.error_message;
            window.errorDiv.style.display = 'block';
        } else {
            window.errorDiv.style.display = 'none';
        }
    }

    // Update StateManager based on server state
    if (window.StateManager) {
        // Don't update state if we're in startup sequence
        if (window.StateManager.currentState === window.StateManager.STATES.STARTUP) {
            console.log('Ignoring state_update during startup sequence');
            return;
        }

        if (state.is_recording) {
            window.StateManager.updateState(window.StateManager.STATES.RECORDING);
        } else if (state.status === 'processing') {
            window.StateManager.updateState(window.StateManager.STATES.PROCESSING);
        } else if (state.video_url) {
            window.StateManager.updateState(window.StateManager.STATES.PLAYBACK);
        } else {
            window.StateManager.updateState(window.StateManager.STATES.CLOCK);
        }
    } else {
        window.statusDiv.textContent = `${state.status}`;
    }
});

window.socket.on('transcription_update', (data) => {
    console.log('Received transcription_update:', data);
    window.transcriptionDiv.textContent = data.text;
});

window.socket.on('video_prompt_update', (data) => {
    console.log('Received video_prompt_update:', data);
    window.videoPromptDiv.textContent = data.text;
    window.loadingDiv.style.display = 'none';
});

window.socket.on('video_ready', (data) => {
    console.log('Received video_ready:', data);
    window.videoContainer.style.display = 'block';
    window.generatedVideo.src = data.url;
    window.loadingDiv.style.display = 'none';
    window.messageDiv.textContent = 'Dream generation complete';
    
    if (window.StateManager) {
        window.StateManager.updateState(window.StateManager.STATES.PLAYBACK);
    }
});

window.socket.on('previous_video', (data) => {
    console.log('Received previous_video:', data);
    if (data.url) {
        window.videoContainer.style.display = 'block';
        window.generatedVideo.src = data.url;
        window.loadingDiv.style.display = 'none';
        
        if (window.StateManager) {
            window.StateManager.updateState(window.StateManager.STATES.PLAYBACK);
        }
    } else {
        // No previous video available
        window.messageDiv.textContent = 'No previous video available';
        if (window.StateManager) {
            window.StateManager.updateState(window.StateManager.STATES.ERROR, 'No previous video available');
            // Auto-clear error after 3 seconds
            setTimeout(() => {
                if (window.StateManager.currentState === window.StateManager.STATES.ERROR) {
                    window.StateManager.goToClock();
                    window.messageDiv.textContent = '';
                }
            }, 3000);
        }
    }
});

window.socket.on('error', (data) => {
    console.log('Received error message:', data);
    window.messageDiv.textContent = data.message;
    
    // Show errorDiv with the error message
    if (window.errorDiv) {
        window.errorDiv.textContent = data.message;
        window.errorDiv.style.display = 'block';
    }
    if (window.StateManager) {
        window.StateManager.updateState(window.StateManager.STATES.ERROR, data.message);
    }
});

window.socket.on('recording_state', (data) => {
    console.log('Received recording_state:', data);
    if (window.StateManager) {
        if (data.status === 'recording') {
            window.StateManager.handleDeviceEvent('double_tap');
        } else if (data.status === 'processing') {
            window.StateManager.handleDeviceEvent('single_tap');
        }
    } else if (window.startRecording && data.status === 'recording') {
        window.startRecording();
    } else if (window.stopRecording && data.status === 'processing') {
        window.stopRecording();
    }
});

window.socket.on('device_event', (data) => {
    console.log('Received device_event:', data);
    if (window.StateManager) {
        // Prefer camelCase, fallback to snake_case for compatibility
        const eventType = data.eventType;
        window.StateManager.handleDeviceEvent(eventType);
    } else if (window.stopRecording) {
        window.stopRecording();
    }
});

window.socket.on('play_video', (data) => {
    console.log('Received play_video:', data);
    if (data.video_url) {
        window.videoContainer.style.display = 'block';
        window.generatedVideo.src = data.video_url;
        window.generatedVideo.loop = data.loop || false;
        window.loadingDiv.style.display = 'none';
        
        if (window.StateManager) {
            window.StateManager.updateState(window.StateManager.STATES.PLAYBACK);
        }
    } else {
        // No video available
        window.messageDiv.textContent = 'No video available';
        if (window.StateManager) {
            window.StateManager.updateState(window.StateManager.STATES.ERROR, 'No video available');
            // Auto-clear error after 3 seconds
            setTimeout(() => {
                if (window.StateManager.currentState === window.StateManager.STATES.ERROR) {
                    window.StateManager.updateState(window.StateManager.STATES.CLOCK);
                    window.messageDiv.textContent = '';
                }
            }, 3000);
        }
    }
});

window.socket.on('reload_config', () => {
    console.log('Received reload_config event, reloading page...');
    window.location.reload();
});

// UI update functions
function updateUI(state) {
    // Don't update status through this function since StateManager handles it
    if (!window.StateManager) {
        window.statusDiv.textContent = state.status;
    }
}
