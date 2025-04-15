class IconAnimations {
    static TYPES = {
        RECORDING: 'recording',
        GENERATING: 'generating',
        ERROR: 'error'
    };

    static FRAME_COUNTS = {
        [IconAnimations.TYPES.RECORDING]: 150,
        [IconAnimations.TYPES.GENERATING]: 150,
        [IconAnimations.TYPES.ERROR]: 71
    };

    static FRAME_PATHS = {
        [IconAnimations.TYPES.RECORDING]: '/static/images/icons/rec/rec-',
        [IconAnimations.TYPES.GENERATING]: '/static/images/icons/gen/gen-',
        [IconAnimations.TYPES.ERROR]: '/static/images/icons/error/error-'
    };

    static init() {
        this.animations = document.getElementById('icon-animations');
        if (!this.animations) {
            console.error('Icon animations container not found');
            return;
        }

        // Hide all animations initially
        this.hideAll();
    }

    static show(type) {
        this.hideAll();
        const animation = this.animations.querySelector(`.${type}-animation`);
        if (animation) {
            animation.style.display = 'block';
            this.startAnimation(animation, type);
        }
    }

    static startAnimation(element, type) {
        let currentFrame = 0;
        const totalFrames = this.FRAME_COUNTS[type];
        const framePath = this.FRAME_PATHS[type];

        const animate = () => {
            if (element.style.display === 'none') return; // Stop if hidden
            
            const frameNumber = currentFrame.toString().padStart(3, '0');
            element.style.backgroundImage = `url('${framePath}${frameNumber}.png')`;
            
            currentFrame = (currentFrame + 1) % totalFrames;
            requestAnimationFrame(animate);
        };

        animate();
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