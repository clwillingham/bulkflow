import logging
import sys

def setup_logging(name: str) -> logging.Logger:
    """Configure logging with both file and console handlers"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('import.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(name)
