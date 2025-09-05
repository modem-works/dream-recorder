// Clock functionality for Dream Recorder
const Clock = {
    clockInterval: null,
    colonVisible: true,
    elements: {
        hourTens: null,
        hourOnes: null,
        colon: null,
        minuteTens: null,
        minuteOnes: null,
        ampm: null
    },

    // Configuration options will be loaded from file
    config: null,

    // Load configuration from file
    async loadConfig() {
        try {
            // Fetch config from server
            const response = await fetch('/api/clock-config-path');
            const { configPath } = await response.json();
            
            // Load the configuration
            const configResponse = await fetch(configPath);
            this.config = await configResponse.json();
            // Dynamically inject font link if fontUrl is present
            if (this.config.fontUrl) {
                const link = document.createElement('link');
                link.rel = 'stylesheet';
                link.href = this.config.fontUrl;
                document.head.appendChild(link);
            }
        } catch (error) {
            console.error('Failed to load clock configuration:', error);
            throw error;
        }
    },

    // Initialize the clock
    async init(config = {}) {
        // Load config first
        await this.loadConfig();
        
        // Override loaded config with any passed in options
        this.config = { ...this.config, ...config };
        
        // Apply configuration
        this.applyConfig();

        // Cache DOM elements
        this.elements.hourTens = document.querySelector('.hour-tens');
        this.elements.hourOnes = document.querySelector('.hour-ones');
        this.elements.colon = document.querySelector('.colon');
        this.elements.minuteTens = document.querySelector('.minute-tens');
        this.elements.minuteOnes = document.querySelector('.minute-ones');
        this.elements.ampm = document.querySelector('.ampm');
        
        // Start the clock
        this.updateClock();
        this.clockInterval = setInterval(() => {
            this.updateClock();
        }, 1000);
    },

    // Apply configuration to CSS variables
    applyConfig() {
        const root = document.documentElement;
        root.style.setProperty('--clock-font-family', this.config.fontFamily);
        root.style.setProperty('--clock-font-size', this.config.fontSize);
        root.style.setProperty('--clock-font-weight', this.config.fontWeight);
        root.style.setProperty('--clock-color', this.config.color);
        root.style.setProperty('--clock-glow-color', this.config.glowColor);
        root.style.setProperty('--clock-spacing', this.config.spacing);
    },

    // Update the clock display
    updateClock() {
        const now = new Date();
        let hours = now.getHours();
        const minutes = now.getMinutes().toString().padStart(2, '0');
        let ampm = '';
        
        // Handle 12-hour format if enabled
        if (this.config.timeFormat === '12hr') {
            ampm = hours >= 12 ? 'PM' : 'AM';
            hours = hours % 12 || 12; // Convert 0 to 12 for midnight
        }
        
        // Pad hours to 2 digits
        hours = hours.toString().padStart(2, '0');
        
        // Helper to update digit only if changed
        function updateDigit(element, newValue) {
            if (!element) return;
            const lastValue = element.getAttribute('data-value');
            if (lastValue !== newValue) {
                element.textContent = newValue;
                element.setAttribute('data-value', newValue);
            }
        }

        // Update digits only if changed
        updateDigit(this.elements.hourTens, hours[0]);
        updateDigit(this.elements.hourOnes, hours[1]);
        updateDigit(this.elements.minuteTens, minutes[0]);
        updateDigit(this.elements.minuteOnes, minutes[1]);
        
        // Update AM/PM indicator
        if (this.elements.ampm) {
            // Show AM/PM only if using 12hr format AND showAmPm is true
            if (this.config.timeFormat === '12hr' && this.config.showAmPm !== false) {
                this.elements.ampm.style.display = 'inline-block';
                updateDigit(this.elements.ampm, ampm);
            } else {
                this.elements.ampm.style.display = 'none';
            }
        }
        
        // Toggle colon visibility
        this.colonVisible = !this.colonVisible;
        if (this.elements.colon) {
            this.elements.colon.classList.toggle('hidden', !this.colonVisible);
        }
    },

    // Update configuration at runtime
    updateConfig(newConfig) {
        this.config = { ...this.config, ...newConfig };
        this.applyConfig();
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
    // Initialize with default config
    Clock.init();
});

// Make Clock globally accessible
window.Clock = Clock; 