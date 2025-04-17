// Clock functionality for Dream Recorder
const Clock = {
    clockInterval: null,
    colonVisible: true,

    // Initialize the clock
    init() {
        this.updateClock();
        this.clockInterval = setInterval(() => {
            this.updateClock();
        }, 1000);
    },

    // Update the clock display
    updateClock() {
        const clockDisplay = document.getElementById('clockDisplay');
        if (!clockDisplay) return;

        const now = new Date();
        let hours = now.getHours();
        const minutes = now.getMinutes().toString().padStart(2, '0');
        
        // Toggle colon visibility
        this.colonVisible = !this.colonVisible;
        const colon = this.colonVisible ? ':' : ' ';
        
        // Format hours (12-hour format)
        const ampm = hours >= 12 ? 'PM' : 'AM';
        hours = hours % 12;
        hours = hours ? hours : 12; // Convert 0 to 12
        
        clockDisplay.textContent = `${hours}${colon}${minutes} ${ampm}`;
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