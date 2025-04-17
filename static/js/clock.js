// Clock functionality for Dream Recorder
const Clock = {
    clockInterval: null,
    colonVisible: true,
    digitElements: null,
    colonElement: null,

    // Initialize the clock
    init() {
        // Cache DOM elements
        this.digitElements = document.querySelectorAll('.digit');
        this.colonElement = document.querySelector('.colon');
        
        // Preload all number images
        this.preloadImages();
        
        // Start the clock
        this.updateClock();
        this.clockInterval = setInterval(() => {
            this.updateClock();
        }, 1000);
    },

    // Preload all number images
    preloadImages() {
        // Preload numbers
        for (let i = 0; i <= 9; i++) {
            const img = new Image();
            img.src = `/static/images/clock/${i}.png`;
        }
        // Preload colon
        const colonImg = new Image();
        colonImg.src = '/static/images/clock/colon.png';
    },

    // Update the clock display
    updateClock() {
        const now = new Date();
        const hours = now.getHours();
        const minutes = now.getMinutes();
        
        // Toggle colon visibility
        this.colonVisible = !this.colonVisible;
        this.colonElement.classList.toggle('hidden', !this.colonVisible);
        
        // Format time as string with leading zeros
        const timeStr = `${hours.toString().padStart(2, '0')}${minutes.toString().padStart(2, '0')}`;
        
        // Update each digit
        for (let i = 0; i < 4; i++) {
            const digit = timeStr[i];
            this.digitElements[i].src = `/static/images/clock/${digit}.png`;
        }
    },

    // Clean up when clock is no longer needed
    cleanup() {
        if (this.clockInterval) {
            clearInterval(this.clockInterval);
            this.clockInterval = null;
        }
    }
};

// Initialize clock when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    Clock.init();
});

// Make Clock globally accessible
window.Clock = Clock; 