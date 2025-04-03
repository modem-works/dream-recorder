#!/usr/bin/env python3
"""
GPIO Service for Dream Recorder

This script runs the GPIO controller in a standalone process,
communicating with the main Flask application via a simple HTTP request.
"""

import time
import logging
import requests
import argparse
import os
import sys
from controllers.gpio_controller import GPIOController

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='GPIO Service for Dream Recorder')
    parser.add_argument('--flask-url', default='http://localhost:5000', 
                        help='URL of the Flask application')
    parser.add_argument('--endpoint', default='/api/trigger_recording',
                        help='Endpoint to call when touch is detected')
    parser.add_argument('--pin', type=int, default=4,
                        help='GPIO pin for touch sensor (default: 4)')
    parser.add_argument('--startup-delay', type=int, default=2,
                        help='Delay in seconds before starting (default: 2)')
    args = parser.parse_args()
    
    # Add a small delay at startup to let system initialize
    logger.info(f"Starting up, waiting {args.startup_delay} seconds for system initialization...")
    time.sleep(args.startup_delay)
    
    # Construct the full URL to call
    trigger_url = f"{args.flask_url}{args.endpoint}"
    logger.info(f"Will send touch events to: {trigger_url}")
    
    # Define the callback function
    def touch_callback():
        logger.info("Touch detected, triggering recording...")
        try:
            response = requests.post(trigger_url)
            if response.status_code == 200:
                logger.info("Recording triggered successfully")
            else:
                logger.error(f"Failed to trigger recording: {response.status_code}")
        except Exception as e:
            logger.error(f"Error triggering recording: {str(e)}")
    
    # Initialize GPIO with retry logic
    max_retries = 3
    retry_delay = 2
    controller = None
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Initializing GPIO controller (attempt {attempt + 1}/{max_retries})...")
            controller = GPIOController(touch_pin=args.pin)
            controller.set_callback(touch_callback)
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
        controller.start_monitoring()
    except KeyboardInterrupt:
        logger.info("GPIO Service shutting down...")
    except Exception as e:
        logger.error(f"Error during GPIO monitoring: {str(e)}")
    finally:
        if controller:
            controller.cleanup()

if __name__ == "__main__":
    main() 