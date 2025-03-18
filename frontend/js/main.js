/**
 * Dream Recorder - Main Frontend Script
 * Handles WebSocket connection, audio recording, and UI updates
 */

import { io } from 'socket.io-client';
import RecordRTC from 'recordrtc';
import Plyr from 'plyr';
import './audio-visualizer.js';

// Configuration
// Always use the current URL to ensure the correct port is used
const SERVER_URL = window.location.origin;

// Socket.IO options to ensure compatibility with different backends
const socketOptions = {
    transports: ['websocket', 'polling'],
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
    timeout: 20000
};

// State
let socket = null;
let recorder = null;
let audioContext = null;
let audioStream = null;
let recordingStartTime = null;
let recordingTimer = null;
let isRecording = false;
let currentState = 'ready';
let videoPlayer = null;
let gpioAvailable = false;
let audioAvailable = false;
let recordingSeconds = 0;
let maxRecordingDuration = 30; // Default max recording duration in seconds
let enhancedPromptReceived = false; // Flag to track if we've received an enhanced prompt

// DOM Elements
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');
const micIcon = document.getElementById('mic-icon');
const recordingTime = document.getElementById('recording-time');
const recordingPrompt = document.getElementById('recording-prompt');
const transcriptionText = document.getElementById('transcription-text');
const enhancedPromptText = document.getElementById('enhanced-prompt-text');
const dreamVideo = document.getElementById('dream-video');
const progressBar = document.getElementById('progress-bar');
const progressText = document.getElementById('progress-text');
const manualTriggerBtn = document.getElementById('manual-trigger');
const resetButton = document.getElementById('reset-button');

// Sections
const recordingSection = document.getElementById('recording-section');
const transcriptionSection = document.getElementById('transcription-section');
const videoSection = document.getElementById('video-section');

// Create an error message container
function createErrorContainer() {
    let errorContainer = document.getElementById('error-container');
    if (!errorContainer) {
        errorContainer = document.createElement('div');
        errorContainer.id = 'error-container';
        errorContainer.className = 'error-container';
        
        // Add it after the progress-container
        const progressContainer = document.querySelector('.progress-container');
        if (progressContainer && progressContainer.parentNode) {
            progressContainer.parentNode.insertBefore(errorContainer, progressContainer.nextSibling);
        } else {
            // Fallback to adding at the bottom of main
            const main = document.querySelector('main');
            if (main) {
                main.appendChild(errorContainer);
            }
        }
        
        // Add styles for the error container
        const style = document.createElement('style');
        style.textContent = `
            .error-container {
                background-color: #ffebee;
                border-left: 4px solid #f44336;
                color: #b71c1c;
                padding: 15px;
                margin: 15px 0;
                border-radius: 4px;
                font-size: 14px;
                line-height: 1.5;
                max-width: 800px;
                margin-left: auto;
                margin-right: auto;
                display: none;
                animation: fadeIn 0.3s ease-in-out;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(-10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .error-container.visible {
                display: block;
            }
            
            .error-container .error-title {
                font-weight: bold;
                margin-bottom: 5px;
            }
            
            .error-container .error-message {
                margin-bottom: 10px;
            }
            
            .error-container .error-action {
                display: flex;
                justify-content: flex-end;
            }
            
            .error-container button {
                background-color: transparent;
                border: none;
                color: #f44336;
                cursor: pointer;
                font-size: 14px;
                text-transform: uppercase;
                padding: 5px 10px;
            }
            
            .error-container button:hover {
                background-color: rgba(244, 67, 54, 0.1);
                border-radius: 4px;
            }
        `;
        document.head.appendChild(style);
    }
    return errorContainer;
}

// Function to show error messages without disrupting other UI components
function showErrorMessage(message) {
    const errorContainer = createErrorContainer();
    
    // Clear existing content
    errorContainer.innerHTML = '';
    
    // Create structure
    const errorTitle = document.createElement('div');
    errorTitle.className = 'error-title';
    errorTitle.textContent = 'Error';
    
    const errorMessage = document.createElement('div');
    errorMessage.className = 'error-message';
    errorMessage.textContent = message;
    
    const errorAction = document.createElement('div');
    errorAction.className = 'error-action';
    
    // If we have an enhanced prompt in storage but it's not visible, add a button to show it
    const storedPrompt = sessionStorage.getItem('lastEnhancedPrompt');
    if (storedPrompt && (!enhancedPromptText.textContent || enhancedPromptText.textContent === 'Enhancing your dream description...')) {
        const showPromptButton = document.createElement('button');
        showPromptButton.textContent = 'Show Enhanced Prompt';
        showPromptButton.style.marginRight = '10px';
        showPromptButton.addEventListener('click', () => {
            // Display the prompt
            enhancedPromptText.textContent = storedPrompt;
            enhancedPromptReceived = true;
            
            // Make sure the container is visible
            const enhancedPromptContainer = document.getElementById('enhanced-prompt-container');
            if (enhancedPromptContainer) {
                enhancedPromptContainer.classList.add('loaded');
            }
            
            // Make transcription section visible
            transcriptionSection.classList.remove('hidden');
            
            showNotification('Enhanced prompt restored from storage', 'success');
        });
        errorAction.appendChild(showPromptButton);
    }
    
    const dismissButton = document.createElement('button');
    dismissButton.textContent = 'Dismiss';
    dismissButton.addEventListener('click', () => {
        errorContainer.classList.remove('visible');
    });
    
    // Assemble error container
    errorAction.appendChild(dismissButton);
    errorContainer.appendChild(errorTitle);
    errorContainer.appendChild(errorMessage);
    errorContainer.appendChild(errorAction);
    
    // Show the container
    errorContainer.classList.add('visible');
    
    // Automatically hide after 15 seconds
    setTimeout(() => {
        if (errorContainer.classList.contains('visible')) {
            errorContainer.classList.remove('visible');
        }
    }, 15000);
}

// UI State Map
const UIStateMap = {
    'ready': {
        statusColor: '#4caf50',
        statusText: 'Ready',
        progressBar: 0,
        progressText: 'Touch the sensor to start recording your dream',
        sections: { recording: true, transcription: false, video: false },
    },
    'recording': {
        statusColor: '#ff4081',
        statusText: 'Recording',
        progressBar: 25,
        progressText: 'Recording your dream... Touch the sensor again to finish',
        sections: { recording: true, transcription: false, video: false },
    },
    'processing_audio': {
        statusColor: '#ff9800',
        statusText: 'Processing',
        progressBar: 40,
        progressText: 'Transcribing your dream...',
        sections: { recording: true, transcription: false, video: false },
    },
    'enhancing_prompt': {
        statusColor: '#ff9800',
        statusText: 'Processing',
        progressBar: 55,
        progressText: 'Enhancing your dream description...',
        sections: { recording: false, transcription: true, video: false },
    },
    'generating_video': {
        statusColor: '#ff9800',
        statusText: 'Processing',
        progressBar: 70,
        progressText: 'Creating your dream visualization...',
        sections: { recording: false, transcription: true, video: false },
    },
    'processing_video': {
        statusColor: '#ff9800',
        statusText: 'Processing',
        progressBar: 85,
        progressText: 'Finalizing your dream video...',
        sections: { recording: false, transcription: true, video: false },
    },
    'video_ready': {
        statusColor: '#4caf50',
        statusText: 'Complete',
        progressBar: 100,
        progressText: 'Your dream visualization is ready',
        sections: { recording: false, transcription: true, video: true },
    },
    'error': {
        statusColor: '#f44336',
        statusText: 'Error',
        progressBar: 0,
        progressText: 'An error occurred. Please try again.',
        sections: { recording: true, transcription: true, video: false },
    }
};

