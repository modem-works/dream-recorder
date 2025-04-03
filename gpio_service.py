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
    args = parser.parse_args()
    
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
    
    # Initialize and start the GPIO controller
    controller = GPIOController(touch_pin=args.pin)
    controller.set_callback(touch_callback)
    
    logger.info(f"GPIO Service started. Touch sensor on pin {args.pin}")
    logger.info("Press Ctrl+C to exit")
    
    try:
        controller.start_monitoring()
    except KeyboardInterrupt:
        logger.info("GPIO Service shutting down...")
    finally:
        controller.cleanup()

if __name__ == "__main__":
    main() 