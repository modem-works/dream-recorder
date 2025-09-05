// Make socket and DOM elements available globally
window.socket = io();
window.statusDiv = document.getElementById('status');
window.messageDiv = document.getElementById('message');
window.transcriptionDiv = document.getElementById('transcription');
window.videoPromptDiv = document.getElementById('videoPrompt');
window.loadingDiv = document.getElementById('loading');
window.videoContainer = document.getElementById('videoContainer');
window.generatedVideo = document.getElementById('generatedVideo');
window.generatedVideo2 = document.getElementById('generatedVideo2');
window.videoPrompt = document.getElementById('videoPrompt');

// Initialize video players
window.generatedVideo.loop = true;
window.generatedVideo2.loop = true;

// Ensure initial state is correct
window.generatedVideo.style.opacity = '1';
window.generatedVideo2.style.opacity = '0';
window.generatedVideo.classList.add('video-player-active');
window.generatedVideo2.classList.remove('video-player-active');

// Track active video player for crossfading
window.activeVideoPlayer = 1; // 1 or 2

// Track transition state
window.isTransitioning = false;

// Periodic sync for looping videos
window.syncInterval = null;
window.startPeriodicSync = function() {
    // Clear any existing interval
    if (window.syncInterval) {
        clearInterval(window.syncInterval);
    }
    
    // Sync every 30 seconds
    window.syncInterval = setInterval(() => {
        if (!window.isTransitioning) {
            const activePlayer = window.activeVideoPlayer === 1 ? window.generatedVideo : window.generatedVideo2;
            
            if (activePlayer.loop && activePlayer.duration && !activePlayer.paused) {
                const expectedPosition = window.getGlobalSyncTime(activePlayer.duration);
                const currentPosition = activePlayer.currentTime;
                const drift = Math.abs(expectedPosition - currentPosition);
                
                // If drift is more than 0.5 seconds, resync
                if (drift > 0.5 && drift < (activePlayer.duration - 0.5)) {
                    console.log(`Resyncing video - drift: ${drift.toFixed(2)}s`);
                    activePlayer.currentTime = expectedPosition;
                }
            }
        }
    }, 30000); // Every 30 seconds
};

// Start sync when we start playing videos
window.startPeriodicSync();

// Global sync timing - all displays use same reference
window.getGlobalSyncTime = function(duration) {
    if (!duration || duration === 0) return 0;
    // Use Unix timestamp to sync across all displays
    const globalTime = Date.now() / 1000; // Convert to seconds
    return globalTime % duration;
};

// Video cache for preloading
window.videoCache = new Map();
window.preloadedVideos = new Set();

// URL normalization helper
window.normalizeVideoUrl = function(url) {
    try {
        return new URL(url, window.location.origin).href;
    } catch {
        return url;
    }
};

// Preload all videos into memory
window.preloadAllVideos = function(videoUrls) {
    console.log('Preloading all videos:', videoUrls);
    
    // Use staggered loading to avoid overwhelming the browser
    videoUrls.forEach((url, index) => {
        setTimeout(() => {
            const normalizedUrl = window.normalizeVideoUrl(url);
            
            if (!window.preloadedVideos.has(normalizedUrl)) {
                const video = document.createElement('video');
                video.preload = 'auto';
                video.muted = true;
                video.loop = true;
                
                // Add to DOM but hidden - helps with preloading
                video.style.position = 'absolute';
                video.style.left = '-9999px';
                video.style.width = '1px';
                video.style.height = '1px';
                document.body.appendChild(video);
                
                // Set source and start loading
                video.src = url;
                
                // Store in cache
                window.videoCache.set(normalizedUrl, video);
                
                const handleLoaded = () => {
                    window.preloadedVideos.add(normalizedUrl);
                    console.log(`Preloaded video ${index + 1}/${videoUrls.length}: ${url}`);
                    
                    // Keep playing to maintain buffer
                    video.play().then(() => {
                        video.pause();
                        video.currentTime = 0;
                    }).catch(() => {
                        // Ignore autoplay errors
                    });
                };
                
                video.addEventListener('canplaythrough', handleLoaded, { once: true });
                
                // Also handle loadeddata as backup
                video.addEventListener('loadeddata', () => {
                    if (video.readyState >= 3) {
                        handleLoaded();
                    }
                }, { once: true });
                
                // Force load
                video.load();
            }
        }, index * 500); // Stagger by 500ms
    });
};