// Initialize
document.addEventListener('DOMContentLoaded', initialize);

function initialize() {
    // Connect to WebSocket server
    connectToServer();
    
    // Set up manual trigger for testing without GPIO
    setupManualControls();
    
    // Initialize audio context
    try {
        window.AudioContext = window.AudioContext || window.webkitAudioContext;
        audioContext = new AudioContext();
        // Don't set audioAvailable to true yet - wait for the server to confirm
    } catch (e) {
        console.error('Web Audio API not supported', e);
        audioAvailable = false;
        showNotification('Audio recording not supported in this browser', 'error');
    }
    
    // Set up native video player
    if (dreamVideo) {
        console.log("Setting up native HTML5 video player");
        dreamVideo.controls = true;
        dreamVideo.autoplay = false;
        dreamVideo.style.width = '100%';
        dreamVideo.style.maxWidth = '640px';
        dreamVideo.style.margin = '0 auto';
        dreamVideo.style.display = 'block';
        
        // Add error handler
        dreamVideo.onerror = function() {
            console.error('Video error during init:', dreamVideo.error);
        };
    } else {
        console.error("Video element not found!");
    }
    
    // Update UI
    updateUIState('ready');
    
    // Remove any stale notifications from previous sessions
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => {
        notification.remove();
    });
    
    // Check for stored transcription and enhanced prompt from previous session
    try {
        const storedTranscription = sessionStorage.getItem('lastTranscription');
        const storedEnhancedPrompt = sessionStorage.getItem('lastEnhancedPrompt');
        
        if (storedTranscription) {
            console.log('Recovering stored transcription from session storage');
            transcriptionText.textContent = storedTranscription;
            
            // Style elements and ensure visibility
            const transcriptionContainer = document.getElementById('transcription-container');
            if (transcriptionContainer) {
                transcriptionContainer.classList.add('loaded');
            }
            
            // Make transcription section visible
            if (storedTranscription.trim() !== '') {
                transcriptionSection.classList.remove('hidden');
            }
        }
        
        if (storedEnhancedPrompt) {
            console.log('Recovering stored enhanced prompt from session storage');
            enhancedPromptText.textContent = storedEnhancedPrompt;
            
            // Set the flag to indicate we have an enhanced prompt
            enhancedPromptReceived = true;
            
            // Style elements and ensure visibility
            const enhancedPromptContainer = document.getElementById('enhanced-prompt-container');
            if (enhancedPromptContainer) {
                enhancedPromptContainer.classList.add('loaded');
            }
            
            // Make transcription section visible
            if (storedEnhancedPrompt.trim() !== '') {
                transcriptionSection.classList.remove('hidden');
            }
        }
    } catch (e) {
        console.warn('Could not recover stored transcription/prompt:', e);
    }
}

