// State manager for Dream Recorder
const StateManager = {
    // Possible states
    STATES: {
        IDLE: 'idle',
        RECORDING: 'recording',
        PROCESSING: 'processing',
        PLAYBACK: 'playback',
        ERROR: 'error',
        CLOCK: 'clock'
    },

    // Input modes (kept for input simulator compatibility)
    MODES: {
        TAP_AND_HOLD: 'tap_and_hold',
        SINGLE_TAP: 'single_tap',
        DOUBLE_TAP: 'double_tap',
    },

    // Current state and mode
    currentState: 'idle',
    currentMode: 'tap_and_hold', // Default to TAP_AND_HOLD
    error: null,
    previousState: null,
    stateChangeCallbacks: [],
    playbackTimer: null,
    idleTimer: null,
    playbackDuration: 120, // Default value, will be updated from config
    idleTimeout: 30, // Default value, will be updated from config

    // Initialize state manager
    async init() {
        try {
            const response = await fetch('/api/config');
            const config = await response.json();
            this.playbackDuration = config.playback_duration;
            this.idleTimeout = config.idle_timeout;
        } catch (error) {
            console.error('Failed to fetch config:', error);
        }
        this.updateState(this.STATES.IDLE);
        this.updateStatus();
        console.log('State Manager initialized');
    },

    // Update state
    updateState(newState, errorMessage = null) {
        // Clear any existing timers
        if (this.playbackTimer) {
            clearTimeout(this.playbackTimer);
            this.playbackTimer = null;
        }
        if (this.idleTimer) {
            clearTimeout(this.idleTimer);
            this.idleTimer = null;
        }

        // Stop clock if transitioning from clock state
        if (this.currentState === this.STATES.CLOCK && newState !== this.STATES.CLOCK) {
            this.stopClock();
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
        
        // Set up idle timer if entering idle state
        if (this.currentState === this.STATES.IDLE) {
            this.idleTimer = setTimeout(() => {
                this.goToClock();
            }, this.idleTimeout * 1000); // Convert to milliseconds
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
        
        // Hide clock if it's showing
        if (this.currentState === this.STATES.CLOCK) {
            const clockDisplay = document.getElementById('clockDisplay');
            if (clockDisplay) {
                clockDisplay.style.display = 'none';
            }
        }
        
        this.updateState(this.STATES.IDLE);
    },

    // Stop the clock
    stopClock() {
        const clockDisplay = document.getElementById('clockDisplay');
        if (clockDisplay) {
            clockDisplay.style.display = 'none';
        }
        // Don't call cleanup() here as we want the clock to keep running
    },

    // Go to clock state
    goToClock() {
        const clockDisplay = document.getElementById('clockDisplay');
        if (clockDisplay) {
            clockDisplay.style.display = 'block';
        }
        this.updateState(this.STATES.CLOCK);
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
        
        // Reset idle timer on any user interaction
        if (this.idleTimer) {
            clearTimeout(this.idleTimer);
            this.idleTimer = null;
        }
        
        // Set up new idle timer if we're in idle state
        if (this.currentState === this.STATES.IDLE) {
            this.idleTimer = setTimeout(() => {
                this.goToClock();
            }, this.idleTimeout * 1000);
        }
        
        switch (eventType) {
            case 'tap':
                if (this.currentState === this.STATES.PLAYBACK || 
                    this.currentState === this.STATES.ERROR) {
                    this.goToIdle();
                } else if (this.currentState === this.STATES.RECORDING) {
                    this.stopRecording();
                } else if (this.currentState === this.STATES.IDLE) {
                    this.goToClock();
                } else if (this.currentState === this.STATES.CLOCK) {
                    this.goToIdle();
                }
                break;
                
            case 'double_tap':
                if (this.currentState === this.STATES.IDLE || 
                    this.currentState === this.STATES.ERROR ||
                    this.currentState === this.STATES.CLOCK) {
                    this.playLatestVideo();
                } else if (this.currentState === this.STATES.PLAYBACK) {
                    this.playPreviousVideo();
                }
                break;
                
            case 'hold_start':
                if (this.currentState === this.STATES.IDLE ||
                    this.currentState === this.STATES.PLAYBACK ||
                    this.currentState === this.STATES.CLOCK) {
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