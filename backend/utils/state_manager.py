"""
State Manager for Dream Recorder
Manages the application state and provides methods to update and query the state
"""

import time
import logging
import json
import os
from threading import Lock
from datetime import datetime

logger = logging.getLogger(__name__)

class StateManager:
    """Manages the application state"""
    
    VALID_STATES = [
        'ready',             # Ready to record
        'recording',         # Recording in progress
        'processing_audio',  # Processing audio to text
        'enhancing_prompt',  # Enhancing prompt with OpenAI
        'generating_video',  # Generating video with LumaLabs
        'processing_video',  # Post-processing video with FFmpeg
        'video_ready',       # Video ready to be played
        'error'              # Error state
    ]
    
    def __init__(self, initial_state='ready', state_file=None):
        """
        Initialize the state manager
        
        Args:
            initial_state: Initial state of the application
            state_file: Path to file for persisting state (optional)
        """
        if initial_state not in self.VALID_STATES:
            raise ValueError(f"Invalid state: {initial_state}")
        
        self._current_state = initial_state
        self._last_updated = time.time()
        self._state_file = state_file
        self._lock = Lock()
        self._error_message = None
        self.state_history = []
        
        # Create state data directory if it doesn't exist
        if state_file:
            os.makedirs(os.path.dirname(state_file), exist_ok=True)
        
        logger.info(f"State manager initialized with state: {initial_state}")
    
    @property
    def current_state(self):
        """Get the current state"""
        with self._lock:
            return self._current_state
    
    @property
    def last_updated(self):
        """Get the timestamp of the last state update"""
        with self._lock:
            return self._last_updated
    
    @property
    def error_message(self):
        """Get the current error message, if any"""
        with self._lock:
            return self._error_message
    
    def set_state(self, state, error_message=None):
        """
        Set the application state and timestamp
        
        Args:
            state (str): New application state
            error_message (str, optional): Error message if state is 'error'
        """
        if state == self.current_state:
            # Don't log if state isn't changing
            return
            
        # Store the previous state before changing
        previous_state = self.current_state
        
        # Update state
        with self._lock:
            self._current_state = state
            self._last_updated = time.time()
            
            # Special handling for error state
            if state == 'error':
                self._error_message = str(error_message) if error_message else 'Unknown error'
                logger.error(f"Error state: {self._error_message}")
                # Add to history with error details
                self.state_history.append({
                    'state': state,
                    'error_message': self._error_message,
                    'timestamp': datetime.now().isoformat(),
                    'previous_state': previous_state
                })
            else:
                # For non-error states, clear any error message
                self._error_message = None
                logger.info(f"State changed to: {state}")
                # Add to history
                self.state_history.append({
                    'state': state,
                    'timestamp': datetime.now().isoformat(),
                    'previous_state': previous_state
                })
            
            # Persist state if a state file is configured
            self._save_state()
    
    def _save_state(self):
        """Save the current state to the state file"""
        if not self._state_file:
            return
        
        try:
            state_data = {
                'state': self._current_state,
                'last_updated': self._last_updated,
                'error_message': self._error_message
            }
            
            with open(self._state_file, 'w') as f:
                json.dump(state_data, f)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def load_state(self):
        """Load the state from the state file"""
        if not self._state_file or not os.path.exists(self._state_file):
            return False
        
        try:
            with open(self._state_file, 'r') as f:
                state_data = json.load(f)
            
            with self._lock:
                self._current_state = state_data.get('state', 'ready')
                self._last_updated = state_data.get('last_updated', time.time())
                self._error_message = state_data.get('error_message')
                
            logger.info(f"Loaded state: {self._current_state}")
            return True
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return False
    
    def get_state(self):
        """
        Get current application state with metadata
        
        Returns:
            dict: Current state information
        """
        state_info = {
            'state': self.current_state,
            'last_updated': self.last_updated,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add error message if we're in an error state
        if self.current_state == 'error' and self.error_message:
            state_info['error_message'] = self.error_message
            
        return state_info
        
    def get_state_history(self):
        """
        Get history of state transitions
        
        Returns:
            list: History of state transitions
        """
        return self.state_history 