async function connectToServer() {
    try {
        // First, try to get server configuration to ensure correct ports
        fetch('/api/config')
            .then(response => {
                if (response.ok) return response.json();
                throw new Error('Could not fetch server config');
            })
            .then(serverConfig => {
                console.log('Server config:', serverConfig);
                // Use server-provided URL if available, otherwise fallback to current origin
                const serverUrl = serverConfig?.server_url || window.location.origin;
                console.log('Connecting to server at:', serverUrl);
                
                socket = io(serverUrl, socketOptions);
                
                // NEW: Add a socket interceptor to log all messages
                const originalOn = socket.on;
                socket.on = function(event, callback) {
                    const wrappedCallback = function(data) {
                        console.log(`%c[SOCKET EVENT] ${event}`, 'background:#3949ab;color:white;padding:3px;border-radius:3px', data);
                        return callback.apply(this, arguments);
                    };
                    return originalOn.call(this, event, wrappedCallback);
                };
                
                // Socket event listeners
                socket.on('connect', () => {
                    console.log('Connected to server');
                    showNotification('Connected to server', 'success');
                });
                
                socket.on('disconnect', () => {
                    console.log('Disconnected from server');
                    showNotification('Disconnected from server', 'error');
                });
                
                socket.on('connect_error', (error) => {
                    console.error('Connection error:', error);
                    showNotification('Connection error: ' + error.message, 'error');
                });
                
                socket.on('status', (data) => {
                    console.log('Status update:', data);
                    
                    // If we've received an enhanced prompt, ALWAYS keep transcription section visible
                    const hasContent = enhancedPromptReceived || 
                                      (transcriptionText && transcriptionText.textContent.trim() !== '');
                    
                    // NEW: When state changes to generating_video, ensure enhanced prompt is visible
                    if (data.state === 'generating_video' && transcriptionText && transcriptionText.textContent) {
                        console.log('State changed to generating_video, ensuring enhanced prompt is visible');
                        
                        // Check if we have an enhanced prompt
                        if (!enhancedPromptText.textContent || 
                            enhancedPromptText.textContent === 'Enhancing your dream description...' ||
                            enhancedPromptText.textContent.trim() === '') {
                            
                            // If there's no enhanced prompt content, show a default message
                            console.log('Enhanced prompt not found, displaying default message');
                            enhancedPromptText.textContent = `Enhanced version of "${transcriptionText.textContent.trim()}"\n\nThis dream scene will be visualized with vibrant colors, dynamic camera movements, and atmospheric lighting to create an immersive experience.`;
                            enhancedPromptReceived = true;
                            
                            // Store it in session storage
                            try {
                                sessionStorage.setItem('lastEnhancedPrompt', enhancedPromptText.textContent);
                            } catch (e) {
                                console.warn('Could not store enhanced prompt in session storage', e);
                            }
                            
                            // Style elements and ensure visibility
                            const enhancedPromptContainer = document.getElementById('enhanced-prompt-container');
                            if (enhancedPromptContainer) {
                                enhancedPromptContainer.classList.add('loaded');
                            }
                            
                            // Show a notification about the fallback
                            showNotification('Generated fallback enhanced prompt', 'info');
                        }
                        
                        // Ensure transcription section is visible
                        transcriptionSection.classList.remove('hidden');
                    }
                    
                    // Special handling for error state - don't hide transcription section
                    if (data.state === 'error') {
                        // Update status indicators
                        statusDot.style.backgroundColor = UIStateMap.error.statusColor;
                        statusText.textContent = UIStateMap.error.statusText;
                        progressBar.style.width = `${UIStateMap.error.progressBar}%`;
                        progressText.textContent = UIStateMap.error.progressText;
                        
                        // Show the error message in our custom container
                        if (data.message) {
                            showErrorMessage(data.message);
                        } else {
                            showErrorMessage('An unknown error occurred. Your transcription is still available.');
                        }
                        
                        // Show reset button when in error state
                        resetButton.classList.remove('hidden');
                        
                        // Force transcription section to be visible if we have content
                        if (hasContent) {
                            console.log('Error state: Preserving transcription section visibility');
                            // Force transcription section to be visible
                            transcriptionSection.classList.remove('hidden');
                            
                            // Update only recording and video sections
                            recordingSection.classList.toggle('hidden', !UIStateMap.error.sections.recording);
                            videoSection.classList.toggle('hidden', !UIStateMap.error.sections.video);
                        } else {
                            // Regular error UI update if no content yet
                            updateUIState('error');
                        }
                    } else {
                        // For non-error states, hide any visible error message
                        const errorContainer = document.getElementById('error-container');
                        if (errorContainer && errorContainer.classList.contains('visible')) {
                            errorContainer.classList.remove('visible');
                        }
                        
                        // Always preserve transcription if we have content, regardless of state
                        if (hasContent) {
                            console.log(`Preserving transcription during ${data.state} state`);
                            
                            // Update status indicators
                            statusDot.style.backgroundColor = UIStateMap[data.state].statusColor;
                            statusText.textContent = UIStateMap[data.state].statusText;
                            progressBar.style.width = `${UIStateMap[data.state].progressBar}%`;
                            progressText.textContent = UIStateMap[data.state].progressText;
                            
                            // Update recording visibility
                            recordingSection.classList.toggle('hidden', !UIStateMap[data.state].sections.recording);
                            videoSection.classList.toggle('hidden', !UIStateMap[data.state].sections.video);
                            
                            // NEVER hide transcription section if we have content
                            transcriptionSection.classList.remove('hidden');
                            
                            // Update current state
                            currentState = data.state;
                        } else {
                            // Normal state update if no content yet
                            updateUIState(data.state);
                        }
                    }
                    
                    // Update GPIO and audio availability
                    const prevAudioAvailable = audioAvailable;
                    gpioAvailable = data.gpio_available || false;
                    audioAvailable = data.audio_available || false;
                    
                    console.log('Hardware availability:', {gpioAvailable, audioAvailable});
                    
                    // If audio availability has changed, update the UI
                    if (prevAudioAvailable !== audioAvailable) {
                        console.log(`Audio availability changed from ${prevAudioAvailable} to ${audioAvailable}`);
                        // Update UI based on availability
                        updateAvailabilityUI();
                    }
                });
                
                socket.on('start_recording', () => {
                    startRecording();
                });
                
                socket.on('stop_recording', () => {
                    stopRecording();
                });
                
                socket.on('transcription', (data) => {
                    console.log('Received transcription:', data.text);
                    transcriptionText.textContent = data.text;
                    
                    // Make sure the transcription section is visible
                    transcriptionSection.classList.remove('hidden');
                    
                    // Store the transcription in sessionStorage to recover it if needed
                    try {
                        sessionStorage.setItem('lastTranscription', data.text);
                    } catch (e) {
                        console.warn('Could not store transcription in session storage', e);
                    }
                    
                    // Clear enhanced prompt until we receive it
                    enhancedPromptText.textContent = 'Enhancing your dream description...';
                    
                    // Style elements and ensure visibility
                    const transcriptionContainer = document.getElementById('transcription-container');
                    if (transcriptionContainer) {
                        transcriptionContainer.classList.add('loaded');
                        console.log('Transcription container loaded and visible');
                    }
                });
                
                socket.on('enhanced_prompt', (data) => {
                    console.log('Received enhanced prompt:', data.text);
                    
                    // Add debug logs to help troubleshoot
                    console.log('Enhanced prompt element exists:', enhancedPromptText !== null);
                    console.log('Enhanced prompt container element:', document.getElementById('enhanced-prompt-container'));
                    
                    try {
                        // Update the enhanced prompt text
                        if (enhancedPromptText) {
                            console.log('Before setting textContent, current value:', enhancedPromptText.textContent);
                            enhancedPromptText.textContent = data.text;
                            console.log('After setting textContent, new value:', enhancedPromptText.textContent);
                        } else {
                            console.error('Enhanced prompt text element is null!');
                        }
                        
                        // Set our flag indicating we've received an enhanced prompt
                        enhancedPromptReceived = true;
                        console.log('Set enhancedPromptReceived flag to true');
                        
                        // Make sure the transcription section is visible
                        transcriptionSection.classList.remove('hidden');
                        console.log('Removed hidden class from transcription section');
                        
                        // Style elements and ensure visibility
                        const enhancedPromptContainer = document.getElementById('enhanced-prompt-container');
                        if (enhancedPromptContainer) {
                            enhancedPromptContainer.classList.add('loaded');
                            console.log('Enhanced prompt container loaded and visible');
                        } else {
                            console.error('Enhanced prompt container element is null!');
                        }
                        
                        // Store the enhanced prompt in sessionStorage to recover it if needed
                        try {
                            sessionStorage.setItem('lastEnhancedPrompt', data.text);
                            console.log('Stored enhanced prompt in sessionStorage');
                        } catch (e) {
                            console.warn('Could not store enhanced prompt in session storage', e);
                        }
                    } catch (err) {
                        console.error('Error in enhanced_prompt handler:', err);
                    }
                });
                
                socket.on('video_ready', (data) => {
                    console.log('[FIREFOX HANDLER] Video ready event received:', data);
                    
                    // Try to load the video using our function
                    const success = loadVideo(data.video_path);
                    
                    // If our function failed, try a direct URL approach
                    if (!success) {
                        console.log('[FIREFOX HANDLER] Direct loading failed, trying URL redirect approach');
                        
                        try {
                            // Get video URL
                            const videoUrl = data.video_path.startsWith('http') ? 
                                data.video_path : `${SERVER_URL}/videos/${data.video_path.split('/').pop()}`;
                            
                            // Create a direct URL to the current page with video parameter
                            const directUrl = `${window.location.origin}${window.location.pathname}?video=${encodeURIComponent(videoUrl)}`;
                            
                            // Show notification
                            showNotification('Redirecting to video player...', 'info');
                            
                            // Redirect after a short delay
                            setTimeout(() => {
                                window.location.href = directUrl;
                            }, 1000);
                        } catch (e) {
                            console.error('[FIREFOX HANDLER] Error with redirect approach:', e);
                            showNotification('Error loading video. Please try again.', 'error');
                        }
                    }
                });
                
                // NEW: Handle direct notification messages from server
                socket.on('notification', (data) => {
                    console.log('Received notification:', data);
                    showNotification(data.message, data.type || 'info');
                });
            })
            .catch(error => {
                console.error('Error setting up socket connection:', error);
                showNotification('Failed to connect to server', 'error');
            });
    } catch (error) {
        console.error('Error connecting to server:', error);
        showNotification('Failed to connect to server', 'error');
    }
}

