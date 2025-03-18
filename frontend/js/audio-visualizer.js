/**
 * Audio Visualizer Module
 * Provides audio visualization functionality
 */

class AudioVisualizer {
    constructor(canvasElement, options = {}) {
        this.canvas = canvasElement;
        this.ctx = this.canvas.getContext('2d');
        this.analyser = null;
        this.dataArray = null;
        this.source = null;
        this.animationId = null;
        this.isActive = false;
        
        // Set default options
        this.options = {
            fftSize: options.fftSize || 256,
            barColor: options.barColor || 'rgba(255, 64, 129, 1)',
            backgroundColor: options.backgroundColor || 'rgba(0, 0, 0, 0)',
            barWidth: options.barWidth || 2,
            barSpacing: options.barSpacing || 1,
            smoothingTimeConstant: options.smoothingTimeConstant || 0.85
        };
    }
    
    connect(audioContext, mediaStream) {
        if (!audioContext || !mediaStream) {
            console.error('Audio context and media stream are required');
            return;
        }
        
        // Create analyzer
        this.analyser = audioContext.createAnalyser();
        this.analyser.fftSize = this.options.fftSize;
        this.analyser.smoothingTimeConstant = this.options.smoothingTimeConstant;
        
        // Create source
        this.source = audioContext.createMediaStreamSource(mediaStream);
        this.source.connect(this.analyser);
        
        // Create data array
        const bufferLength = this.analyser.frequencyBinCount;
        this.dataArray = new Uint8Array(bufferLength);
        
        // Set canvas dimensions
        this.resize();
        
        // Start visualizing
        this.start();
    }
    
    start() {
        if (this.isActive) return;
        this.isActive = true;
        this.draw();
    }
    
    stop() {
        this.isActive = false;
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
        
        // Clear canvas
        if (this.canvas && this.ctx) {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        }
    }
    
    resize() {
        if (this.canvas) {
            this.canvas.width = this.canvas.clientWidth;
            this.canvas.height = this.canvas.clientHeight;
        }
    }
    
    draw() {
        if (!this.isActive || !this.analyser) return;
        
        this.animationId = requestAnimationFrame(this.draw.bind(this));
        
        // Resize canvas if needed
        this.resize();
        
        // Get frequency data
        this.analyser.getByteFrequencyData(this.dataArray);
        
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw background
        this.ctx.fillStyle = this.options.backgroundColor;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Calculate bar width based on canvas width and buffer length
        const totalBars = this.dataArray.length;
        const canvasWidth = this.canvas.width;
        const canvasHeight = this.canvas.height;
        
        const effectiveBarWidth = this.options.barWidth;
        const effectiveBarSpacing = this.options.barSpacing;
        const barCount = Math.min(totalBars, Math.floor(canvasWidth / (effectiveBarWidth + effectiveBarSpacing)));
        
        // Draw bars
        let x = 0;
        
        for (let i = 0; i < barCount; i++) {
            const barHeight = (this.dataArray[i] / 255) * canvasHeight;
            
            // Calculate bar color with opacity based on height
            const opacity = 0.3 + (barHeight / canvasHeight) * 0.7;
            const color = this.options.barColor.replace('1)', `${opacity})`);
            
            this.ctx.fillStyle = color;
            this.ctx.fillRect(x, canvasHeight - barHeight, effectiveBarWidth, barHeight);
            
            x += effectiveBarWidth + effectiveBarSpacing;
        }
    }
    
    disconnect() {
        this.stop();
        
        if (this.source) {
            this.source.disconnect();
            this.source = null;
        }
        
        this.analyser = null;
        this.dataArray = null;
    }
}

export default AudioVisualizer;