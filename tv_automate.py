import logging
import subprocess
import sys
import time
from datetime import datetime

import schedule

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("tv_scheduler.log"),
        logging.StreamHandler(sys.stdout),
    ],
)


class TVController:
    def __init__(self):
        self.device_id = "0"
        self.cec_client = "cec-client"

    def execute_cec_command(self, command):
        """Execute a CEC command and handle potential errors"""
        try:
            full_command = f'echo "{command}" | {self.cec_client} -s -d 1'
            process = subprocess.run(
                full_command, shell=True, capture_output=True, text=True, timeout=30
            )

            if process.returncode != 0:
                logging.error(f"Command failed: {full_command}")
                logging.error(f"Error output: {process.stderr}")
                return False

            logging.info(f"Successfully executed command: {command}")
            return True

        except subprocess.TimeoutExpired:
            logging.error(f"Command timed out: {command}")
            return False
        except Exception as e:
            logging.error(f"Error executing command: {command}")
            logging.error(f"Error details: {str(e)}")
            return False

    def turn_on_tv(self):
        """Turn on TV and switch to default HDMI input"""
        logging.info("Attempting to turn on TV...")

        # Turn on TV
        if not self.execute_cec_command(f"on {self.device_id}"):
            logging.error("Failed to turn on TV")
            return False

        # Wait for TV to fully power on
        time.sleep(15)

        # Switch to default HDMI input
        if not self.execute_cec_command("tx 1F:82:10:00"):
            logging.error("Failed to switch HDMI input")
            return False

        logging.info("TV turned on and input switched successfully")
        return True

    def turn_off_tv(self):
        """Turn off TV"""
        logging.info("Attempting to turn off TV...")

        if not self.execute_cec_command(f"standby {self.device_id}"):
            logging.error("Failed to turn off TV")
            return False

        logging.info("TV turned off successfully")
        return True


def setup_schedule(controller):
    """Set up the weekly schedule"""
    # Clear any existing schedules
    schedule.clear()

    # Schedule for Monday to Thursday and Sunday
    weekday_schedule = ["monday", "tuesday", "wednesday", "thursday", "sunday"]
    for day in weekday_schedule:
        schedule.every().day.at("09:30").do(controller.turn_on_tv).tag(day)
        schedule.every().day.at("17:45").do(controller.turn_off_tv).tag(day)

    # Schedule for Friday and Saturday
    weekend_schedule = ["friday", "saturday"]
    for day in weekend_schedule:
        schedule.every().day.at("08:30").do(controller.turn_on_tv).tag(day)
        schedule.every().day.at("21:45").do(controller.turn_off_tv).tag(day)

    logging.info("Schedule setup completed")


def main():
    """Main function to run the TV scheduler"""
    try:
        controller = TVController()
        setup_schedule(controller)

        logging.info("TV scheduler started")

        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check schedule every minute

            except Exception as e:
                logging.error(f"Error in scheduler loop: {str(e)}")
                time.sleep(60)  # Wait before retrying

    except KeyboardInterrupt:
        logging.info("TV scheduler stopped by user")
    except Exception as e:
        logging.error(f"Fatal error in main loop: {str(e)}")
        raise


if __name__ == "__main__":
    main()