function updateAvailabilityUI() {
    // Update recording prompt based on hardware availability
    if (!gpioAvailable) {
        recordingPrompt.textContent = 'GPIO not available. Use manual controls to record.';
        manualTriggerBtn.classList.remove('hidden');
    } else {
        // Reset the prompt if GPIO is available
        recordingPrompt.textContent = 'Touch the sensor to start recording your dream';
    }
    
    // Only show audio warning if audio is definitely not available
    // Do a thorough check to make sure audio really isn't available
    if (!audioAvailable) {
        console.warn('Audio recording is not available - displaying warning');
        recordingPrompt.textContent = 'Audio recording not available. The system will use sample text.';
        
        // Only show the notification if we haven't already shown it
        // Use a flag to track if we've shown the notification
        if (!window.audioWarningShown) {
            window.audioWarningShown = true;
            showNotification('Audio recording not available - using sample text', 'warning');
        }
    } else {
        // Clear any warnings if audio is actually available
        console.log('Audio recording is available and will be used');
        
        // Clear the warning flag
        window.audioWarningShown = false;
        
        // Remove any existing audio unavailability notifications
        const notifications = document.querySelectorAll('.notification');
        notifications.forEach(notification => {
            if (notification.textContent.includes('Audio recording not available')) {
                notification.remove();
            }
        });
    }
}

function setupManualControls() {
    // Always show manual controls
    manualTriggerBtn.classList.remove('hidden');
    
    // Manual trigger button toggles recording state
    manualTriggerBtn.addEventListener('click', () => {
        if (currentState === 'ready') {
            console.log("Manual trigger: starting recording");
            
            // Send a single event to the server - the server will handle the UI update
            // and send back a start_recording event
            socket.emit('manual_trigger', { action: 'start_recording' });
            
            // Don't call startRecording() here - wait for the server to tell us to start
        } else if (currentState === 'recording') {
            console.log("Manual trigger: stopping recording");
            
            // Notify server to stop recording
            socket.emit('manual_trigger', { action: 'stop_recording' });
            
            // Stop recording on the client side
            if (audioAvailable && recorder) {
                stopRecording();
            } else {
                // Use the correct state - 'processing_audio' matches the backend state
                updateUIState('processing_audio');
                // Notify the server that recording is complete even if we don't have audio
                socket.emit('recording_complete');
            }
        }
    });
    
    // Reset button resets the application state
    resetButton.addEventListener('click', () => {
        resetApplication();
    });
}

function startRecording() {
    if (isRecording) return;
    
    console.log(`Starting recording with audioAvailable: ${audioAvailable}`);
    
    // Ensure that the UI is updated with the current audio status
    // before trying to start recording
    updateAvailabilityUI();
    
    // Check if audio is available
    if (!audioAvailable) {
        console.warn('Audio recording is not available, using sample text');
        showMessage('Audio recording is not available. The system will use sample text instead.', 'warning');
        // We don't emit start_recording here since it's already sent by the manual trigger
        isRecording = true;
        updateUIState('recording');
        return;
    }
    
    // Now we know audio should be available, so let's try to access it
    console.log("Starting audio recording with browser API...");
    
    // Reset recording state
    recordingSeconds = 0;
    
    // Ensure we emit the start_recording event before accessing the microphone
    // This is important because we need the backend to initialize the recording session
    if (socket && socket.connected) {
        console.log("Notifying server that recording is starting");
        socket.emit('start_recording');
    } else {
        console.error("Socket not connected, cannot start recording properly");
        showMessage('Cannot connect to server. Please refresh the page.', 'error');
        return;
    }
    
    // Request high-quality audio with specific constraints for better recording
    const audioConstraints = {
        audio: {
            echoCancellation: false,    // Disable echo cancellation for better quality
            noiseSuppression: false,    // Disable noise suppression for cleaner audio
            autoGainControl: false,     // Disable auto gain for consistent levels
            sampleRate: 44100,          // Request 44.1kHz sample rate
            sampleSize: 16              // Request 16-bit samples
        }
    };
    
    navigator.mediaDevices.getUserMedia(audioConstraints)
        .then(function(stream) {
            console.log("Media stream obtained with constraints:", audioConstraints);
            
            // Get actual audio track settings to log them
            const audioTrack = stream.getAudioTracks()[0];
            const settings = audioTrack.getSettings();
            console.log("Actual audio track settings:", settings);
            
            // Since we successfully got audio, make sure the UI reflects this
            if (!audioAvailable) {
                audioAvailable = true;  // Update the global state
                console.log("Audio stream obtained successfully - updating audioAvailable to true");
                updateAvailabilityUI(); // Update the UI
            }
            
            // Define preferred audio format, with fallbacks
            let audioMimeType = 'audio/webm';
            
            // Check if the preferred MIME type is supported
            if (!MediaRecorder.isTypeSupported(audioMimeType)) {
                // Try alternatives
                if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
                    audioMimeType = 'audio/webm;codecs=opus';
                } else if (MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')) {
                    audioMimeType = 'audio/ogg;codecs=opus';
                }
            }
            
            console.log(`Using audio format: ${audioMimeType}`);
            
            audioStream = stream;
            
            // Create recorder with the selected MIME type and better options
            recorder = new RecordRTC(stream, {
                type: 'audio',
                mimeType: audioMimeType,
                recorderType: StereoAudioRecorder,
                desiredSampRate: 44100,       // Higher sample rate for better quality
                numberOfAudioChannels: 1,     // Mono recording is simpler for speech
                timeSlice: 500,               // Get data every 500ms
                disableLogs: false,           // Enable logs for debugging
                bufferSize: 16384,            // Larger buffer for better quality
                ondataavailable: function(blob) {
                    if (blob && blob.size > 0) {
                        try {
                            console.log(`Audio data chunk available: ${blob.size} bytes`);
                            const reader = new FileReader();
                            reader.onloadend = function() {
                                try {
                                    const base64data = reader.result.split(',')[1];
                                    if (base64data) {
                                        socket.emit('audio_data', base64data);
                                    }
                                } catch (e) {
                                    console.error('Error processing audio data:', e);
                                }
                            };
                            reader.readAsDataURL(blob);
                        } catch (e) {
                            console.error('Error handling audio data:', e);
                        }
                    } else {
                        console.warn('Received empty audio blob');
                    }
                }
            });
            
            // Start recording
            recorder.startRecording();
            
            // Start visualizer
            startVisualizer(stream);
            
            // Set UI state
            isRecording = true;
            updateUIState('recording');
            
            // Start recording timer
            recordingTimer = setInterval(function() {
                recordingSeconds++;
                updateRecordingTime();
                
                // Cap recording at maxRecordingDuration (30 seconds by default)
                if (recordingSeconds >= maxRecordingDuration) {
                    console.log(`Max recording duration of ${maxRecordingDuration}s reached`);
                    stopRecording();
                }
            }, 1000);
            
            micIcon.classList.add('recording');
        })
        .catch(function(err) {
            console.error('Error accessing microphone:', err);
            // Set audioAvailable to false since we couldn't access the mic
            audioAvailable = false;
            showMessage('Could not access the microphone. Check browser permissions. Using sample text instead.', 'error');
            
            // Even without audio, we can still proceed with the demo
            isRecording = true;
            updateUIState('recording');
        });
}

