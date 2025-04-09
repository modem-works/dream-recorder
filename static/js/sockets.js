// Make socket and DOM elements available globally
window.socket = io();
window.statusDiv = document.getElementById('status');
window.errorDiv = document.getElementById('error');
window.transcriptionDiv = document.getElementById('transcription');
window.videoPromptDiv = document.getElementById('videoPrompt');
window.loadingDiv = document.getElementById('loading');
window.videoContainer = document.getElementById('videoContainer');
window.generatedVideo = document.getElementById('generatedVideo');
window.generateDreamBtn = document.getElementById('generateDreamBtn');

// Socket event handlers
window.socket.on('connect', () => {
    console.log('Connected to server');
    window.errorDiv.textContent = '';
});

window.socket.on('disconnect', () => {
    console.log('Disconnected from server');
    window.errorDiv.textContent = 'Disconnected from server';
});

window.socket.on('state_update', (state) => {
    console.log('Received state_update:', state);
    updateUI(state);
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
    window.generateDreamBtn.disabled = false;
});

window.socket.on('error', (data) => {
    console.log('Received error message:', data);
    window.errorDiv.textContent = data.message;
});

window.socket.on('recording_state', (data) => {
    console.log('Received recording_state:', data);
    if (window.startRecording) {
        window.startRecording();
    }
});

window.socket.on('device_event', (data) => {
    console.log('Received device_event:', data);
    if (window.stopRecording) {
        window.stopRecording();
    }
});

// UI update functions
function updateUI(state) {
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    
    startBtn.disabled = state.is_recording;
    stopBtn.disabled = !state.is_recording;
    window.statusDiv.textContent = state.status;
    
    // Update button visibility based on recording state
    if (state.is_recording) {
        startBtn.style.display = 'none';
        stopBtn.style.display = 'inline-block';
        window.loadingDiv.style.display = 'none';
    } else {
        startBtn.style.display = 'inline-block';
        stopBtn.style.display = 'none';
        if (state.status === 'processing') {
            window.loadingDiv.style.display = 'block';
        } else {
            window.loadingDiv.style.display = 'none';
        }
    }
    
    // Update generate dream button visibility based on state
    if (state.video_prompt && !state.video_url) {
        window.generateDreamBtn.style.display = 'block';
    } else {
        window.generateDreamBtn.style.display = 'none';
    }
}

// Event listeners
window.generateDreamBtn.addEventListener('click', () => {
    window.generateDreamBtn.disabled = true;
    window.loadingDiv.style.display = 'block';
    console.log('Sending generate_video with prompt:', window.videoPromptDiv.textContent);
    window.socket.emit('generate_video', { prompt: window.videoPromptDiv.textContent });
}); 