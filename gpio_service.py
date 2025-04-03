#!/usr/bin/env python3
"""
GPIO Service for Dream Recorder

This script runs the GPIO controller in a standalone process,
communicating with the main Flask application via a simple HTTP request.
It detects different touch patterns and calls different endpoints.
"""

import time
import logging
import requests
import argparse
import os
import sys
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Touch pattern configuration
class TouchPattern(Enum):
    SINGLE_TAP = 1
    DOUBLE_TAP = 2
    LONG_PRESS = 3
    LONG_PRESS_RELEASE = 4

# Default configuration (can be overridden via command-line arguments)
DEFAULT_CONFIG = {
    # GPIO pin configuration
    'pin': 4,
    
    # Flask API endpoints
    'flask_url': 'http://localhost:5000',
    'single_tap_endpoint': '/api/wake_device',
    'double_tap_endpoint': '/api/show_previous_dream',
    'long_press_endpoint': '/api/trigger_recording',
    'long_press_release_endpoint': '/api/stop_recording',
    
    # Touch pattern timing configuration (in seconds)
    'single_tap_max_duration': 0.5,         # Maximum duration for a single tap
    'double_tap_max_interval': 0.7,         # Maximum interval between two taps for a double tap
    'long_press_min_duration': 1.5,         # Minimum duration for a long press
    
    # Other configuration
    'debounce_time': 0.05,                  # Minimum time between state changes
    'startup_delay': 2,                     # Delay before starting
    'sampling_rate': 0.01,                  # How often to sample the pin state (seconds)
}

