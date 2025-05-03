class IconAnimations {
    static TYPES = {
        RECORDING: 'recording',
        GENERATING: 'generating',
        ERROR: 'error'
    };

    static WEBP_PATHS = {
        [IconAnimations.TYPES.RECORDING]: '/static/images/icons/recording.webp',
        [IconAnimations.TYPES.GENERATING]: '/static/images/icons/generating.webp',
        [IconAnimations.TYPES.ERROR]: '/static/images/icons/error.webp'
    };

    static init() {
        this.animations = document.getElementById('icon-animations');
        if (!this.animations) {
            console.error('Icon animations container not found');
            return;
        }
        // Insert WebP <img> tags if not present
        this.ensureWebpImages();
        this.hideAll();
    }

    static ensureWebpImages() {
        Object.entries(this.WEBP_PATHS).forEach(([type, path]) => {
            const container = this.animations.querySelector(`.${type}-animation`);
            if (container && !container.querySelector('img')) {
                const img = document.createElement('img');
                img.src = path;
                img.alt = `${type} animation`;
                container.appendChild(img);
            }
        });
    }

    static show(type) {
        this.hideAll();
        const animation = this.animations.querySelector(`.${type}-animation`);
        if (animation) {
            animation.style.display = 'flex';
        }
    }

    static hide(type) {
        if (type) {
            const animation = this.animations.querySelector(`.${type}-animation`);
            if (animation) {
                animation.style.display = 'none';
            }
        }
    }

    static hideAll() {
        const animations = this.animations.querySelectorAll('.icon-animation');
        animations.forEach(animation => {
            animation.style.display = 'none';
        });
    }
}

// Initialize animations when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    IconAnimations.init();
});

// Make IconAnimations globally accessible
window.IconAnimations = IconAnimations; 