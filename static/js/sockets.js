// Make socket and DOM elements available globally
window.socket = io();
window.statusDiv = document.getElementById('status');
window.errorDiv = document.getElementById('error');
window.transcriptionDiv = document.getElementById('transcription');
window.videoPromptDiv = document.getElementById('videoPrompt');
window.loadingDiv = document.getElementById('loading');
window.videoContainer = document.getElementById('videoContainer');
window.generatedVideo = document.getElementById('generatedVideo');
window.videoPrompt = document.getElementById('videoPrompt');

// Socket event handlers
window.socket.on('connect', () => {
    console.log('Connected to server');
    window.errorDiv.textContent = '';
    if (window.StateManager) {
        window.StateManager.updateState(window.StateManager.STATES.IDLE);
    }
});

window.socket.on('disconnect', () => {
    console.log('Disconnected from server');
    window.errorDiv.textContent = 'Disconnected from server';
    if (window.StateManager) {
        window.StateManager.updateState(window.StateManager.STATES.ERROR, 'Disconnected from server');
    }
});

window.socket.on('state_update', (state) => {
    console.log('Received state_update:', state);
    updateUI(state);
    
    // Update StateManager based on server state
    if (window.StateManager) {
        if (state.is_recording) {
            window.StateManager.updateState(window.StateManager.STATES.RECORDING);
        } else if (state.status === 'processing') {
            window.StateManager.updateState(window.StateManager.STATES.PROCESSING);
        } else if (state.video_url) {
            window.StateManager.updateState(window.StateManager.STATES.PLAYBACK);
        } else {
            window.StateManager.updateState(window.StateManager.STATES.IDLE);
        }
    }
});

window.socket.on('transcription_update', (data) => {
    console.log('Received transcription_update:', data);
    const transcriptionOutput = document.getElementById('transcriptionOutput');
    transcriptionOutput.style.display = 'block';
    window.transcriptionDiv.textContent = data.text;
});

window.socket.on('video_prompt_update', (data) => {
    console.log('Received video_prompt_update:', data);
    const transcriptionOutput = document.getElementById('transcriptionOutput');
    const videoPromptOutput = document.getElementById('videoPromptOutput');
    transcriptionOutput.style.display = 'none';
    videoPromptOutput.style.display = 'block';
    window.videoPromptDiv.textContent = data.text;
    window.loadingDiv.style.display = 'none';
});

window.socket.on('video_ready', (data) => {
    console.log('Received video_ready:', data);
    const transcriptionOutput = document.getElementById('transcriptionOutput');
    const videoPromptOutput = document.getElementById('videoPromptOutput');
    transcriptionOutput.style.display = 'none';
    videoPromptOutput.style.display = 'none';
    window.videoContainer.style.display = 'block';
    window.generatedVideo.src = data.url;
    window.loadingDiv.style.display = 'none';
    window.stopRecordingBtn.disabled = false;
    window.videoPrompt.textContent = 'Dream generation complete!';
    
    if (window.StateManager) {
        window.StateManager.updateState(window.StateManager.STATES.PLAYBACK);
    }
});

window.socket.on('previous_video', (data) => {
    console.log('Received previous_video:', data);
    if (data.url) {
        const transcriptionOutput = document.getElementById('transcriptionOutput');
        const videoPromptOutput = document.getElementById('videoPromptOutput');
        transcriptionOutput.style.display = 'none';
        videoPromptOutput.style.display = 'none';
        window.videoContainer.style.display = 'block';
        window.generatedVideo.src = data.url;
        window.loadingDiv.style.display = 'none';
        
        if (window.StateManager) {
            window.StateManager.updateState(window.StateManager.STATES.PLAYBACK);
        }
    } else {
        // No previous video available
        window.errorDiv.textContent = 'No previous video available';
        if (window.StateManager) {
            window.StateManager.updateState(window.StateManager.STATES.ERROR, 'No previous video available');
            // Auto-clear error after 3 seconds
            setTimeout(() => {
                if (window.StateManager.currentState === window.StateManager.STATES.ERROR) {
                    window.StateManager.goToIdle();
                    window.errorDiv.textContent = '';
                }
            }, 3000);
        }
    }
});

window.socket.on('error', (data) => {
    console.log('Received error message:', data);
    window.errorDiv.textContent = data.message;
    
    if (window.StateManager) {
        window.StateManager.updateState(window.StateManager.STATES.ERROR, data.message);
    }
});

window.socket.on('recording_state', (data) => {
    console.log('Received recording_state:', data);
    if (window.StateManager) {
        window.StateManager.handleDeviceEvent('hold_start');
    } else if (window.startRecording) {
        window.startRecording();
    }
});

window.socket.on('device_event', (data) => {
    console.log('Received device_event:', data);
    if (window.StateManager) {
        window.StateManager.handleDeviceEvent(data.event_type || 'hold_release');
    } else if (window.stopRecording) {
        window.stopRecording();
    }
});

// UI update functions
function updateUI(state) {
    // Don't update status through this function since StateManager handles it
    if (!window.StateManager) {
        window.statusDiv.textContent = state.status;
    }
}
