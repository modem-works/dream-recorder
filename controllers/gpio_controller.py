#!/usr/bin/env python3
"""
GPIO Controller for Dream Recorder

This module manages the GPIO interactions with hardware components,
particularly the capacitive touch sensor (TTP223B) that triggers
recording actions.
"""

import RPi.GPIO as GPIO
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the GPIO pin number where the touch sensor is connected
TOUCH_PIN = 4  # GPIO pin for the capacitive touch sensor

class GPIOController:
    """Controller for GPIO interactions with hardware components."""
    
    def __init__(self, touch_pin=TOUCH_PIN):
        """
        Initialize the GPIO controller.
        
        Args:
            touch_pin (int): GPIO pin number for the touch sensor
        """
        self.touch_pin = touch_pin
        self.is_running = False
        self.callback = None
        
        # Set up GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.touch_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        
        logger.info(f"GPIO Controller initialized with touch sensor on pin {self.touch_pin}")
    
    def set_callback(self, callback_func):
        """
        Set a callback function to be called when touch is detected.
        
        Args:
            callback_func (callable): Function to call when touch is detected
        """
        self.callback = callback_func
        logger.info("Callback function registered")
    
    def start_monitoring(self):
        """Start monitoring for touch sensor events."""
        self.is_running = True
        logger.info("Starting GPIO monitoring loop")
        
        try:
            while self.is_running:
                if GPIO.input(self.touch_pin) == GPIO.HIGH:
                    logger.info("Touch detected!")
                    if self.callback:
                        self.callback()
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.cleanup()
        except Exception as e:
            logger.error(f"Error in GPIO monitoring: {str(e)}")
            self.cleanup()
    
    def stop_monitoring(self):
        """Stop monitoring for touch sensor events."""
        self.is_running = False
        logger.info("Stopping GPIO monitoring")
    
    def cleanup(self):
        """Clean up GPIO resources."""
        GPIO.cleanup()
        logger.info("GPIO resources cleaned up")


# Simple standalone test if file is run directly
if __name__ == "__main__":
    def test_callback():
        print("Touch callback triggered!")
    
    controller = GPIOController()
    controller.set_callback(test_callback)
    print("Touch the sensor to test (Ctrl+C to exit)...")
    controller.start_monitoring() 