// Preload a single video in the background
window.preloadNextVideo = function(videoUrl) {
    window.preloadAllVideos([videoUrl]);
};

// Simplified crossfade function with better reliability
window.crossfadeToVideo = function(videoUrl) {
    // Prevent overlapping transitions
    if (window.isTransitioning) {
        console.log('Transition already in progress, skipping...');
        return;
    }
    
    window.isTransitioning = true;
    
    const activePlayer = window.activeVideoPlayer === 1 ? window.generatedVideo : window.generatedVideo2;
    const inactivePlayer = window.activeVideoPlayer === 1 ? window.generatedVideo2 : window.generatedVideo;
    
    console.log(`Starting crossfade from player ${window.activeVideoPlayer} to ${window.activeVideoPlayer === 1 ? 2 : 1}`);
    
    // Reset inactive player
    inactivePlayer.style.opacity = '0';
    inactivePlayer.classList.remove('video-player-active');
    
    // Configure the inactive player
    inactivePlayer.muted = true;
    inactivePlayer.loop = activePlayer.loop;
    inactivePlayer.preload = 'auto';
    
    // Check if video is already loaded in this player
    const normalizedUrl = window.normalizeVideoUrl(videoUrl);
    const isPreloaded = window.normalizeVideoUrl(inactivePlayer.src) === normalizedUrl && inactivePlayer.readyState >= 3;
    
    if (!isPreloaded) {
        // Check if we have this video in cache
        const cachedVideo = window.videoCache.get(normalizedUrl);
        if (cachedVideo && cachedVideo.readyState >= 3) {
            // Copy attributes from cached video
            console.log('Using cached video data for:', videoUrl);
            inactivePlayer.src = videoUrl;
            // The browser should use the cached data
        } else {
            // Load the new video
            inactivePlayer.src = videoUrl;
        }
    }
    
    // Simple approach: wait for the video to be ready to play
    const startTransition = () => {
        console.log('Video ready, starting transition');
        
        // Synchronize video start time for multiple displays
        const syncVideos = () => {
            // Wait for video metadata to load
            const waitForDuration = (video) => {
                return new Promise((resolve) => {
                    if (video.duration && !isNaN(video.duration)) {
                        resolve();
                    } else {
                        video.addEventListener('loadedmetadata', () => resolve(), { once: true });
                        // Timeout after 1 second
                        setTimeout(resolve, 1000);
                    }
                });
            };
            
            waitForDuration(inactivePlayer).then(() => {
                if (activePlayer.loop && inactivePlayer.loop && inactivePlayer.duration) {
                    try {
                        // Use global sync time for all displays
                        const syncPosition = window.getGlobalSyncTime(inactivePlayer.duration);
                        inactivePlayer.currentTime = syncPosition;
                        console.log(`Synced video to global position: ${syncPosition.toFixed(2)}s of ${inactivePlayer.duration.toFixed(2)}s`);
                    } catch (e) {
                        console.log('Could not sync video position:', e);
                    }
                }
            });
        };
        
        syncVideos();
        
        // Start playing the new video
        inactivePlayer.play().then(() => {
            // Use a consistent delay across all displays
            const transitionDelay = 50;
            
            setTimeout(() => {
                // Apply the transition by changing opacity directly
                inactivePlayer.style.transition = 'opacity 1.2s cubic-bezier(0.4, 0, 0.2, 1)';
                activePlayer.style.transition = 'opacity 1.2s cubic-bezier(0.4, 0, 0.2, 1)';
                
                // Force a reflow to ensure styles are applied
                void inactivePlayer.offsetHeight;
                void activePlayer.offsetHeight;
                
                // Start the crossfade at a consistent time
                requestAnimationFrame(() => {
                    inactivePlayer.style.opacity = '1';
                    activePlayer.style.opacity = '0';
                    
                    // Update classes for consistency
                    inactivePlayer.classList.add('video-player-active');
                    activePlayer.classList.remove('video-player-active');
                    
                    // Clean up after transition
                    setTimeout(() => {
                        activePlayer.pause();
                        // Don't clear src to allow quick re-use
                        window.activeVideoPlayer = window.activeVideoPlayer === 1 ? 2 : 1;
                        window.isTransitioning = false;
                        console.log('Crossfade complete');
                    }, 1300); // Slightly longer than transition duration
                });
            }, transitionDelay);
        }).catch(error => {
            console.error('Failed to play video:', error);
            window.isTransitioning = false;
        });
    };
    
    // If video is already preloaded, start immediately
    if (isPreloaded) {
        console.log('Video was preloaded, starting transition immediately');
        startTransition();
    } else {
        // Use a single reliable event
        let hasStarted = false;
        const handleCanPlay = () => {
            if (!hasStarted && inactivePlayer.readyState >= 3) {
                hasStarted = true;
                inactivePlayer.removeEventListener('canplay', handleCanPlay);
                startTransition();
            }
        };
        
        inactivePlayer.addEventListener('canplay', handleCanPlay);
        
        // Check immediately in case video loads very quickly
        if (inactivePlayer.readyState >= 3) {
            handleCanPlay();
        }
        
        // Fallback timeout
        setTimeout(() => {
            if (!hasStarted) {
                console.log('Timeout reached, forcing transition');
                inactivePlayer.removeEventListener('canplay', handleCanPlay);
                hasStarted = true;
                startTransition();
            }
        }, 3000);
    }
    
    // Error handling
    inactivePlayer.addEventListener('error', (e) => {
        console.error('Video load error:', e);
        window.isTransitioning = false;
    }, { once: true });
};

