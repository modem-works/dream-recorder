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
from dotenv import load_dotenv
from scripts.env_check import check_required_env_vars

# Load environment variables and check they're all set
load_dotenv()
check_required_env_vars()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Touch pattern configuration
class TouchPattern(Enum):
    SINGLE_TAP = 1
    DOUBLE_TAP = 2

class GPIOController:
    """Controller for GPIO interactions with hardware components."""
    
    def __init__(self, pin=None, debounce_time=None, sampling_rate=None):
        """
        Initialize the GPIO controller.
        
        Args:
            pin (int): GPIO pin number for the touch sensor
            debounce_time (float): Minimum time between state changes
            sampling_rate (float): How often to sample the pin state
        """
        self.pin = pin or int(os.getenv('GPIO_PIN'))
        self.debounce_time = debounce_time or float(os.getenv('GPIO_DEBOUNCE_TIME'))
        self.sampling_rate = sampling_rate or float(os.getenv('GPIO_SAMPLING_RATE'))
        self.is_running = False
        self.callbacks = {}
        
        # Touch detection state
        self.last_state = None
        self.last_change_time = 0
        self.press_start_time = 0
        self.last_tap_time = 0
        self.tap_count = 0
        
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
    
    def start_monitoring(self, single_tap_max=None, double_tap_max_interval=None):
        """
        Start monitoring for touch sensor events with specific pattern detection.
        
        Args:
            single_tap_max (float): Maximum duration for a single tap
            double_tap_max_interval (float): Maximum interval between taps for a double tap
        """
        self.single_tap_max = single_tap_max or float(os.getenv('GPIO_SINGLE_TAP_MAX_DURATION'))
        self.double_tap_max_interval = double_tap_max_interval or float(os.getenv('GPIO_DOUBLE_TAP_MAX_INTERVAL'))
        self.is_running = True
        logger.info("Starting GPIO monitoring loop")
        
        try:
            while self.is_running:
                current_state = self.GPIO.input(self.pin) == self.GPIO.HIGH
                current_time = time.time()
                
                if current_state != self.last_state:
                    if current_time - self.last_change_time > self.debounce_time:
                        self.last_change_time = current_time
                        self.last_state = current_state

                        if current_state:  # Button pressed
                            self.press_start_time = current_time
                        else:  # Button released
                            press_duration = current_time - self.press_start_time
                            
                            if press_duration <= self.single_tap_max:
                                self.tap_count += 1
                                if self.tap_count == 1:
                                    self.last_tap_time = current_time
                                elif self.tap_count == 2:
                                    if current_time - self.last_tap_time <= self.double_tap_max_interval:
                                        if TouchPattern.DOUBLE_TAP in self.callbacks:
                                            self.callbacks[TouchPattern.DOUBLE_TAP]()
                                    self.tap_count = 0

                # Check for single tap timeout
                if self.tap_count == 1 and current_time - self.last_tap_time > self.double_tap_max_interval:
                    if TouchPattern.SINGLE_TAP in self.callbacks:
                        self.callbacks[TouchPattern.SINGLE_TAP]()
                    self.tap_count = 0
                
                # Sleep for a bit to reduce CPU usage
                time.sleep(self.sampling_rate)
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, stopping")
        except Exception as e:
            if logger:
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
    parser.add_argument('--flask-url', default=os.getenv('GPIO_FLASK_URL'), 
                        help=f'Base URL of the Flask application (default: {os.getenv("GPIO_FLASK_URL")})')
    parser.add_argument('--single-tap-endpoint', default=os.getenv('GPIO_SINGLE_TAP_ENDPOINT'),
                        help=f'Endpoint for single tap (default: {os.getenv("GPIO_SINGLE_TAP_ENDPOINT")})')
    parser.add_argument('--double-tap-endpoint', default=os.getenv('GPIO_DOUBLE_TAP_ENDPOINT'),
                        help=f'Endpoint for double tap (default: {os.getenv("GPIO_DOUBLE_TAP_ENDPOINT")})')
    parser.add_argument('--pin', type=int, default=os.getenv('GPIO_PIN'),
                        help=f'GPIO pin for touch sensor (default: {os.getenv("GPIO_PIN")})')
    parser.add_argument('--single-tap-max', type=float, default=os.getenv('GPIO_SINGLE_TAP_MAX_DURATION'),
                        help=f'Maximum duration for a single tap in seconds (default: {os.getenv("GPIO_SINGLE_TAP_MAX_DURATION")})')
    parser.add_argument('--double-tap-max-interval', type=float, default=os.getenv('GPIO_DOUBLE_TAP_MAX_INTERVAL'),
                        help=f'Maximum interval between taps for a double tap in seconds (default: {os.getenv("GPIO_DOUBLE_TAP_MAX_INTERVAL")})')
    parser.add_argument('--debounce-time', type=float, default=os.getenv('GPIO_DEBOUNCE_TIME'),
                        help=f'Debounce time in seconds (default: {os.getenv("GPIO_DEBOUNCE_TIME")})')
    parser.add_argument('--sampling-rate', type=float, default=os.getenv('GPIO_SAMPLING_RATE'),
                        help=f'Sampling rate in seconds (default: {os.getenv("GPIO_SAMPLING_RATE")})')
    parser.add_argument('--startup-delay', type=int, default=int(os.getenv('GPIO_STARTUP_DELAY')),
                        help=f'Delay in seconds before starting (default: {os.getenv("GPIO_STARTUP_DELAY")})')
    args = parser.parse_args()
    
    # Add a small delay at startup to let system initialize
    logger.info(f"Starting up, waiting {args.startup_delay} seconds for system initialization...")
    time.sleep(args.startup_delay)
    
    # Construct the full URLs to call
    single_tap_url = f"{args.flask_url}{args.single_tap_endpoint}"
    double_tap_url = f"{args.flask_url}{args.double_tap_endpoint}"
    
    logger.info(f"Will send touch events to:")
    logger.info(f"  Single tap: {single_tap_url}")
    logger.info(f"  Double tap: {double_tap_url}")
    
    # Define the callback functions for each touch pattern
    def single_tap_callback():
        logger.info("Single tap detected, sending to server...")
        try:
            response = requests.post(single_tap_url)
            if response.status_code == 200:
                logger.info("Single tap processed successfully")
            else:
                if logger:
                    logger.error(f"Failed to process single tap: {response.status_code} - {single_tap_url}")
        except Exception as e:
            if logger:
                logger.error(f"Error sending single tap: {str(e)}")
    
    def double_tap_callback():
        logger.info("Double tap detected, sending to server...")
        try:
            response = requests.post(double_tap_url)
            if response.status_code == 200:
                logger.info("Double tap processed successfully")
            else:
                if logger:
                    logger.error(f"Failed to process double tap: {response.status_code} - {double_tap_url}")
        except Exception as e:
            if logger:
                logger.error(f"Error sending double tap: {str(e)}")
    
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
            
            logger.info(f"GPIO Service started successfully. Touch sensor on pin {args.pin}")
            break
        except Exception as e:
            if logger:
                logger.error(f"Error initializing GPIO (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                if logger:
                    logger.error("Failed to initialize GPIO after multiple attempts. Exiting.")
                sys.exit(1)
    
    logger.info("Press Ctrl+C to exit")
    
    try:
        controller.start_monitoring(
            single_tap_max=args.single_tap_max,
            double_tap_max_interval=args.double_tap_max_interval
        )
    except KeyboardInterrupt:
        logger.info("GPIO Service shutting down...")
    except Exception as e:
        if logger:
            logger.error(f"Error during GPIO monitoring: {str(e)}")
    finally:
        if controller:
            controller.cleanup()

if __name__ == "__main__":
    main() 