class GPIOController:
    """Controller for GPIO interactions with hardware components."""
    
    def __init__(self, pin, debounce_time=0.05, sampling_rate=0.01):
        """
        Initialize the GPIO controller.
        
        Args:
            pin (int): GPIO pin number for the touch sensor
            debounce_time (float): Minimum time between state changes
            sampling_rate (float): How often to sample the pin state
        """
        self.pin = pin
        self.debounce_time = debounce_time
        self.sampling_rate = sampling_rate
        self.is_running = False
        self.callbacks = {}
        
        # Touch detection state
        self.last_state = False
        self.last_change_time = 0
        self.press_start_time = 0
        self.last_tap_time = 0
        self.tap_count = 0
        self.long_press_triggered = False
        
        # Import GPIO here for better error handling
        import RPi.GPIO as GPIO
        self.GPIO = GPIO
        
        # Set up GPIO
        self.GPIO.setmode(self.GPIO.BCM)
        self.GPIO.setup(self.pin, self.GPIO.IN, pull_up_down=self.GPIO.PUD_DOWN)
        logger.info(f"GPIO Controller initialized with touch sensor on pin {self.pin}")
    
    def register_callback(self, pattern, callback_func):
        """
        Register a callback function for a specific touch pattern.
        
        Args:
            pattern (TouchPattern): The touch pattern to detect
            callback_func (callable): Function to call when pattern is detected
        """
        self.callbacks[pattern] = callback_func
        logger.info(f"Registered callback for {pattern.name}")
    
    def start_monitoring(self, single_tap_max=0.5, double_tap_max_interval=0.7, long_press_min=1.5):
        """
        Start monitoring for touch sensor events with specific pattern detection.
        
        Args:
            single_tap_max (float): Maximum duration for a single tap
            double_tap_max_interval (float): Maximum interval between taps for a double tap
            long_press_min (float): Minimum duration for a long press
        """
        self.is_running = True
        logger.info("Starting GPIO monitoring loop")
        
        try:
            while self.is_running:
                current_state = self.GPIO.input(self.pin) == self.GPIO.HIGH
                current_time = time.time()
                
                # State changed from LOW to HIGH (touch started)
                if current_state and not self.last_state:
                    # Debounce
                    if current_time - self.last_change_time > self.debounce_time:
                        self.press_start_time = current_time
                        self.last_change_time = current_time
                        self.long_press_triggered = False
                        logger.debug("Touch started")
                
                # Check for long press while finger is still down
                elif current_state and self.last_state:
                    press_duration = current_time - self.press_start_time
                    # Long press threshold reached and not yet triggered
                    if press_duration >= long_press_min and not self.long_press_triggered:
                        logger.info("Long press detected!")
                        self.long_press_triggered = True
                        if TouchPattern.LONG_PRESS in self.callbacks:
                            self.callbacks[TouchPattern.LONG_PRESS]()
                
                # State changed from HIGH to LOW (touch ended)
                elif not current_state and self.last_state:
                    # Debounce
                    if current_time - self.last_change_time > self.debounce_time:
                        self.last_change_time = current_time
                        press_duration = current_time - self.press_start_time
                        logger.debug(f"Touch ended, duration: {press_duration:.2f}s")
                        
                        # If we had a long press and now releasing, call the release callback
                        if self.long_press_triggered:
                            logger.info("Long press released!")
                            if TouchPattern.LONG_PRESS_RELEASE in self.callbacks:
                                self.callbacks[TouchPattern.LONG_PRESS_RELEASE]()
                        # Check if it was a short tap (and not part of a long press)
                        elif press_duration < single_tap_max:
                            # Check for potential double tap
                            if current_time - self.last_tap_time < double_tap_max_interval:
                                # Double tap detected
                                logger.info("Double tap detected!")
                                self.tap_count = 0
                                self.last_tap_time = 0
                                if TouchPattern.DOUBLE_TAP in self.callbacks:
                                    self.callbacks[TouchPattern.DOUBLE_TAP]()
                            else:
                                # First tap of potential double tap
                                self.last_tap_time = current_time
                                self.tap_count = 1
                                # Schedule a single tap with delay to allow for double tap
                                self.single_tap_scheduled = True
                                self.single_tap_time = current_time
                
                # Check for scheduled single tap that wasn't part of a double tap
                if self.tap_count == 1 and current_time - self.last_tap_time > double_tap_max_interval:
                    logger.info("Single tap detected!")
                    self.tap_count = 0
                    self.last_tap_time = 0
                    if TouchPattern.SINGLE_TAP in self.callbacks:
                        self.callbacks[TouchPattern.SINGLE_TAP]()
                
                # Update the last state
                self.last_state = current_state
                
                # Sleep for a bit to reduce CPU usage
                time.sleep(self.sampling_rate)
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, stopping")
        except Exception as e:
            logger.error(f"Error in GPIO monitoring: {str(e)}")
        finally:
            self.cleanup()
    
    def stop_monitoring(self):
        """Stop monitoring for touch sensor events."""
        self.is_running = False
        logger.info("Stopping GPIO monitoring")
    
    def cleanup(self):
        """Clean up GPIO resources."""
        try:
            self.GPIO.cleanup()
            logger.info("GPIO resources cleaned up")
        except:
            pass

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='GPIO Service for Dream Recorder')
    parser.add_argument('--flask-url', default=DEFAULT_CONFIG['flask_url'], 
                        help=f'Base URL of the Flask application (default: {DEFAULT_CONFIG["flask_url"]})')
    parser.add_argument('--single-tap-endpoint', default=DEFAULT_CONFIG['single_tap_endpoint'],
                        help=f'Endpoint for single tap (default: {DEFAULT_CONFIG["single_tap_endpoint"]})')
    parser.add_argument('--double-tap-endpoint', default=DEFAULT_CONFIG['double_tap_endpoint'],
                        help=f'Endpoint for double tap (default: {DEFAULT_CONFIG["double_tap_endpoint"]})')
    parser.add_argument('--long-press-endpoint', default=DEFAULT_CONFIG['long_press_endpoint'],
                        help=f'Endpoint for long press (default: {DEFAULT_CONFIG["long_press_endpoint"]})')
    parser.add_argument('--long-press-release-endpoint', default=DEFAULT_CONFIG['long_press_release_endpoint'],
                        help=f'Endpoint for long press release (default: {DEFAULT_CONFIG["long_press_release_endpoint"]})')
    parser.add_argument('--pin', type=int, default=DEFAULT_CONFIG['pin'],
                        help=f'GPIO pin for touch sensor (default: {DEFAULT_CONFIG["pin"]})')
    parser.add_argument('--single-tap-max', type=float, default=DEFAULT_CONFIG['single_tap_max_duration'],
                        help=f'Maximum duration for a single tap in seconds (default: {DEFAULT_CONFIG["single_tap_max_duration"]})')
    parser.add_argument('--double-tap-max-interval', type=float, default=DEFAULT_CONFIG['double_tap_max_interval'],
                        help=f'Maximum interval between taps for a double tap in seconds (default: {DEFAULT_CONFIG["double_tap_max_interval"]})')
    parser.add_argument('--long-press-min', type=float, default=DEFAULT_CONFIG['long_press_min_duration'],
                        help=f'Minimum duration for a long press in seconds (default: {DEFAULT_CONFIG["long_press_min_duration"]})')
    parser.add_argument('--debounce-time', type=float, default=DEFAULT_CONFIG['debounce_time'],
                        help=f'Debounce time in seconds (default: {DEFAULT_CONFIG["debounce_time"]})')
    parser.add_argument('--sampling-rate', type=float, default=DEFAULT_CONFIG['sampling_rate'],
                        help=f'Sampling rate in seconds (default: {DEFAULT_CONFIG["sampling_rate"]})')
    parser.add_argument('--startup-delay', type=int, default=DEFAULT_CONFIG['startup_delay'],
                        help=f'Delay in seconds before starting (default: {DEFAULT_CONFIG["startup_delay"]})')
    args = parser.parse_args()
    
    # Add a small delay at startup to let system initialize
    logger.info(f"Starting up, waiting {args.startup_delay} seconds for system initialization...")
    time.sleep(args.startup_delay)
    
    # Construct the full URLs to call
    single_tap_url = f"{args.flask_url}{args.single_tap_endpoint}"
    double_tap_url = f"{args.flask_url}{args.double_tap_endpoint}"
    long_press_url = f"{args.flask_url}{args.long_press_endpoint}"
    long_press_release_url = f"{args.flask_url}{args.long_press_release_endpoint}"
    
    logger.info(f"Will send touch events to:")
    logger.info(f"  Single tap: {single_tap_url}")
    logger.info(f"  Double tap: {double_tap_url}")
    logger.info(f"  Long press: {long_press_url}")
    logger.info(f"  Long press release: {long_press_release_url}")
    
    # Define the callback functions for each touch pattern
    def single_tap_callback():
        logger.info("Single tap detected, waking device...")
        try:
            response = requests.post(single_tap_url)
            if response.status_code == 200:
                logger.info("Wake device triggered successfully")
            else:
                logger.error(f"Failed to trigger wake device: {response.status_code}")
        except Exception as e:
            logger.error(f"Error triggering wake device: {str(e)}")
    
    def double_tap_callback():
        logger.info("Double tap detected, showing previous dream...")
        try:
            response = requests.post(double_tap_url)
            if response.status_code == 200:
                logger.info("Show previous dream triggered successfully")
            else:
                logger.error(f"Failed to trigger show previous dream: {response.status_code}")
        except Exception as e:
            logger.error(f"Error triggering show previous dream: {str(e)}")
    
    def long_press_callback():
        logger.info("Long press detected, triggering recording...")
        try:
            response = requests.post(long_press_url)
            if response.status_code == 200:
                logger.info("Recording triggered successfully")
            else:
                logger.error(f"Failed to trigger recording: {response.status_code}")
        except Exception as e:
            logger.error(f"Error triggering recording: {str(e)}")
    
    def long_press_release_callback():
        logger.info("Long press released, stopping recording...")
        try:
            response = requests.post(long_press_release_url)
            if response.status_code == 200:
                logger.info("Recording stopped successfully")
            else:
                logger.error(f"Failed to stop recording: {response.status_code}")
        except Exception as e:
            logger.error(f"Error stopping recording: {str(e)}")
    
    # Initialize GPIO with retry logic
    max_retries = 3
    retry_delay = 2
    controller = None
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Initializing GPIO controller (attempt {attempt + 1}/{max_retries})...")
            controller = GPIOController(
                pin=args.pin, 
                debounce_time=args.debounce_time,
                sampling_rate=args.sampling_rate
            )
            
            # Register callbacks for each touch pattern
            controller.register_callback(TouchPattern.SINGLE_TAP, single_tap_callback)
            controller.register_callback(TouchPattern.DOUBLE_TAP, double_tap_callback)
            controller.register_callback(TouchPattern.LONG_PRESS, long_press_callback)
            controller.register_callback(TouchPattern.LONG_PRESS_RELEASE, long_press_release_callback)
            
            logger.info(f"GPIO Service started successfully. Touch sensor on pin {args.pin}")
            break
        except Exception as e:
            logger.error(f"Error initializing GPIO (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("Failed to initialize GPIO after multiple attempts. Exiting.")
                sys.exit(1)
    
    logger.info("Press Ctrl+C to exit")
    
    try:
        controller.start_monitoring(
            single_tap_max=args.single_tap_max,
            double_tap_max_interval=args.double_tap_max_interval,
            long_press_min=args.long_press_min
        )
    except KeyboardInterrupt:
        logger.info("GPIO Service shutting down...")
    except Exception as e:
        logger.error(f"Error during GPIO monitoring: {str(e)}")
    finally:
        if controller:
            controller.cleanup()

if __name__ == "__main__":
    main() 