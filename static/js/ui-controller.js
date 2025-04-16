// UI Controller for Dream Recorder
document.addEventListener('DOMContentLoaded', () => {
    // Input simulator buttons
    const tapBtn = document.getElementById('tapBtn');
    const doubleTapBtn = document.getElementById('doubleTapBtn');
    const holdStartBtn = document.getElementById('holdStartBtn');
    const holdReleaseBtn = document.getElementById('holdReleaseBtn');
    
    // Input simulator handlers
    tapBtn.addEventListener('click', () => simulateInput('tap'));
    doubleTapBtn.addEventListener('click', () => simulateInput('double_tap'));
    holdStartBtn.addEventListener('click', () => simulateInput('hold_start'));
    holdReleaseBtn.addEventListener('click', () => simulateInput('hold_release'));
    
    // Listen for state changes
    document.addEventListener('stateChange', (event) => {
        updateUIForState(event.detail.state);
    });
    
    // Initial UI state
    if (StateManager) {
        updateUIForState(StateManager.currentState);
    }
});

// Simulate input for development/testing
function simulateInput(eventType) {
    console.log(`Simulating input: ${eventType}`);
    if (StateManager) {
        StateManager.handleDeviceEvent(eventType);
    }
}

// Update UI based on state
function updateUIForState(state) {
    const container = document.querySelector('.container');
    
    // Remove all state classes
    container.classList.remove('idle', 'recording', 'processing', 'playback', 'error');
    
    // Add current state class
    container.classList.add(state);
} 