function stopRecording() {
    if (!isRecording) return;
    
    console.log("Stopping recording...");
    
    // Stop visualizer first to ensure clean UI update
    stopVisualizer();
    
    // Clear recording timer
    clearInterval(recordingTimer);
    micIcon.classList.remove('recording');
    
    // Handle the case where audio recording is not available
    if (!recorder || !audioAvailable) {
        // Clean up any resources
        isRecording = false;
        if (audioStream) {
            audioStream.getTracks().forEach(track => track.stop());
            audioStream = null;
        }
        
        // Just notify the server that recording is complete without audio
        socket.emit('recording_complete');
        updateUIState('processing_audio');
        return;
    }
    
    // Flag to prevent duplicate recording_complete events
    let recordingCompleteEmitted = false;
    
    try {
        // Stop recorder
        recorder.stopRecording(() => {
            console.log("Recorder stopped");
            
            try {
                // Get recorded blob
                const blob = recorder.getBlob();
                console.log("Got blob:", blob.size, "bytes, type:", blob.type);
                
                if (blob && blob.size > 0) {
                    // Convert to base64 and send final data
                    const reader = new FileReader();
                    reader.onloadend = () => {
                        try {
                            const base64data = reader.result.split(',')[1];
                            if (base64data) {
                                console.log("Sending final audio chunk and recording_complete event");
                                socket.emit('audio_data', base64data);
                                
                                // Only emit recording_complete if not already emitted
                                if (!recordingCompleteEmitted) {
                                    recordingCompleteEmitted = true;
                                    socket.emit('recording_complete');
                                }
                            }
                        } catch (error) {
                            console.error('Error preparing final audio data:', error);
                            // Emit recording_complete even if there was an error
                            if (!recordingCompleteEmitted) {
                                recordingCompleteEmitted = true;
                                socket.emit('recording_complete');
                            }
                        }
                    };
                    
                    reader.onerror = () => {
                        console.error('Error reading audio blob');
                        // Emit recording_complete even if there was an error
                        if (!recordingCompleteEmitted) {
                            recordingCompleteEmitted = true;
                            socket.emit('recording_complete');
                        }
                    };
                    
                    reader.readAsDataURL(blob);
                } else {
                    console.warn("Empty or invalid audio blob");
                    // Emit recording_complete even if blob is invalid
                    if (!recordingCompleteEmitted) {
                        recordingCompleteEmitted = true;
                        socket.emit('recording_complete');
                    }
                }
            } catch (error) {
                console.error('Error processing recorded audio:', error);
                // Emit recording_complete even if there was an error
                if (!recordingCompleteEmitted) {
                    recordingCompleteEmitted = true;
                    socket.emit('recording_complete');
                }
            }
            
            // Clean up
            isRecording = false;
            
            // Ensure we stop all audio tracks
            if (audioStream) {
                audioStream.getTracks().forEach(track => {
                    console.log('Stopping track:', track.kind, track.id);
                    track.stop();
                });
                audioStream = null;
            }
            
            recorder = null;
            
            // Update UI
            updateUIState('processing_audio');
        });
    } catch (error) {
        console.error('Error stopping recording:', error);
        isRecording = false;
        
        // Make sure tracks are stopped even if there was an error
        if (audioStream) {
            audioStream.getTracks().forEach(track => track.stop());
            audioStream = null;
        }
        
        // Emit recording_complete even if there was an error
        if (!recordingCompleteEmitted) {
            recordingCompleteEmitted = true;
            socket.emit('recording_complete');
        }
        
        updateUIState('processing_audio');
    }
}

function updateRecordingTime() {
    const minutes = Math.floor(recordingSeconds / 60);
    const seconds = recordingSeconds % 60;
    const timeDisplay = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    
    // Update the recording time element if it exists
    const recordingTimeElement = document.getElementById('recording-time');
    if (recordingTimeElement) {
        recordingTimeElement.textContent = timeDisplay;
    }
    
    // Update the record button text if it exists
    if (manualTriggerBtn) {
        manualTriggerBtn.textContent = `Recording (${timeDisplay})`;
    }
}

function updateUIState(state) {
    currentState = state;
    const stateConfig = UIStateMap[state] || UIStateMap.ready;
    
    // Update status indicator
    statusDot.style.backgroundColor = stateConfig.statusColor;
    statusText.textContent = stateConfig.statusText;
    
    // Update progress bar
    progressBar.style.width = `${stateConfig.progressBar}%`;
    progressText.textContent = stateConfig.progressText;
    
    // Special handling for error state - preserve transcription section if it's visible
    if (state === 'error' && !transcriptionSection.classList.contains('hidden')) {
        // Only update the recording and video sections
        recordingSection.classList.toggle('hidden', !stateConfig.sections.recording);
        videoSection.classList.toggle('hidden', !stateConfig.sections.video);
        
        // Leave the transcription section as is (visible)
        console.log('Preserving transcription section in error state');
    } else {
        // Regular update for all sections
        recordingSection.classList.toggle('hidden', !stateConfig.sections.recording);
        transcriptionSection.classList.toggle('hidden', !stateConfig.sections.transcription);
        videoSection.classList.toggle('hidden', !stateConfig.sections.video);
    }
    
    // Update button text for manual trigger
    if (state === 'ready') {
        manualTriggerBtn.textContent = 'Start Recording';
        manualTriggerBtn.disabled = false;
    } else if (state === 'recording') {
        manualTriggerBtn.textContent = 'Stop Recording';
        manualTriggerBtn.disabled = false;
    } else {
        manualTriggerBtn.textContent = 'Processing...';
        manualTriggerBtn.disabled = true;
    }
    
    // Show reset button in certain states
    if (['video_ready', 'error'].includes(state)) {
        resetButton.classList.remove('hidden');
    } else {
        resetButton.classList.add('hidden');
    }
    
    // Add state class to body
    document.body.className = '';
    document.body.classList.add(`state-${state}`);
}

