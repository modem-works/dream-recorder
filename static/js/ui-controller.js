// UI Controller for Dream Recorder
document.addEventListener('DOMContentLoaded', () => {
    // Input simulator buttons
    const singleTapBtn = document.getElementById('singleTapBtn');
    const doubleTapBtn = document.getElementById('doubleTapBtn');
    
    // Input simulator handlers
    singleTapBtn.addEventListener('click', () => simulateInput('single_tap'));
    doubleTapBtn.addEventListener('click', () => simulateInput('double_tap'));
    
    // Listen for state changes
    document.addEventListener('stateChange', (event) => {
        updateUIForState(event.detail.state);
    });
    
    // Initial UI state
    if (StateManager) {
        updateUIForState(StateManager.currentState);
    }
    
    // Add keyboard shortcut to toggle debug console
    document.addEventListener('keydown', (event) => {
        // Check for Ctrl+D (Windows/Linux) or Cmd+D (Mac)
        if ((event.ctrlKey || event.metaKey) && event.key === 'd') {
            event.preventDefault(); // Prevent default browser behavior
            toggleDebugConsole();
        }
    });
});

// Simulate input for development/testing
function simulateInput(eventType) {
    console.log(`Simulating input: ${eventType}`);
    // Instead of handling locally, emit to server so all clients receive it
    if (window.socket) {
        // Call the API endpoint to broadcast to all clients
        const endpoint = eventType === 'single_tap' ? '/api/gpio_single_tap' : '/api/gpio_double_tap';
        fetch(endpoint, { method: 'POST' })
            .then(response => response.json())
            .then(data => console.log(`API response:`, data))
            .catch(error => console.error(`API error:`, error));
    } else if (StateManager) {
        // Fallback to local handling if no socket
        StateManager.handleDeviceEvent(eventType);
    }
}

// Update UI based on state
function updateUIForState(state) {
    const container = document.querySelector('.container');
    
    // Remove all state classes
    container.classList.remove('clock', 'recording', 'processing', 'playback', 'error');
    
    // Add current state class
    container.classList.add(state);
}

// Toggle debug console visibility
function toggleDebugConsole() {
    const debugConsole = document.querySelector('.debug-console');
    if (debugConsole) {
        debugConsole.classList.toggle('hidden');
        console.log('Debug console toggled:', !debugConsole.classList.contains('hidden') ? 'visible' : 'hidden');
    }
} 