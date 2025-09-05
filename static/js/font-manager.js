// Font Manager for Dream Recorder
const FontManager = {
    // Debounce timer for font size saves
    fontSizeSaveTimer: null,
    
    // Initialize font controls
    init() {
        this.setupEventListeners();
        // Wait for Clock to load its config from server, then update UI
        this.waitForClockConfig();
        // Listen for font config updates from other browsers
        this.listenForFontUpdates();
    },
    
    // Wait for Clock config to be loaded from server
    async waitForClockConfig() {
        // Give Clock time to initialize
        const checkInterval = setInterval(() => {
            if (window.Clock && window.Clock.config) {
                clearInterval(checkInterval);
                this.updateUIFromConfig(window.Clock.config);
            }
        }, 100);
        
        // Stop checking after 5 seconds
        setTimeout(() => clearInterval(checkInterval), 5000);
    },
    
    // Listen for font config updates from other browsers
    listenForFontUpdates() {
        // The socket event handler is already set up in sockets.js
        // This method is just for clarity and potential future extensions
        console.log('FontManager: Listening for font config updates');
    },
    
    // Update UI controls from Clock config
    updateUIFromConfig(config) {
        if (!config) return;
        
        // Update font size slider
        if (config.fontSize) {
            const fontSizeSlider = document.getElementById('fontSize');
            const fontSizeValue = document.getElementById('fontSizeValue');
            if (fontSizeSlider) {
                let px;
                if (config.fontSize.includes('rem')) {
                    // Convert rem to px
                    const rem = parseFloat(config.fontSize);
                    px = rem * 16;
                } else {
                    px = parseInt(config.fontSize);
                }
                fontSizeSlider.value = px;
                const rem = (px / 16).toFixed(1);
                fontSizeValue.textContent = `${px}px (${rem}rem)`;
            }
        }
        
        // Update font weight selector
        if (config.fontWeight) {
            const fontWeightSelect = document.getElementById('fontWeight');
            if (fontWeightSelect) {
                // Handle both numeric and string values
                let weight = config.fontWeight;
                if (weight === 'normal') weight = '400';
                if (weight === 'bold') weight = '700';
                fontWeightSelect.value = weight;
            }
        }
        
        // Update font selector
        if (config.fontFamily) {
            const fontSelector = document.getElementById('fontSelector');
            if (fontSelector) {
                const standardFont = Array.from(fontSelector.options).find(
                    opt => opt.value === config.fontFamily
                );
                fontSelector.value = standardFont ? config.fontFamily : 'custom';
                
                // If custom font, show the URL
                if (!standardFont && config.fontUrl) {
                    document.getElementById('customFontInput').style.display = 'block';
                    document.getElementById('googleFontUrl').value = config.fontUrl;
                }
            }
        }
        
        // Update time format selector
        if (config.timeFormat) {
            const timeFormatSelect = document.getElementById('timeFormat');
            if (timeFormatSelect) {
                timeFormatSelect.value = config.timeFormat;
            }
        }
        
        // Update show AM/PM checkbox
        if (config.showAmPm !== undefined) {
            const showAmPmCheckbox = document.getElementById('showAmPm');
            if (showAmPmCheckbox) {
                showAmPmCheckbox.checked = config.showAmPm;
            }
        }
    },

    // Setup event listeners for font controls
    setupEventListeners() {
        const fontSelector = document.getElementById('fontSelector');
        const customFontInput = document.getElementById('customFontInput');
        const googleFontUrl = document.getElementById('googleFontUrl');
        const applyGoogleFont = document.getElementById('applyGoogleFont');
        const fontSize = document.getElementById('fontSize');
        const fontSizeValue = document.getElementById('fontSizeValue');
        const fontWeight = document.getElementById('fontWeight');
        const timeFormat = document.getElementById('timeFormat');
        const showAmPm = document.getElementById('showAmPm');

        // Font selector change
        fontSelector?.addEventListener('change', (e) => {
            if (e.target.value === 'custom') {
                customFontInput.style.display = 'block';
            } else {
                customFontInput.style.display = 'none';
                const selectedOption = e.target.selectedOptions[0];
                const fontUrl = selectedOption.getAttribute('data-font-url');
                
                if (fontUrl) {
                    // Google Font preset
                    this.loadGoogleFont(fontUrl);
                    this.updateClockConfig({ 
                        fontFamily: e.target.value,
                        fontUrl: fontUrl
                    });
                } else {
                    // Standard font
                    this.applyFont(e.target.value);
                }
                this.saveSettings();
            }
        });

        // Apply Google font button
        applyGoogleFont?.addEventListener('click', () => {
            const url = googleFontUrl.value.trim();
            if (url) {
                this.applyGoogleFont(url);
            }
        });

        // Enter key in Google font input
        googleFontUrl?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const url = googleFontUrl.value.trim();
                if (url) {
                    this.applyGoogleFont(url);
                }
            }
        });

        // Font size slider
        fontSize?.addEventListener('input', (e) => {
            const px = e.target.value;
            const rem = (px / 16).toFixed(1);
            fontSizeValue.textContent = `${px}px (${rem}rem)`;
            this.updateClockConfig({ fontSize: `${rem}rem` });
            
            // Debounce the save to avoid too many requests while dragging
            clearTimeout(this.fontSizeSaveTimer);
            this.fontSizeSaveTimer = setTimeout(() => {
                this.saveSettings();
            }, 500); // Save 500ms after user stops dragging
        });

        // Font weight selector
        fontWeight?.addEventListener('change', (e) => {
            this.updateClockConfig({ fontWeight: e.target.value });
            this.saveSettings();
        });
        
        // Time format selector
        timeFormat?.addEventListener('change', (e) => {
            this.updateClockConfig({ timeFormat: e.target.value });
            this.saveSettings();
        });
        
        // Show AM/PM checkbox
        showAmPm?.addEventListener('change', (e) => {
            this.updateClockConfig({ showAmPm: e.target.checked });
            this.saveSettings();
        });
    },

    // Apply a standard font
    applyFont(fontFamily) {
        this.updateClockConfig({ fontFamily });
        this.saveSettings();
    },

    // Apply a Google font
    applyGoogleFont(input) {
        let fontUrl, fontFamily;

        // Check if input is a URL
        if (input.startsWith('http')) {
            fontUrl = input;
            // Extract font family from URL
            const match = input.match(/family=([^:&]+)/);
            if (match) {
                fontFamily = match[1].replace(/\+/g, ' ');
                // Handle fonts with weights in the URL
                if (fontFamily.includes(':')) {
                    fontFamily = fontFamily.split(':')[0];
                }
                fontFamily = `'${fontFamily}', sans-serif`;
            }
        } else {
            // Treat as font name
            const fontName = input.trim();
            fontFamily = `'${fontName}', sans-serif`;
            // Create Google Fonts URL
            const urlFontName = fontName.replace(/ /g, '+');
            fontUrl = `https://fonts.googleapis.com/css2?family=${urlFontName}:wght@100;300;400;500;700;900&display=swap`;
        }

        if (fontUrl && fontFamily) {
            // Load the font
            this.loadGoogleFont(fontUrl);
            // Update clock config
            this.updateClockConfig({ 
                fontFamily,
                fontUrl 
            });
            // Update selector to show custom is selected
            document.getElementById('fontSelector').value = 'custom';
            this.saveSettings();
        }
    },

    // Load Google Font
    loadGoogleFont(url) {
        // Remove existing Google font links
        const existingLinks = document.querySelectorAll('link[href*="fonts.googleapis.com"]');
        existingLinks.forEach(link => {
            if (link.href !== url) {
                link.remove();
            }
        });

        // Check if this font is already loaded
        const alreadyLoaded = document.querySelector(`link[href="${url}"]`);
        if (!alreadyLoaded) {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = url;
            document.head.appendChild(link);
        }
    },

    // Update clock configuration
    updateClockConfig(config) {
        if (window.Clock && window.Clock.updateConfig) {
            window.Clock.updateConfig(config);
        }
        
        // Update preview
        const preview = document.getElementById('fontPreview');
        if (preview) {
            // Update preview to use the same CSS variables
            preview.style.fontFamily = 'var(--clock-font-family)';
            preview.style.fontWeight = 'var(--clock-font-weight)';
            // Show current time in preview
            const now = new Date();
            const hours = now.getHours().toString().padStart(2, '0');
            const minutes = now.getMinutes().toString().padStart(2, '0');
            preview.textContent = `${hours}:${minutes}`;
        }
    },

    // Save settings to localStorage and server
    async saveSettings() {
        // Only save the fields we're actually managing
        const settings = {
            fontFamily: window.Clock?.config?.fontFamily,
            fontSize: window.Clock?.config?.fontSize,
            fontWeight: window.Clock?.config?.fontWeight,
            timeFormat: window.Clock?.config?.timeFormat,
            showAmPm: window.Clock?.config?.showAmPm
        };
        
        // Include fontUrl only if it exists (for Google fonts)
        if (window.Clock?.config?.fontUrl) {
            settings.fontUrl = window.Clock.config.fontUrl;
        }
        
        // Save to server config file
        try {
            const response = await fetch('/api/clock-config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(settings)
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('Clock config saved to server:', result);
                // The server will broadcast the font change to all connected clients
                // Show saved status
                this.showSavedStatus(settings);
            } else {
                console.error('Failed to save clock config to server:', response.status);
                // Still show saved status since localStorage worked
                this.showSavedStatus(settings);
            }
        } catch (error) {
            console.error('Error saving clock config to server:', error);
            // Still show saved status since localStorage worked
            this.showSavedStatus(settings);
        }
    },
    
    // Show saved status notification
    showSavedStatus(settings) {
        const statusDiv = document.getElementById('fontStatus');
        const infoSpan = document.getElementById('savedFontInfo');
        
        if (statusDiv && infoSpan) {
            const fontName = settings.fontFamily?.replace(/['"]/g, '').split(',')[0];
            const fontSize = settings.fontSize || '12rem';
            const fontWeight = settings.fontWeight || '400';
            const timeFormat = settings.timeFormat || '24hr';
            const showAmPm = settings.showAmPm !== undefined ? settings.showAmPm : true;
            
            infoSpan.innerHTML = `
                Font: ${fontName}<br>
                Size: ${fontSize}<br>
                Weight: ${fontWeight}<br>
                Time: ${timeFormat}${timeFormat === '12hr' ? (showAmPm ? ' with AM/PM' : ' no AM/PM') : ''}
            `;
            
            statusDiv.style.display = 'block';
            
            // Auto-hide after 3 seconds
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 3000);
        }
    },


};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    FontManager.init();
});

// Make FontManager globally accessible
window.FontManager = FontManager; 