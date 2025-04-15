const canvas = document.getElementById('visualizer');
const ctx = canvas.getContext('2d');

let mediaRecorder = null;
let audioContext = null;
let analyser = null;
let animationFrame = null;

// Set canvas size
function resizeCanvas() {
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
}
resizeCanvas();
window.addEventListener('resize', resizeCanvas);

// Audio visualization
function drawVisualizer() {
    if (!analyser) return;
    
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    analyser.getByteFrequencyData(dataArray);
    
    // Clear the canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Set up the line style
    ctx.lineWidth = 10;
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.8)'; // Semi-transparent white
    ctx.lineCap = 'round';  // Rounded line caps
    ctx.lineJoin = 'round'; // Rounded line joins
    ctx.beginPath();
    
    // Calculate the slice width
    const sliceWidth = canvas.width / bufferLength;
    let x = 0;
    
    // Start the path at the bottom of the canvas
    ctx.moveTo(0, canvas.height);
    
    // Draw the waveform
    for(let i = 0; i < bufferLength; i++) {
        // Normalize the value to a range that looks good
        const v = dataArray[i] / 128.0;
        const y = canvas.height - (v * canvas.height / 4);
        
        ctx.lineTo(x, y);
        x += sliceWidth;
    }
    
    // Complete the path
    ctx.stroke();
    
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
            mimeType: 'audio/webm;codecs=opus'
        });
        
        // Set up audio context and analyser for visualization
        audioContext = new AudioContext();
        const source = audioContext.createMediaStreamSource(stream);
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 256;
        source.connect(analyser);
        
        // Show visualizer and start drawing
        document.querySelector('.audio-visualizer').style.display = 'block';
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
                        window.socket.emit('audio_data', audioData);
                        console.log('Sent audio_data chunk, size:', audioData.data.length);
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
        window.errorDiv.textContent = `Error accessing microphone: ${err.message}`;
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
        // Hide visualizer
        document.querySelector('.audio-visualizer').style.display = 'none';
        if (window.socket) {
            window.socket.emit('stop_recording');
            console.log('Sent stop_recording event to server');
        }
    }
}; 