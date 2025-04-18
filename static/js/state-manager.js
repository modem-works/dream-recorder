// State manager for Dream Recorder
const StateManager = {
    // Possible states
    STATES: {
        STARTUP: 'startup',
        CLOCK: 'clock',
        RECORDING: 'recording',
        PROCESSING: 'processing',
        PLAYBACK: 'playback',
        ERROR: 'error'
    },

    // Configuration
    config: {
        logoFadeInDuration: 1000,    // 1 second
        logoDisplayDuration: 2000,    // 2 seconds
        logoFadeOutDuration: 1000,    // 1 second
        clockFadeDuration: 500,       // 0.5 seconds
        transitionDelay: 500          // 0.5 seconds
    },

    // Input modes (kept for input simulator compatibility)
    MODES: {
        TAP_AND_HOLD: 'tap_and_hold',
        SINGLE_TAP: 'single_tap',
        DOUBLE_TAP: 'double_tap',
    },

    // Current state and mode
    currentState: 'startup',
    currentMode: 'tap_and_hold', // Default to TAP_AND_HOLD
    error: null,
    previousState: null,
    stateChangeCallbacks: [],
    playbackTimer: null,
    playbackDuration: 120, // Default value, will be updated from config

    // Initialize state manager
    async init() {
        console.log(`[${new Date().toISOString()}] StateManager.init() called`);
        try {
            const response = await fetch('/api/config');
            const config = await response.json();
            this.playbackDuration = config.playback_duration;
            console.log(`[${new Date().toISOString()}] Config loaded:`, config);
        } catch (error) {
            console.error('Failed to fetch config:', error);
        }

        // Set initial state to STARTUP
        console.log(`[${new Date().toISOString()}] Setting initial state to STARTUP`);
        this.currentState = this.STATES.STARTUP;
        this.updateStatus();

        // Start the startup sequence
        console.log(`[${new Date().toISOString()}] Starting startup sequence`);
        this.startStartupSequence();
    },

    // Handle startup sequence
    startStartupSequence() {
        console.log(`[${new Date().toISOString()}] startStartupSequence() called`);
        const logo = document.querySelector('.startup-logo');
        const clockDisplay = document.getElementById('clockDisplay');
        if (!logo || !clockDisplay) {
            console.error('Startup elements not found');
            this.updateState(this.STATES.CLOCK);
            return;
        }

        console.log(`[${new Date().toISOString()}] Hiding clock display`);
        // Ensure clock is hidden
        clockDisplay.style.display = 'none';
        clockDisplay.style.opacity = '0';

        console.log(`[${new Date().toISOString()}] Resetting logo styles`);
        // Reset logo styles
        logo.style.opacity = '0';
        logo.style.display = 'block';
        logo.style.transition = 'none';
        
        // Force a reflow to ensure styles are applied
        logo.offsetHeight;
        
        // Start the sequence
        console.log(`[${new Date().toISOString()}] Starting logo fade in`);
        this.fadeInLogo(logo);
    },

    // Fade in the logo
    fadeInLogo(logo) {
        console.log(`[${new Date().toISOString()}] fadeInLogo() called`);
        // Set up transition for fade in
        logo.style.transition = `opacity ${this.config.logoFadeInDuration}ms ease-out`;
        logo.style.opacity = '1';

        // After fade in, wait and then fade out
        console.log(`[${new Date().toISOString()}] Scheduling fade out in ${this.config.logoFadeInDuration + this.config.logoDisplayDuration}ms`);
        setTimeout(() => {
            console.log(`[${new Date().toISOString()}] Starting logo fade out`);
            this.fadeOutLogo(logo);
        }, this.config.logoFadeInDuration + this.config.logoDisplayDuration);
    },

    // Fade out the logo
    fadeOutLogo(logo) {
        console.log(`[${new Date().toISOString()}] fadeOutLogo() called`);
        // Set up transition for fade out
        logo.style.transition = `opacity ${this.config.logoFadeOutDuration}ms ease-out`;
        logo.style.opacity = '0';

        // After fade out completes, transition to CLOCK state
        console.log(`[${new Date().toISOString()}] Scheduling CLOCK state transition in ${this.config.logoFadeOutDuration}ms`);
        setTimeout(() => {
            console.log(`[${new Date().toISOString()}] Transitioning to CLOCK state`);
            logo.style.display = 'none';
            this.updateState(this.STATES.CLOCK);
        }, this.config.logoFadeOutDuration);
    },

    // Update state
    updateState(newState, errorMessage = null) {
        console.log(`[${new Date().toISOString()}] updateState() called - Current: ${this.currentState}, New: ${newState}`);
        
        // Don't allow state changes during startup sequence
        if (this.currentState === this.STATES.STARTUP && newState !== this.STATES.CLOCK) {
            console.log(`[${new Date().toISOString()}] Ignoring state change during startup sequence`);
            return;
        }

        // Clear any existing timers
        if (this.playbackTimer) {
            clearTimeout(this.playbackTimer);
            this.playbackTimer = null;
        }

        // Handle transitions
        console.log(`[${new Date().toISOString()}] Handling state transition`);
        this.handleStateTransition(newState);

        this.previousState = this.currentState;
        this.currentState = newState;
        this.error = errorMessage;
        this.updateStatus();
        
        console.log(`[${new Date().toISOString()}] State updated to ${this.currentState}`);
        
        // Handle icon animations based on state
        if (this.currentState === this.STATES.RECORDING) {
            IconAnimations.show(IconAnimations.TYPES.RECORDING);
        } else if (this.currentState === this.STATES.PROCESSING) {
            IconAnimations.show(IconAnimations.TYPES.GENERATING);
        } else if (this.currentState === this.STATES.ERROR) {
            IconAnimations.show(IconAnimations.TYPES.ERROR);
        } else {
            // Hide icons for all other states (STARTUP, CLOCK, PLAYBACK, etc.)
            IconAnimations.hideAll();
        }
        
        // Set up playback timer if entering playback state
        if (this.currentState === this.STATES.PLAYBACK) {
            this.playbackTimer = setTimeout(() => {
                this.updateState(this.STATES.CLOCK);
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

    // Handle state transitions
    handleStateTransition(newState) {
        const clockDisplay = document.getElementById('clockDisplay');
        const videoContainer = document.getElementById('videoContainer');
        const video = document.getElementById('generatedVideo');

        // Handle video container
        if (videoContainer) {
            if (newState === this.STATES.PLAYBACK) {
                // Show video container
                videoContainer.style.display = 'block';
                
                // Force a reflow to ensure transition works
                videoContainer.offsetHeight;
                
                // Fade in video container
                videoContainer.style.opacity = '1';
                
                // After container is visible, fade in video
                setTimeout(() => {
                    if (video) {
                        video.style.opacity = '1';
                        if (video.paused) {
                            video.play().catch(error => console.error('Error playing video:', error));
                        }
                    }
                }, 100); // Small delay to ensure container is visible first
            } else if (this.currentState === this.STATES.PLAYBACK) {
                // Fade out video first
                if (video) {
                    video.style.opacity = '0';
                }
                
                // Then fade out container
                videoContainer.style.opacity = '0';
                setTimeout(() => {
                    if (this.currentState !== this.STATES.PLAYBACK) {
                        videoContainer.style.display = 'none';
                        if (video) {
                            video.pause();
                            video.currentTime = 0;
                        }
                    }
                }, this.config.clockFadeDuration);
            }
        }

        // Handle clock display
        if (clockDisplay) {
            if (newState === this.STATES.CLOCK) {
                // Fade in clock
                clockDisplay.style.transition = `opacity ${this.config.clockFadeDuration}ms ease-out`;
                clockDisplay.style.display = 'block';
                // Force reflow
                clockDisplay.offsetHeight;
                clockDisplay.style.opacity = '1';
                clockDisplay.style.zIndex = '10'; // Below video when playing

                // Initialize clock if needed
                if (window.Clock && !window.Clock.clockInterval) {
                    window.Clock.init();
                }
            } else if (this.currentState === this.STATES.CLOCK) {
                // Fade out clock
                clockDisplay.style.transition = `opacity ${this.config.clockFadeDuration}ms ease-out`;
                clockDisplay.style.opacity = '0';
                setTimeout(() => {
                    if (this.currentState !== this.STATES.CLOCK) {
                        clockDisplay.style.display = 'none';
                    }
                }, this.config.clockFadeDuration);
            }
        }
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
                    this.updateState(this.STATES.CLOCK);
                } else if (this.currentState === this.STATES.RECORDING) {
                    this.stopRecording();
                } else if (this.currentState === this.STATES.CLOCK) {
                    this.updateState(this.STATES.CLOCK);
                }
                break;
                
            case 'double_tap':
                if (this.currentState === this.STATES.ERROR ||
                    this.currentState === this.STATES.CLOCK) {
                    this.playLatestVideo();
                } else if (this.currentState === this.STATES.PLAYBACK) {
                    this.playPreviousVideo();
                }
                break;
                
            case 'hold_start':
                if (this.currentState === this.STATES.PLAYBACK ||
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