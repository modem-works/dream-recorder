class BackgroundManager {
    constructor() {
        this.container = document.getElementById('container');
        this.currentImage = null;
        this.fadeDuration = 5000;
        this.updateInterval = 60000; // 1 minute in milliseconds
        this.isLoading = false;
        this.totalImages = parseInt(document.body.dataset.totalBackgroundImages);
        
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

    getImageNumberForTime() {
        const now = new Date();
        const minutesInDay = now.getHours() * 60 + now.getMinutes();
        const totalMinutes = 24 * 60;
        
        // Calculate which image to show based on time of day
        const imageNumber = Math.floor((minutesInDay / totalMinutes) * this.totalImages);
        return Math.min(Math.max(imageNumber, 0), this.totalImages - 1);
    }

    getImagePath() {
        const imageNumber = this.getImageNumberForTime();
        return `/static/images/background/${imageNumber}.jpg`;
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