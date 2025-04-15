class BackgroundManager {
    constructor() {
        this.container = document.getElementById('container');
        this.currentImage = null;
        this.fadeDuration = 5000; // 5 seconds in milliseconds
        this.updateInterval = 60000; // 1 minute in milliseconds
        this.isLoading = false;
        
        // Time segments configuration
        this.timeSegments = {
            '0000-0559': { start: 0, end: 559, folder: '0000-0559', minImage: 3000, maxImage: 3287 },
            '0600-1159': { start: 600, end: 1159, folder: '0600-1159', minImage: 4000, maxImage: 4254 },
            '1200-1759': { start: 1200, end: 1759, folder: '1200-1759', minImage: 2000, maxImage: 2287 },
            '1800-2359': { start: 1800, end: 2359, folder: '1800-2359', minImage: 1000, maxImage: 1287 }
        };

        // Preload the first image
        this.preloadNextImage().then(() => {
            this.start();
        });
    }

    async preloadNextImage() {
        const newImagePath = this.getImagePath();
        if (newImagePath === this.currentImage) return;

        return new Promise((resolve) => {
            const img = new Image();
            img.onload = () => {
                this.nextImage = img;
                resolve();
            };
            img.src = newImagePath;
        });
    }

    getCurrentTimeSegment() {
        const now = new Date();
        const currentTime = now.getHours() * 100 + now.getMinutes();
        
        for (const [segment, config] of Object.entries(this.timeSegments)) {
            if (currentTime >= config.start && currentTime <= config.end) {
                return config;
            }
        }
        return this.timeSegments['0000-0559']; // Default to first segment if no match
    }

    getImageNumberForTime() {
        const segment = this.getCurrentTimeSegment();
        const now = new Date();
        const minutesInDay = now.getHours() * 60 + now.getMinutes();
        const segmentStartMinutes = Math.floor(segment.start / 100) * 60 + (segment.start % 100);
        const segmentEndMinutes = Math.floor(segment.end / 100) * 60 + (segment.end % 100);
        const segmentDuration = segmentEndMinutes - segmentStartMinutes;
        const positionInSegment = minutesInDay - segmentStartMinutes;
        
        const range = segment.maxImage - segment.minImage;
        const imageNumber = Math.floor((positionInSegment / segmentDuration) * range) + segment.minImage;
        
        return Math.min(Math.max(imageNumber, segment.minImage), segment.maxImage);
    }

    getImagePath() {
        const segment = this.getCurrentTimeSegment();
        const imageNumber = this.getImageNumberForTime();
        return `/static/images/backgrounds/${segment.folder}/DR-BG-${imageNumber}.jpg`;
    }

    async changeBackground() {
        if (this.isLoading) return;
        
        const newImagePath = this.getImagePath();
        if (newImagePath === this.currentImage) return;

        this.isLoading = true;

        try {
            // If we have a preloaded image, use it
            if (this.nextImage && this.nextImage.src === newImagePath) {
                this.container.style.backgroundImage = `url('${newImagePath}')`;
                this.currentImage = newImagePath;
            } else {
                // Otherwise, load the new image
                const img = new Image();
                await new Promise((resolve) => {
                    img.onload = resolve;
                    img.src = newImagePath;
                });
                this.container.style.backgroundImage = `url('${newImagePath}')`;
                this.currentImage = newImagePath;
            }

            // Preload the next image
            await this.preloadNextImage();
        } finally {
            this.isLoading = false;
        }
    }

    start() {
        // Initial background set
        this.changeBackground();
        
        // Set up interval for background changes
        setInterval(() => {
            this.changeBackground();
        }, this.updateInterval);
    }
}

// Initialize the background manager when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.backgroundManager = new BackgroundManager();
}); 