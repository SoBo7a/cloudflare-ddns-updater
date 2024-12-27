import os
import gzip
import shutil
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timedelta

def setup_logger(log_file):
    """
    Configures the logger with a timed rotating handler.

    Args:
        log_file (str): Path to the log file.

    Returns:
        logging.Logger: Configured logger instance.
    """
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, log_level, "INFO")
        
    logger = logging.getLogger(__name__)
    logger.setLevel(level)

    # TimedRotatingFileHandler to rotate every monday
    handler = TimedRotatingFileHandler(log_file, when="W0", interval=1, backupCount=0)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    handler.namer = namer
    logger.addHandler(handler)
    
    return logger


def namer(name):
    """Rename function to add the timestamp to the log file."""
    return name.replace(".log", "") + ".log"


def compress_old_logs(log_dir, age_threshold=5, keep_count=3):
    """
    Compress log files older than `age_threshold` minutes to .gz format,
    but only if there are more than `keep_count` uncompressed and renamed logs.
    
    Args:
        log_dir (str): The directory where the logs are stored.
        age_threshold (int): The age in minutes after which the logs should be compressed.
        keep_count (int): The number of most recent logs to keep uncompressed.
    """
    age_limit = datetime.now() - timedelta(minutes=age_threshold)
    renamed_logs = []

    # Gather all renamed log files (those with timestamp in the filename)
    for file_name in os.listdir(log_dir):
        file_path = os.path.join(log_dir, file_name)

        # Only consider files with the .log extension
        if file_name.endswith('.log'):
            try:
                # Extract the timestamp from the filename (i.e., after the first dot)
                timestamp_str = file_name.split('.')[1]
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d_%H-%M')
                renamed_logs.append((timestamp, file_path))
            except (ValueError, IndexError):
                # Skip files with unexpected naming
                continue

    # Sort logs by timestamp (oldest first)
    renamed_logs.sort(key=lambda x: x[0])

    # If there are more logs than the `keep_count`, compress the oldest ones
    if len(renamed_logs) > keep_count:
        # Compress all logs older than the age limit
        for timestamp, file_path in renamed_logs[:-keep_count]:  # Skip the `keep_count` newest logs
            if timestamp < age_limit:
                with open(file_path, 'rb') as f_in:
                    with gzip.open(file_path + '.gz', 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(file_path)  # Remove the original file after compression
      
                
def delete_old_gz_logs(log_dir, age_threshold=10, keep_count=4):
    """
    Delete .gz log files older than `age_threshold` minutes, but ensure at least `keep_count` .gz files remain.
    
    Args:
        log_dir (str): The directory where the .gz log files are stored.
        age_threshold (int): The age in minutes after which the .gz files should be deleted.
        keep_count (int): The number of most recent .gz files to keep.
    """
    age_limit = datetime.now() - timedelta(minutes=age_threshold)
    gz_files = []

    # Gather all .gz files in the log directory
    for file_name in os.listdir(log_dir):
        file_path = os.path.join(log_dir, file_name)
        
        if file_name.endswith('.gz'):
            file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
            gz_files.append((file_mtime, file_path))

    # Sort .gz files by modification time (oldest first)
    gz_files.sort(key=lambda x: x[0])

    # Only delete files if there are more than `keep_count` .gz files
    if len(gz_files) > keep_count:
        # Delete .gz files older than the age limit, starting from the oldest
        for mtime, file_path in gz_files[:-keep_count]:  # Skip the `keep_count` newest .gz files
            if mtime < age_limit:
                os.remove(file_path)