function loadVideo(videoPath) {
    try {
        console.log("[FIREFOX COMPATIBLE] Loading video:", videoPath);
        
        // Get the video URL
        const videoUrl = videoPath.startsWith('http') ? 
            videoPath : `${SERVER_URL}/videos/${videoPath.split('/').pop()}`;
        
        // Log the video URL for debugging
        console.log("[FIREFOX COMPATIBLE] Video URL:", videoUrl);
        
        // Try to create a direct URL with the video parameter
        const directVideoUrl = `${window.location.origin}${window.location.pathname}?video=${encodeURIComponent(videoUrl)}`;
        console.log("[FIREFOX COMPATIBLE] Direct video URL:", directVideoUrl);
        
        // Make a direct video element in the container
        const videoSection = document.getElementById('video-section');
        const videoContainer = document.querySelector('.video-container');
        
        if (videoContainer) {
            console.log("[FIREFOX COMPATIBLE] Found video container, creating player");
            
            // Clear the container
            videoContainer.innerHTML = '';
            
            // Create a simple video element
            const videoElement = document.createElement('video');
            videoElement.id = 'dream-video';
            videoElement.controls = true;
            videoElement.autoplay = true;
            videoElement.loop = true;
            videoElement.playsInline = true;
            
            // Set the source
            videoElement.src = videoUrl;
            
            // Add the video element to the container
            videoContainer.appendChild(videoElement);
            
            // Add a direct link as a fallback
            const fallbackLink = document.createElement('a');
            fallbackLink.href = videoUrl;
            fallbackLink.target = '_blank';
            fallbackLink.className = 'video-fallback';
            fallbackLink.textContent = 'Open Video Directly';
            fallbackLink.style.marginTop = '15px';
            fallbackLink.style.padding = '10px';
            fallbackLink.style.backgroundColor = '#3498db';
            fallbackLink.style.color = 'white';
            fallbackLink.style.borderRadius = '5px';
            fallbackLink.style.textDecoration = 'none';
            fallbackLink.style.display = 'inline-block';
            fallbackLink.style.fontWeight = 'bold';
            
            // Add some space
            videoContainer.appendChild(document.createElement('br'));
            videoContainer.appendChild(fallbackLink);
            
            // Add fallback message
            const fallbackMessage = document.createElement('div');
            fallbackMessage.textContent = 'If the video doesn\'t play, click the button above to open it in a new tab.';
            fallbackMessage.style.color = 'white';
            fallbackMessage.style.padding = '15px';
            fallbackMessage.style.marginTop = '15px';
            fallbackMessage.style.fontSize = '14px';
            fallbackMessage.style.textAlign = 'center';
            videoContainer.appendChild(fallbackMessage);
            
            // Show notification
            showNotification('Dream video is ready. If it doesn\'t play automatically, click the button below the video.', 'success');
            
            // Make the section visible
            if (videoSection) {
                videoSection.classList.remove('hidden');
            }
            
            // Update UI state without relying on complex processing
            statusDot.style.backgroundColor = '#4caf50';
            statusText.textContent = 'Complete';
            progressBar.style.width = '100%';
            progressText.textContent = 'Your dream visualization is ready';
            
            // Show reset button
            resetButton.classList.remove('hidden');
            
            // Update state without triggering events
            currentState = 'video_ready';
            
            // Force the body state class
            document.body.className = '';
            document.body.classList.add('state-video_ready');
            
            // Update sections visibility directly
            recordingSection.classList.add('hidden');
            transcriptionSection.classList.remove('hidden');
            videoSection.classList.remove('hidden');
            
            // Try to play the video directly
            try {
                videoElement.play().catch(e => {
                    console.warn("[FIREFOX COMPATIBLE] Auto-play was prevented:", e);
                });
            } catch (e) {
                console.warn("[FIREFOX COMPATIBLE] Error playing video:", e);
            }
            
            // Set in global state - do this after all other operations
            dreamVideo = videoElement;
            
            return true;
        } else {
            console.error("[FIREFOX COMPATIBLE] Video container not found");
            showNotification('Error: Video container not found', 'error');
            return false;
        }
    } catch (err) {
        console.error("[FIREFOX COMPATIBLE] Error in loadVideo:", err);
        showNotification(`Error loading video: ${err.message}`, 'error');
        return false;
    }
}

function resetApplication() {
    // Add confirmation for reset when transcription is visible
    if (!transcriptionSection.classList.contains('hidden')) {
        const confirmReset = confirm('Reset will clear your transcription and enhanced prompt. Continue?');
        if (!confirmReset) {
            return;
        }
    }
    
    // Stop any ongoing recording
    if (isRecording) {
        stopRecording();
    }
    
    // Reset UI
    updateUIState('ready');
    transcriptionText.textContent = '';
    enhancedPromptText.textContent = '';
    recordingTime.textContent = '00:00';
    
    // Thoroughly reset the video player for Firefox compatibility
    try {
        const videoContainer = document.querySelector('.video-container');
        if (videoContainer) {
            // First find and stop any playing videos
            const videoElements = videoContainer.querySelectorAll('video');
            videoElements.forEach(video => {
                console.log('Stopping video playback');
                try {
                    video.pause();
                    video.removeAttribute('src');
                    video.load();
                } catch (e) {
                    console.warn('Error while stopping video:', e);
                }
            });
            
            // Clear the container completely
            videoContainer.innerHTML = '';
            console.log('Video container cleared');
        }
        
        // Reset the global video reference
        dreamVideo = null;
        
        // Hide the video section
        videoSection.classList.add('hidden');
    } catch (e) {
        console.error('Error resetting video player:', e);
    }
    
    // Reset flags
    enhancedPromptReceived = false;
    
    // Reset styles
    const transcriptionContainer = document.getElementById('transcription-container');
    const enhancedPromptContainer = document.getElementById('enhanced-prompt-container');
    if (transcriptionContainer) transcriptionContainer.classList.remove('loaded');
    if (enhancedPromptContainer) enhancedPromptContainer.classList.remove('loaded');
    
    // Clear session storage
    try {
        sessionStorage.removeItem('lastTranscription');
        sessionStorage.removeItem('lastEnhancedPrompt');
        console.log('Cleared transcription and enhanced prompt from session storage');
    } catch (e) {
        console.warn('Could not clear session storage:', e);
    }
    
    // Emit reset event to server
    socket.emit('manual_trigger', { action: 'reset' });
    
    // Show notification
    showNotification('Application reset complete', 'info');
}

// Audio visualizer functions
function startVisualizer(stream) {
    const audioVisualizer = document.getElementById('visualizer');
    
    if (!audioVisualizer || !audioContext) return;
    
    const canvasCtx = audioVisualizer.getContext('2d');
    const source = audioContext.createMediaStreamSource(stream);
    const analyser = audioContext.createAnalyser();
    
    analyser.fftSize = 256;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    
    source.connect(analyser);
    
    function draw() {
        if (!isRecording) return;
        
        requestAnimationFrame(draw);
        
        const width = audioVisualizer.width = audioVisualizer.clientWidth;
        const height = audioVisualizer.height = audioVisualizer.clientHeight;
        
        canvasCtx.clearRect(0, 0, width, height);
        analyser.getByteFrequencyData(dataArray);
        
        canvasCtx.fillStyle = 'rgba(0, 0, 0, 0)';
        canvasCtx.fillRect(0, 0, width, height);
        
        const barWidth = (width / bufferLength) * 2.5;
        let x = 0;
        
        for (let i = 0; i < bufferLength; i++) {
            const barHeight = (dataArray[i] / 255) * height;
            
            canvasCtx.fillStyle = `rgba(255, 64, 129, ${barHeight / height})`;
            canvasCtx.fillRect(x, height - barHeight, barWidth, barHeight);
            
            x += barWidth + 1;
        }
    }
    
    draw();
}

