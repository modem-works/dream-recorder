// State manager for Dream Recorder
const StateManager = {
    // Possible states
    STATES: {
        IDLE: 'idle',
        RECORDING: 'recording',
        PROCESSING: 'processing',
        PLAYBACK: 'playback',
        ERROR: 'error'
    },

    // Input modes (kept for input simulator compatibility)
    MODES: {
        TAP_AND_HOLD: 'tap_and_hold',
        SINGLE_TAP: 'single_tap',
        DOUBLE_TAP: 'double_tap',
        TRIPLE_TAP: 'triple_tap'
    },

    // Current state and mode
    currentState: 'idle',
    currentMode: 'tap_and_hold', // Default to TAP_AND_HOLD
    error: null,
    previousState: null,
    stateChangeCallbacks: [],
    playbackTimer: null,
    playbackDuration: 120, // Default value, will be updated from config

    // Initialize state manager
    async init() {
        try {
            const response = await fetch('/api/config');
            const config = await response.json();
            this.playbackDuration = config.playback_duration;
        } catch (error) {
            console.error('Failed to fetch config:', error);
        }
        this.updateState(this.STATES.IDLE);
        this.updateStatus();
        console.log('State Manager initialized');
    },

    // Update state
    updateState(newState, errorMessage = null) {
        // Clear any existing playback timer
        if (this.playbackTimer) {
            clearTimeout(this.playbackTimer);
            this.playbackTimer = null;
        }

        this.previousState = this.currentState;
        this.currentState = newState;
        this.error = errorMessage;
        this.updateStatus();
        
        // Handle icon animations based on state
        if (this.currentState === this.STATES.RECORDING) {
            IconAnimations.show(IconAnimations.TYPES.RECORDING);
        } else if (this.currentState === this.STATES.PROCESSING) {
            IconAnimations.show(IconAnimations.TYPES.GENERATING);
        } else if (this.currentState === this.STATES.ERROR) {
            IconAnimations.show(IconAnimations.TYPES.ERROR);
        } else {
            // Hide icons for all other states (IDLE, PLAYBACK, etc.)
            IconAnimations.hideAll();
        }
        
        // Set up playback timer if entering playback state
        if (this.currentState === this.STATES.PLAYBACK) {
            this.playbackTimer = setTimeout(() => {
                this.goToIdle();
            }, this.playbackDuration * 1000); // Convert to milliseconds
        }
        
        // Notify all registered callbacks
        this.stateChangeCallbacks.forEach(callback => callback(this.currentState, this.previousState));
        
        // Emit state change event
        const event = new CustomEvent('stateChange', { 
            detail: { 
                state: this.currentState, 
                error: this.error,
                mode: this.currentMode
            } 
        });
        document.dispatchEvent(event);
    },

    // Update the status display
    updateStatus() {
        const statusDiv = document.getElementById('status');
        if (!statusDiv) return;
        let statusText = `${this.currentState.charAt(0).toUpperCase() + this.currentState.slice(1)}`;
        
        if (this.currentState === this.STATES.ERROR && this.error) {
            statusText += ` - ${this.error}`;
        }
        
        statusDiv.textContent = statusText;
    },

    // Go to idle state
    goToIdle() {
        // Hide video if it's playing
        if (this.currentState === this.STATES.PLAYBACK) {
            const videoContainer = document.getElementById('videoContainer');
            if (videoContainer) {
                videoContainer.style.display = 'none';
            }
        }
        
        this.updateState(this.STATES.IDLE);
    },

    // Play latest video
    playLatestVideo() {
        console.log('Playing latest video');
        // Request the latest video from server
        if (window.socket) {
            window.socket.emit('show_previous_dream');
            this.updateState(this.STATES.PLAYBACK);
        }
    },

    // Play previous video
    playPreviousVideo() {
        console.log('Playing previous video');
        // Request the previous video from server
        if (window.socket) {
            window.socket.emit('show_previous_dream');
            this.updateState(this.STATES.PLAYBACK);
        }
    },

    // Handle recording start
    startRecording() {
        if (this.currentState === this.STATES.RECORDING) {
            console.log(`Already recording`);
            return;
        }

        // If in playback, hide video first
        if (this.currentState === this.STATES.PLAYBACK) {
            const videoContainer = document.getElementById('videoContainer');
            if (videoContainer) {
                videoContainer.style.display = 'none';
            }
        }

        this.updateState(this.STATES.RECORDING);
        
        if (window.startRecording) {
            window.startRecording();
        }
    },

    // Handle recording stop
    stopRecording() {
        if (this.currentState !== this.STATES.RECORDING) {
            console.log(`Cannot stop recording in ${this.currentState} state`);
            return;
        }

        this.updateState(this.STATES.PROCESSING);
        
        if (window.stopRecording) {
            window.stopRecording();
        }
    },

    // Handle device events based on mode
    handleDeviceEvent(eventType) {
        console.log(`Handling device event: ${eventType}`);
        
        switch (eventType) {
            case 'tap':
                if (this.currentState === this.STATES.PLAYBACK || 
                    this.currentState === this.STATES.ERROR) {
                    this.goToIdle();
                } else if (this.currentState === this.STATES.RECORDING) {
                    this.stopRecording();
                }
                break;
                
            case 'double_tap':
                if (this.currentState === this.STATES.IDLE || 
                    this.currentState === this.STATES.ERROR) {
                    this.playLatestVideo();
                } else if (this.currentState === this.STATES.PLAYBACK) {
                    this.playPreviousVideo();
                }
                break;
                
            case 'triple_tap':
                // For now, do nothing at all
                console.log('Triple tap - no action assigned');
                break;
                
            case 'hold_start':
                if (this.currentState === this.STATES.IDLE ||
                    this.currentState === this.STATES.PLAYBACK) {
                    this.startRecording();
                }
                break;
                
            case 'hold_release':
                if (this.currentState === this.STATES.RECORDING) {
                    this.stopRecording();
                }
                break;
                
            default:
                console.log(`Unhandled event type: ${eventType}`);
        }
    },

    // Register a callback for state changes
    registerStateChangeCallback(callback) {
        this.stateChangeCallbacks.push(callback);
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    StateManager.init();
});

// Make StateManager globally accessible
window.StateManager = StateManager; 