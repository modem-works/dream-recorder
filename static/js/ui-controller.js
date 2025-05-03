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
    container.classList.remove('clock', 'recording', 'processing', 'playback', 'error');
    
    // Add current state class
    container.classList.add(state);
} 