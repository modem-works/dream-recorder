const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
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
    
    ctx.fillStyle = '#f8f9fa';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    const barWidth = (canvas.width / bufferLength) * 2.5;
    let barHeight;
    let x = 0;
    
    for(let i = 0; i < bufferLength; i++) {
        barHeight = dataArray[i] / 2;
        ctx.fillStyle = '#4caf50';
        ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
        x += barWidth + 1;
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

// Local event listeners
startBtn.addEventListener('click', window.startRecording);
stopBtn.addEventListener('click', window.stopRecording); 