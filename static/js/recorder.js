// Remove canvas and related variables
// const canvas = document.getElementById('visualizer');
// const ctx = canvas.getContext('2d');

let mediaRecorder = null;
let audioContext = null;
let analyser = null;
let animationFrame = null;

// Remove resizeCanvas and window resize event
// function resizeCanvas() { ... }
// resizeCanvas();
// window.addEventListener('resize', resizeCanvas);

// Audio visualization (now only animates the recording icon)
function drawVisualizer() {
    if (!analyser) {
        console.warn('drawVisualizer: analyser not initialized');
        return;
    }
    
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    analyser.getByteFrequencyData(dataArray);

    // Try time-domain data
    const timeDomainArray = new Uint8Array(bufferLength);
    analyser.getByteTimeDomainData(timeDomainArray);

    // Calculate intensity using RMS of time-domain data
    let sum = 0;
    for (let i = 0; i < timeDomainArray.length; i++) {
        let v = (timeDomainArray[i] - 128) / 128; // Normalize to -1..1
        sum += v * v;
    }
    const rms = Math.sqrt(sum / timeDomainArray.length); // Root mean square
    const intensity = rms; // 0 (silence) to ~1 (loud)

    // Animate the recording icon
    const recordingContainer = document.querySelector('.recording-animation');
    if (!recordingContainer) {
        console.warn('drawVisualizer: .recording-animation not found');
    }
    const recordingImg = recordingContainer ? recordingContainer.querySelector('img') : null;
    if (!recordingImg) {
        console.warn('drawVisualizer: .recording-animation img not found');
    }
    if (recordingImg) {
        // Add smooth transition if not already set
        if (!recordingImg.style.transition) {
            recordingImg.style.transition = 'transform 0.1s cubic-bezier(0.4,0,0.2,1)';
        }
        // Only pulse the scale (size), not opacity
        const scale = 1 + intensity * 1.2; // up to 2.2x
        recordingImg.style.transform = `scale(${scale})`;
        // Remove opacity pulsing
        recordingImg.style.opacity = '';
    }
    // Remove background color pulsing
    if (recordingContainer) {
        recordingContainer.style.backgroundColor = '';
    }

    animationFrame = requestAnimationFrame(drawVisualizer);
}

// Make these functions available globally for socket.js to use
window.startRecording = async function() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                channelCount: 1,
                sampleRate: 44100,
                sampleSize: 16
            } 
        });
        mediaRecorder = new MediaRecorder(stream, {
            mimeType: 'audio/webm;codecs=opus',
            audioBitsPerSecond: 128000
        });
        
        // Set up audio context and analyser for visualization
        audioContext = new AudioContext();
        const source = audioContext.createMediaStreamSource(stream);
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 256;
        source.connect(analyser);
        
        // Ensure recording animation is visible
        if (window.IconAnimations) {
            window.IconAnimations.show('recording');
        }
        drawVisualizer();

        // Handle audio data
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                // Convert blob to array buffer before sending
                event.data.arrayBuffer().then(buffer => {
                    const audioData = {
                        data: Array.from(new Uint8Array(buffer)),
                        timestamp: Date.now()
                    };
                    // Emit through the global socket object
                    if (window.socket) {
                        window.socket.emit('stream_recording', audioData);
                        // console.log('Sent audio_data chunk, size:', audioData.data.length);
                    }
                });
            }
        };

        // Start recording
        mediaRecorder.start(100); // Send chunks every 100ms
        if (window.socket) {
            window.socket.emit('start_recording');
            console.log('Sent start_recording event to server');
        }
    } catch (err) {
        window.messageDiv.textContent = `Error accessing microphone: ${err.message}`;
        console.error('Error accessing microphone:', err);
        
        // Update state manager if available
        if (window.StateManager) {
            window.StateManager.updateState(window.StateManager.STATES.ERROR, `Error accessing microphone: ${err.message}`);
        }
    }
};

window.stopRecording = function() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
        if (audioContext) {
            audioContext.close();
            audioContext = null;
        }
        if (animationFrame) {
            cancelAnimationFrame(animationFrame);
            animationFrame = null;
        }
        // Hide recording animation
        if (window.IconAnimations) {
            window.IconAnimations.hide('recording');
        }
        if (window.socket) {
            window.socket.emit('stop_recording');
            console.log('Sent stop_recording event to server');
        }
    }
}; 