function stopVisualizer() {
    // Set isRecording to false to ensure animation loop stops
    isRecording = false;
    
    // Clear canvas
    const audioVisualizer = document.getElementById('visualizer');
    if (audioVisualizer) {
        const canvasCtx = audioVisualizer.getContext('2d');
        canvasCtx.clearRect(0, 0, audioVisualizer.width, audioVisualizer.height);
    }
}

// Notification function
function showNotification(message, type = 'info') {
    console.log(`Showing notification: ${message} (${type})`);
    
    // Create notification element if it doesn't exist
    let notification = document.getElementById('notification');
    if (!notification) {
        notification = document.createElement('div');
        notification.id = 'notification';
        notification.className = 'notification';
        document.body.appendChild(notification);
        
        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 12px 20px;
                border-radius: 4px;
                color: white;
                font-size: 14px;
                z-index: 9999;
                transition: all 0.3s ease;
                opacity: 0;
                transform: translateY(-20px);
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
                max-width: 80%;
                word-wrap: break-word;
            }
            .notification.show {
                opacity: 1;
                transform: translateY(0);
            }
            .notification.info {
                background-color: #2196F3;
            }
            .notification.success {
                background-color: #4CAF50;
            }
            .notification.warning {
                background-color: #FF9800;
            }
            .notification.error {
                background-color: #F44336;
            }
        `;
        document.head.appendChild(style);
    }
    
    // Clear any existing timeout
    if (notification.timeoutId) {
        clearTimeout(notification.timeoutId);
        notification.timeoutId = null;
    }
    
    // Update notification content and style
    notification.textContent = message;
    notification.className = `notification ${type}`;
    
    // Show notification
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Hide notification after 7 seconds
    notification.timeoutId = setTimeout(() => {
        notification.classList.remove('show');
    }, 7000);
    
    // Add click handler to dismiss notification
    notification.onclick = function() {
        notification.classList.remove('show');
        if (notification.timeoutId) {
            clearTimeout(notification.timeoutId);
            notification.timeoutId = null;
        }
    };
}

// Function to show a notification or message to the user
function showMessage(message, type = 'info') {
    console.log(`Message (${type}): ${message}`);
    
    // Check if we have a notification element
    const notificationElement = document.getElementById('notification');
    if (notificationElement) {
        notificationElement.textContent = message;
        notificationElement.className = `notification ${type}`;
        notificationElement.style.display = 'block';
        
        // Hide after 5 seconds
        setTimeout(() => {
            notificationElement.style.display = 'none';
        }, 5000);
    } else {
        // Fallback to alert for critical messages
        if (type === 'error') {
            alert(message);
        }
    }
}

// Add styles for the new transcription cards
document.addEventListener('DOMContentLoaded', function() {
    const style = document.createElement('style');
    style.textContent = `
        .transcription-card {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }
        
        .transcription-card h3 {
            margin-top: 0;
            color: #333;
            font-size: 18px;
            font-weight: 500;
            margin-bottom: 10px;
        }
        
        #transcription-container, #enhanced-prompt-container {
            opacity: 0.7;
            transition: opacity 0.3s ease;
            padding: 10px;
            border-radius: 4px;
        }
        
        #transcription-container.loaded, #enhanced-prompt-container.loaded {
            opacity: 1;
            background-color: #fff;
            border: 1px solid #e0e0e0;
        }
        
        #transcription-text, #enhanced-prompt-text {
            line-height: 1.6;
            color: #333;
            min-height: 20px;
        }
        
        #enhanced-prompt-text {
            white-space: pre-line;
            background-color: #f0f8ff;
            border: 1px solid #cce5ff;
            padding: 12px;
            border-radius: 4px;
        }
    `;
    document.head.appendChild(style);
    
    // Add additional initialization to ensure all elements are found
    console.log("DOM Content Loaded - checking key elements");
    console.log("transcriptionText element:", transcriptionText);
    console.log("enhancedPromptText element:", enhancedPromptText);
    console.log("transcriptionSection element:", transcriptionSection);
    
    // Add double-click handler to manually test setting the enhanced prompt
    const enhancedPromptContainer = document.getElementById('enhanced-prompt-container');
    if (enhancedPromptContainer) {
        enhancedPromptContainer.addEventListener('dblclick', function() {
            console.log("Double-click on enhanced prompt container detected");
            const testPrompt = "This is a test enhanced prompt.\nIt should be visible with proper formatting.\nLine breaks should work too.";
            
            if (enhancedPromptText) {
                enhancedPromptText.textContent = testPrompt;
                enhancedPromptReceived = true;
                enhancedPromptContainer.classList.add('loaded');
                transcriptionSection.classList.remove('hidden');
                console.log("Manually set enhanced prompt text for testing");
                
                try {
                    sessionStorage.setItem('lastEnhancedPrompt', testPrompt);
                } catch (e) {
                    console.warn('Could not store test prompt in session storage', e);
                }
                
                showNotification('Test prompt set manually', 'info');
            }
        });
    }
});

// Add a global function to manually display the enhanced prompt for debugging
window.forceDisplayEnhancedPrompt = function(text) {
    console.log("forceDisplayEnhancedPrompt called with:", text);
    const promptText = text || "Forced enhanced prompt test.\nThis is a manually triggered display.";
    
    if (enhancedPromptText) {
        enhancedPromptText.textContent = promptText;
        enhancedPromptReceived = true;
        
        const enhancedPromptContainer = document.getElementById('enhanced-prompt-container');
        if (enhancedPromptContainer) {
            enhancedPromptContainer.classList.add('loaded');
        }
        
        transcriptionSection.classList.remove('hidden');
        console.log("Manually forced enhanced prompt display");
        showNotification('Enhanced prompt displayed manually', 'success');
    } else {
        console.error("enhancedPromptText element not found");
        showNotification('Could not display enhanced prompt - element not found', 'error');
    }
};

// NEW: Function to recover enhanced prompt from server logs
window.recoverEnhancedPromptFromLogs = function(logLine) {
    try {
        if (!logLine || typeof logLine !== 'string') {
            console.error("Please provide the server log line containing the enhanced prompt");
            showNotification('Please provide the server log line', 'error');
            return;
        }
        
        // Extract the enhanced prompt from the log line
        // Format is usually: "- __main__ - INFO - Enhanced prompt: Begin with a wide..."
        const match = logLine.match(/Enhanced prompt: (.*?)($|(\d{4}-\d{2}-\d{2}))/s);
        if (!match) {
            console.error("Could not extract enhanced prompt from the provided log line");
            showNotification('Could not extract enhanced prompt from log', 'error');
            return;
        }
        
        // Get the extracted text and clean it up
        let extractedPrompt = match[1].trim();
        
        // Remove any trailing timestamps or log entries
        extractedPrompt = extractedPrompt.replace(/\d{4}-\d{2}-\d{2}.*$/, '').trim();
        
        // Display the extracted prompt
        console.log("Extracted enhanced prompt:", extractedPrompt);
        forceDisplayEnhancedPrompt(extractedPrompt);
        
        return extractedPrompt;
    } catch (err) {
        console.error("Error recovering enhanced prompt:", err);
        showNotification('Error recovering enhanced prompt', 'error');
    }
};

// NEW: Add a DOM inspector function to diagnose the enhanced prompt elements
window.inspectEnhancedPromptElements = function() {
    console.group("DOM INSPECTOR: Enhanced Prompt Elements");
    
    // Check if element exists
    const enhancedPromptText = document.getElementById('enhanced-prompt-text');
    console.log("Enhanced prompt text element exists:", enhancedPromptText !== null);
    
    if (enhancedPromptText) {
        // Check content
        console.log("Text content:", enhancedPromptText.textContent);
        console.log("Inner HTML:", enhancedPromptText.innerHTML);
        
        // Check styling
        const computedStyle = window.getComputedStyle(enhancedPromptText);
        console.log("Computed styles:", {
            display: computedStyle.display,
            visibility: computedStyle.visibility,
            height: computedStyle.height,
            opacity: computedStyle.opacity,
            whiteSpace: computedStyle.whiteSpace,
            overflow: computedStyle.overflow
        });
        
        // Check parent container
        const container = document.getElementById('enhanced-prompt-container');
        console.log("Container exists:", container !== null);
        if (container) {
            console.log("Container classes:", container.className);
            console.log("Container is visible:", !container.classList.contains('hidden'));
            
            const containerStyle = window.getComputedStyle(container);
            console.log("Container computed styles:", {
                display: containerStyle.display,
                visibility: containerStyle.visibility,
                height: containerStyle.height,
                opacity: containerStyle.opacity
            });
        }
        
        // Check section visibility
        const transcriptionSection = document.getElementById('transcription-section');
        console.log("Transcription section exists:", transcriptionSection !== null);
        if (transcriptionSection) {
            console.log("Transcription section classes:", transcriptionSection.className);
            console.log("Transcription section is visible:", !transcriptionSection.classList.contains('hidden'));
        }
    }
    
    // Check session storage
    try {
        const storedPrompt = sessionStorage.getItem('lastEnhancedPrompt');
        console.log("Enhanced prompt in session storage:", storedPrompt ? "Yes (length: " + storedPrompt.length + ")" : "No");
    } catch (e) {
        console.warn("Error checking session storage:", e);
    }
    
    console.groupEnd();
    
    return "Inspection complete - check console for details";
};

// NEW: Function to extract and display enhanced prompt from raw socket message
window.displayFromSocketMessage = function(socketMessage) {
    try {
        console.log("Attempting to extract enhanced prompt from raw socket message:", socketMessage);
        
        // Try to parse the socket message format: 42["enhanced_prompt",{"text":"..."}]
        // First, strip any leading/trailing whitespace
        const cleanMessage = socketMessage.trim();
        
        // Extract the JSON part (everything after the event name)
        const match = cleanMessage.match(/42\["enhanced_prompt",(.+)\]$/);
        if (!match) {
            console.error("Couldn't match the socket message format");
            showNotification("Couldn't extract prompt from socket message", "error");
            return false;
        }
        
        // Parse the JSON payload
        const jsonString = match[1];
        const payload = JSON.parse(jsonString);
        
        if (payload && payload.text) {
            console.log("Successfully extracted enhanced prompt:", payload.text);
            forceDisplayEnhancedPrompt(payload.text);
            return true;
        } else {
            console.error("Extracted payload doesn't contain a text field:", payload);
            showNotification("No text found in the socket message", "error");
            return false;
        }
    } catch (err) {
        console.error("Error parsing socket message:", err);
        showNotification("Error extracting prompt from socket message", "error");
        return false;
    }
};

// Auto-run the inspector after page load
document.addEventListener('DOMContentLoaded', function() {
    // Add styles for the new transcription cards
    const style = document.createElement('style');
    style.textContent = `
        .transcription-card {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }
        
        .transcription-card h3 {
            margin-top: 0;
            color: #333;
            font-size: 18px;
            font-weight: 500;
            margin-bottom: 10px;
        }
        
        #transcription-container, #enhanced-prompt-container {
            opacity: 0.7;
            transition: opacity 0.3s ease;
            padding: 10px;
            border-radius: 4px;
        }
        
        #transcription-container.loaded, #enhanced-prompt-container.loaded {
            opacity: 1;
            background-color: #fff;
            border: 1px solid #e0e0e0;
        }
        
        #transcription-text, #enhanced-prompt-text {
            line-height: 1.6;
            color: #333;
            min-height: 20px;
        }
        
        #enhanced-prompt-text {
            white-space: pre-line;
            background-color: #f0f8ff;
            border: 1px solid #cce5ff;
            padding: 12px;
            border-radius: 4px;
        }
    `;
    document.head.appendChild(style);
    
    // Add additional initialization to ensure all elements are found
    console.log("DOM Content Loaded - checking key elements");
    console.log("transcriptionText element:", transcriptionText);
    console.log("enhancedPromptText element:", enhancedPromptText);
    console.log("transcriptionSection element:", transcriptionSection);
    
    // Add double-click handler to manually test setting the enhanced prompt
    const enhancedPromptContainer = document.getElementById('enhanced-prompt-container');
    if (enhancedPromptContainer) {
        enhancedPromptContainer.addEventListener('dblclick', function() {
            console.log("Double-click on enhanced prompt container detected");
            const testPrompt = "This is a test enhanced prompt.\nIt should be visible with proper formatting.\nLine breaks should work too.";
            
            if (enhancedPromptText) {
                enhancedPromptText.textContent = testPrompt;
                enhancedPromptReceived = true;
                enhancedPromptContainer.classList.add('loaded');
                transcriptionSection.classList.remove('hidden');
                console.log("Manually set enhanced prompt text for testing");
                
                try {
                    sessionStorage.setItem('lastEnhancedPrompt', testPrompt);
                } catch (e) {
                    console.warn('Could not store test prompt in session storage', e);
                }
                
                showNotification('Test prompt set manually', 'info');
            }
        });
    }
    
    // Run the DOM inspector on page load
    setTimeout(() => {
        window.inspectEnhancedPromptElements();
    }, 1000);
});