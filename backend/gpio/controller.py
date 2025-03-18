"""
GPIO Controller for Dream Recorder
Handles interactions with the TTP223B capacitive touch sensor
"""

import logging
import time
from threading import Timer
import os

# Check if running on Raspberry Pi
try:
    import RPi.GPIO as GPIO
    from gpiozero import Button
    RPI_AVAILABLE = True
except ImportError:
    RPI_AVAILABLE = False

logger = logging.getLogger(__name__)

class GPIOController:
    """Controls the GPIO pins for the touch sensor"""
    
    def __init__(self, state_manager, touch_pin=17, debounce_time=0.3):
        """
        Initialize the GPIO controller
        
        Args:
            state_manager: StateManager instance to track application state
            touch_pin: GPIO pin number for the touch sensor (BCM numbering)
            debounce_time: Time in seconds to debounce button presses
        """
        self.state_manager = state_manager
        self.touch_pin = touch_pin
        self.debounce_time = debounce_time
        self.button_callback = None
        self.last_press_time = 0
        self.initialized = False
    
    def setup(self):
        """Set up the GPIO pins"""
        if not RPI_AVAILABLE:
            logger.warning("RPi.GPIO not available - running in simulation mode")
            return
        
        # Set up GPIO using BCM numbering
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.touch_pin, GPIO.IN)
        
        # Add event detection for both rising and falling edges
        GPIO.add_event_detect(
            self.touch_pin, 
            GPIO.RISING, 
            callback=self._handle_touch, 
            bouncetime=int(self.debounce_time * 1000)
        )
        
        self.initialized = True
        logger.info(f"GPIO initialized with touch sensor on pin {self.touch_pin}")
    
    def register_button_callback(self, callback):
        """
        Register a callback function to be called when the button is pressed
        
        Args:
            callback: Function to be called when the button is pressed
        """
        self.button_callback = callback
        logger.info("Button callback registered")
    
    def _handle_touch(self, channel):
        """
        Handle touch event from GPIO
        
        Args:
            channel: GPIO channel that triggered the event
        """
        current_time = time.time()
        
        # Debounce the button
        if current_time - self.last_press_time < self.debounce_time:
            return
        
        self.last_press_time = current_time
        logger.info(f"Touch detected on pin {channel}")
        
        if self.button_callback:
            self.button_callback()
    
    def cleanup(self):
        """Clean up GPIO resources"""
        if RPI_AVAILABLE and self.initialized:
            GPIO.cleanup()
            logger.info("GPIO resources cleaned up")

    def __del__(self):
        """Destructor to ensure GPIO resources are cleaned up"""
        self.cleanup()


# Simulation class for testing without Raspberry Pi hardware
class SimulatedGPIOController(GPIOController):
    """Simulated GPIO controller for testing without hardware"""
    
    def setup(self):
        """Set up the simulated GPIO"""
        self.initialized = True
        logger.info("Simulated GPIO initialized")
    
    def simulate_touch(self):
        """Simulate a touch event"""
        logger.info("Simulated touch event")
        if self.button_callback:
            self.button_callback()
    
    def cleanup(self):
        """Clean up simulated GPIO resources"""
        logger.info("Simulated GPIO resources cleaned up") 