// Socket event handlers
window.socket.on('connect', () => {
    console.log('Connected to server');
    window.messageDiv.textContent = '';
    
    // Clear cache on reconnect to ensure fresh data
    if (window.videoCache && window.videoCache.size > 0) {
        console.log('Clearing video cache on reconnect');
        window.videoCache.clear();
        window.preloadedVideos.clear();
    }
    
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
    
    // Stop periodic sync
    if (window.syncInterval) {
        clearInterval(window.syncInterval);
        window.syncInterval = null;
    }
    
    // Clean up video cache to free memory
    if (window.videoCache) {
        window.videoCache.forEach((video, url) => {
            video.pause();
            video.src = '';
            video.load();
            if (video.parentNode) {
                video.parentNode.removeChild(video);
            }
        });
        window.videoCache.clear();
        window.preloadedVideos.clear();
    }
    
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
    window.crossfadeToVideo(data.url);
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
        window.crossfadeToVideo(data.url);
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
        // Set loop property on both video elements
        window.generatedVideo.loop = data.loop || false;
        window.generatedVideo2.loop = data.loop || false;
        window.crossfadeToVideo(data.video_url);
        window.loadingDiv.style.display = 'none';
        
        // Preload the next video if provided
        if (data.next_video_url) {
            setTimeout(() => {
                window.preloadNextVideo(data.next_video_url);
            }, 2000); // Start preloading after 2 seconds
        }
        
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

window.socket.on('font_config_update', (data) => {
    console.log('Received font config update:', data.config);
    
    // Update Clock config if available
    if (window.Clock && window.Clock.updateConfig) {
        window.Clock.updateConfig(data.config);
    }
    
    // Update FontManager UI if available
    if (window.FontManager && window.FontManager.updateUIFromConfig) {
        window.FontManager.updateUIFromConfig(data.config);
    }
    
    // Load Google Font if needed
    if (data.config.fontUrl && window.FontManager && window.FontManager.loadGoogleFont) {
        window.FontManager.loadGoogleFont(data.config.fontUrl);
    }
});

window.socket.on('preload_videos', (data) => {
    console.log('Received videos to preload:', data.urls);
    if (data.urls && data.urls.length > 0) {
        window.preloadAllVideos(data.urls);
    }
});

// UI update functions
function updateUI(state) {
    // Don't update status through this function since StateManager handles it
    if (!window.StateManager) {
        window.statusDiv.textContent = state.status;
    }
}
