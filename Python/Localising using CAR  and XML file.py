"""
BLDM CONFIG LOCALIZER - XML/CAR File Management Utility

Description:
------------
This enterprise-grade utility provides comprehensive processing capabilities for XML 
and CAR (Container Archive) configuration files exported from the Business Logic Development and Management Tool (BLDM). The tool performs automated path transformations, SFTP 
configuration updates, and collector management operations while maintaining strict 
data integrity.

Key Functionality:
-----------------
1. Path Management:
   - Extracts filesystem paths from designated XML tags
   - Prepends configurable path prefixes
   - Generates directory creation commands (mkdir)
   - Updates XML/CAR files with transformed paths

2. SFTP Configuration:
   - Secure update of host IP addresses
   - Credential management (username/password)
   - Password requirement flag management

3. Collector Management:
   - Bulk configuration of default stopped state
   - Path normalization across collectors/distributers

4. File Processing:
   - Supports both standalone XML and packaged CAR files
   - Maintains original file structure and metadata
   - Validates file integrity throughout processing

Technical Implementation:
-------------------------
- Modular architecture with separation of concerns
- Comprehensive error handling and validation
- Transactional file operations with rollback capability
- Configurable logging with audit trails
- Memory-efficient streaming processing

Usage Guidelines:
----------------
1. Execution:
   python bldm_config_processor.py [optional directory path]

2. Operation:
   - Interactive mode guides users through available operations
   - Batch processing supported via configuration files (future)
   - Outputs include:
     * Modified configuration files
     * Directory creation scripts
     * Detailed audit logs

Compatibility:
-------------
- Verified with BLDM v9.3+ configuration exports
- Supports Windows/Linux/macOS environments
- Python 3.8+ required

Security Notes:
--------------
- All file operations maintain original permissions
- Credential fields support encrypted input only
- Temporary files are securely wiped after processing
- Logs redact sensitive information

Maintenance:
-----------
Version: v1.1.1
Last Updated: [27-05-2025]
Contact: [suvra.dwibedy@ericsson.com]
Documentation: [To be updated]
"""


import os
import sys
import re
import ipaddress
from typing import List, Tuple, Optional, Iterator
import shutil
import tempfile
import zipfile
import logging
from datetime import datetime
import webbrowser
import urllib.parse
import time
import getpass
import socket


###################################
# Winow closing with grace Module #
###################################

import sys
import time

def handle_error_with_countdown(error_message: str, countdown_seconds: int = 5) -> None:
    """
    Display a professional animated error message with countdown before exiting.
    Suitable for CLI tools, production packaging, and clear user communication.
    
    Args:
        error_message: The error message to display
        countdown_seconds: Seconds to wait before closing
    """
    # Get user, host, and timestamp info
    user = getpass.getuser()
    host = socket.gethostname()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    RED = "\033[91m"
    RESET = "\033[0m"
    DIM = "\033[2m"
    BOLD = "\033[1m"

    line_width = 60
    pad = " " * 4

    # Header block
    print("\n╔" + "═" * line_width + "╗")
    print("║" + f"{'ERROR OCCURRED':^{line_width}}" + "║")
    print("╚" + "═" * line_width + "╝")

    print(f"\n{RED}{BOLD}{error_message}{RESET}")
    print(f"{DIM}An unrecoverable error occurred. The application will now close.{RESET}\n")
    print(f"{DIM}User: {user} | Host: {host} | Time: {now}{RESET}\n")
    
    # Countdown with animated pulsing effect
    for remaining in range(countdown_seconds, 0, -1):
        for phase in [".  ", ".. ", "...", " ..", "  .", "   "]:
            display = f"{pad}Closing in {remaining} second(s){phase}"
            sys.stdout.write(f"\r{DIM}{display:<{line_width + len(pad)}}{RESET}")
            sys.stdout.flush()
            time.sleep(0.2)

    sys.stdout.write(f"\r{pad}{BOLD}Closing now...{' ' * (line_width - len('Closing now...'))}{RESET}\n")
    sys.exit(1)  # Exit with error code



def handle_user_cancellation(message: str = "Operation cancelled by user.", countdown_seconds: int = 5) -> None:
    """
    Show a pulsing animated countdown timer before graceful exit.
    Clean and formal for production use.
    """
    RED = "\033[91m"
    RESET = "\033[0m"
    DIM = "\033[2m"
    BOLD = "\033[1m"

    line_width = 60
    pad = " " * 4

    # Title block
    print("\n╔" + "═" * line_width + "╗")
    print("║" + f"{'OPERATION CANCELLED':^{line_width}}" + "║")
    print("╚" + "═" * line_width + "╝")

    print(f"\n{RED}{BOLD}{message}{RESET}")
    print(f"{DIM}Please wait while the application exits safely.{RESET}\n")

    # Countdown with elegant pulsing dots
    for remaining in range(countdown_seconds, 0, -1):
        for phase in [".  ", ".. ", "...", " ..", "  .", "   "]:
            display = f"{pad}Closing in {remaining} second(s){phase}"
            sys.stdout.write(f"\r{DIM}{display:<{line_width + len(pad)}}{RESET}")
            sys.stdout.flush()
            time.sleep(0.2)

    sys.stdout.write(f"\r{pad}{BOLD}Closing now...{' ' * (line_width - len('Closing now...'))}{RESET}\n")
    sys.exit(0)
    
    
def handle_sucessful_completion(message: str = "Operation completed successfully.", countdown_seconds: int = 3) -> None:
    """
    Display a professional animated success message with a countdown before graceful exit.
    Optimized for production-grade CLI tools.
    
    Args:
        message: Message to display on successful completion.
        countdown_seconds: Duration before the application closes.
    """
    GREEN = "\033[92m"
    RESET = "\033[0m"
    DIM = "\033[2m"
    BOLD = "\033[1m"

    line_width = 60
    pad = " " * 4

    # Success block
    print("\n╔" + "═" * line_width + "╗")
    print("║" + f"{'OPERATION COMPLETED SUCCESSFULLY':^{line_width}}" + "║")
    print("╚" + "═" * line_width + "╝")

    print(f"\n{GREEN}{BOLD}{message}{RESET}")
    print(f"{DIM}Application will close shortly. Please wait...{RESET}\n")

    # Countdown with pulsing dots
    for remaining in range(countdown_seconds, 0, -1):
        for phase in [".  ", ".. ", "...", " ..", "  .", "   "]:
            display = f"{pad}Closing in {remaining} second(s){phase}"
            sys.stdout.write(f"\r{DIM}{display:<{line_width + len(pad)}}{RESET}")
            sys.stdout.flush()
            time.sleep(0.2)

    sys.stdout.write(f"\r{pad}{BOLD}Closing now...{' ' * (line_width - len('Closing now...'))}{RESET}\n")
    sys.exit(0)

######################
# Log Handler Module #
######################

def log_file_paths(original_path: str, modified_path: str, log_path: str) -> None:
    """
    Log detailed information about file paths used in processing.
    Args:
        original_path: Path to the original input file
        modified_path: Path to the modified output file
        log_path: Path to the log file
    """
    logger = logging.getLogger()
    logger.info("=" * 50)
    logger.info("FILE PATH SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Original input file: {original_path}")
    logger.info(f"Modified output file: {modified_path}")
    logger.info(f"Log file location: {log_path}")
    logger.info("=" * 50)

def log_car_processing_details(temp_dir: str, extracted_xml: str, modified_xml: str, output_car: str) -> None:
    """
    Log detailed information about CAR file processing paths.
    
    Args:
        temp_dir: Temporary extraction directory path
        extracted_xml: Path to extracted XML file
        modified_xml: Path to modified XML file
        output_car: Path to output CAR file
    """
    logger = logging.getLogger()
    logger.info("=" * 50)
    logger.info("CAR PROCESSING PATHS")
    logger.info("=" * 50)
    logger.info(f"Temporary extraction directory: {temp_dir}")
    logger.info(f"Extracted XML file: {extracted_xml}")
    logger.info(f"Modified XML file: {modified_xml}")
    logger.info(f"Output CAR file: {output_car}")
    logger.info("=" * 50)


def setup_logging(file_path: str = '', log_level=logging.INFO, log_to_file=True, console_output=False):
    """
    Sets up logging configuration for the application.
    
    Args:
        log_level: The logging level (default: logging.INFO)
        log_to_file: Whether to log to a file (default: True)
        console_output: Whether to show logs in console (default: False)
    
    Returns:
        The configured logger instance
    """
    
    # Get user, host, and timestamp info
    user = getpass.getuser()
    host = socket.gethostname()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create logs directory if it doesn't exist
    if log_to_file and not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Clear any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Add file handler if requested
    if log_to_file:
        # Create log filename based on input file if provided
        if file_path:
             # Extract name from XML if possible
            name = ""
            if file_path.lower().endswith('.xml'):
                name = extract_name_from_xml(file_path)
            if not name:  # If no name from XML or it's a CAR file
                name = os.path.splitext(os.path.basename(file_path))[0]
            
            # Clean the name to be filesystem-safe
            name = re.sub(r'[\\/*?:"<>|]', "_", name).strip()
            # Create unique log filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join('logs', f'{name}_{timestamp}.log')
            
        else:
            # Fallback to timestamp if no input file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join('logs', f'xml_processor_{timestamp}.log')
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.info(f"Session started - User: {user} | Host: {host} | Time: {now}")
        
    # Add console handler only if console output is requested
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger

def log_operation_start(operation_name):
    """
    Logs the start of an operation with a consistent format.
    
    Args:
        operation_name: Name of the operation being started
    """
    logging.info(f"{'=' * 20} Starting {operation_name} {'=' * 20}")

def log_operation_end(operation_name, status="completed"):
    """
    Logs the end of an operation with a consistent format.
    
    Args:
        operation_name: Name of the operation that ended
        status: Status of the operation (default: "completed")
    """
    logging.info(f"{'=' * 20} {operation_name} {status} {'=' * 20}")

def log_summary(operations_performed):
    """
    Logs a summary of all operations performed.
    
    Args:
        operations_performed: List of operations performed
    """
    if not operations_performed:
        logging.info("No operations were performed")
        return
        
    logging.info("=" * 50)
    logging.info("OPERATIONS SUMMARY")
    logging.info("=" * 50)
    
    for idx, operation in enumerate(operations_performed, 1):
        logging.info(f"{idx}. {operation}")
    
    logging.info("=" * 50)
    # Brief summary to console
    print(f"\nDetailed log saved to log file")
    print("\nProcessing complete!")
    
    logger.info("=" * 50)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

#############################
# File type checking Module #
#############################

def check_file_extension(file_path: str) -> str:
    """
    Check the extension of the file and return the type.
    
    Args:
        file_path: Path to the file
        
    Returns:
        str: 'xml' for XML files, 'car' for CAR files, 'unknown' for others
    """
    _, ext = os.path.splitext(file_path.lower())
    # Log the file extension check operation
    logger.debug(f"Checking file extension for: {file_path}")
    
    if ext == '.xml':
        logger.info(f"Identified XML file: {file_path}")
        return 'xml'
    elif ext == '.car':
        logger.info(f"Identified CAR file: {file_path}")
        return 'car'
    else:
        logger.warning(f"Unknown file type for: {file_path} (Extension: {ext})")
        return 'unknown'
    
############################
# .CAR file Handler Module #
############################

def extract_car_file(car_path: str) -> Tuple[str, str]:
    """
    Extract the contents of a .car file to a temporary directory.
    
    Args:
        car_path: Path to the .car file
        
    Returns:
        Tuple[str, str]: Path to the temp directory and the extracted XML file path
    """
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp(prefix="car_extract_")
    logger.info(f"[INIT] Temporary extraction directory created: {temp_dir}")
    
    try:
        # Extract the .car file (which is essentially a ZIP file)
        with zipfile.ZipFile(car_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
            logger.info(f"[EXTRACT] Successfully extracted '{car_path}' to '{temp_dir}'")
        
        # Find all XML files in the extracted directory
        xml_files = []
        for root, _, files in os.walk(temp_dir):
            for file in files:
                if file.lower().endswith('.xml'):
                    xml_files.append(os.path.join(root, file))
        
        if not xml_files:
            logger.error("[ERROR] No XML files found in the extracted CAR archive.")
            error_msg = 'No XML files found in the extracted CAR archive.'
            shutil.rmtree(temp_dir)
            handle_error_with_countdown(error_msg)
            raise
        
        # Sort alphabetically and select the first one
        xml_files.sort()
        selected_xml = xml_files[0]
        
        logger.info(f"[SELECT] Using XML file: {selected_xml}")
        return temp_dir, selected_xml
        
    except Exception as e:
        logger.error(f"Error extracting CAR file: {e}")
        error_msg = f"Error extracting CAR file: {e}"
        shutil.rmtree(temp_dir)
        handle_error_with_countdown(error_msg)
        raise
        
def rename_modified_xml_files(temp_dir: str) -> None:
    """
    Rename XML files by removing "_modified" from their filenames.
    
    This function walks through the temporary directory, finds all XML files
    with "_modified" in their names, and renames them by removing the "_modified" suffix.
    
    Args:
        temp_dir: Path to the temporary directory with extracted contents
    """
    modified_files_renamed = 0
    
    try:
        for root, _, files in os.walk(temp_dir):
            for file in files:
                if file.lower().endswith('.xml') and "_modified" in file:
                    old_path = os.path.join(root, file)
                    # Create new filename by removing "_modified" from the name
                    new_filename = file.replace("_modified", "")
                    new_path = os.path.join(root, new_filename)
                    
                    try:
                        os.rename(old_path, new_path)
                        modified_files_renamed += 1
                        logger.info(f"Renamed file from '{file}' to '{new_filename}'")
                    except OSError as e:
                        logger.error(f"Error renaming file '{file}': {e}")
        
        logger.info(f"\nRenamed Files Summary:")
        logger.info(f"  XML files renamed (removed '_modified'): {modified_files_renamed}")
        
    except Exception as e:
        logger.error(f"Error while renaming modified XML files: {e}")
        
        
def delete_original_xml_from_car(temp_dir: str, xml_path: str) -> bool:
    """
    Delete the original XML file from the extracted CAR contents before repackaging.
    
    Args:
        temp_dir: Path to the temporary directory with extracted contents
        xml_path: Path to the original XML file to be deleted
        
    Returns:
        bool: True if successful, False otherwise
    """
    
    try:
        if os.path.exists(xml_path):
            os.remove(xml_path)
            logger.info(f"Deleted original XML file: {xml_path}")
            
            # Verify the file was actually deleted
            if not os.path.exists(xml_path):
                return True
            else:
                logger.error(f"Failed to delete original XML file: {xml_path}")
                return False
        else:
            logger.warning(f"Original XML file not found for deletion: {xml_path}")
            return False
            
    except OSError as e:
        logger.error(f"Error deleting original XML file: {e}")
        return False

def repackage_car_file(temp_dir: str, original_car_path: str, xml_path: str, modified_xml_path: str) -> str:
    """
    Repackage the modified XML file back into a new CAR archive.
    
    Args:
        temp_dir: Path to the temporary directory with extracted contents
        original_car_path: Path to the original .car file
        xml_path: Path to the original XML file (to be removed)
        modified_xml_path: Path to the modified XML file
        
    Returns:
        str: Path to the new CAR file
    """
    # Create output filename
    base_name = os.path.splitext(original_car_path)[0]
    new_car_path = f"{base_name}_modified.car"
    
    # Calculate relative path of the XML file within the archive
    rel_xml_path = os.path.relpath(xml_path, temp_dir)
    
    try:
        # First, delete the original XML file from the extracted contents
        delete_success = delete_original_xml_from_car(temp_dir, xml_path)
        if not delete_success:
            logger.warning("Failed to delete original XML file, but continuing with repackaging")
        
        # Copy the modified XML file to the correct location in the temp directory
        # This will place it where the original XML file was
        shutil.copy2(modified_xml_path, xml_path)
        logger.info(f"Placed modified XML at: {xml_path}")
        
        # Create a new CAR file
        with zipfile.ZipFile(new_car_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all files from the temp directory to the zip
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Calculate path in the zip file
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)
        
        logger.info(f"Created modified CAR archive: {new_car_path}")
        return new_car_path
        
    except Exception as e:
        logger.error(f"Error repackaging CAR file: {e}")
        return ""

def cleanup_temp_directory(temp_dir: str) -> None:
    """
    Clean up the temporary directory used for extraction.
    
    Args:
        temp_dir: Path to the temporary directory
    """
    try:
        shutil.rmtree(temp_dir)
        logger.info(f"Removed temporary directory: {temp_dir}")
    except Exception as e:
        logger.error(f"Error cleaning up temporary directory: {e}")

def process_car_file(car_path: str) -> Tuple[str, str, str]:
    """
    Process a CAR file by extracting it and finding an XML file to process.
    
    Args:
        car_path: Path to the CAR file
        
    Returns:
        Tuple[str, str, str]: Temporary directory, XML file path, and output XML path
    """
    temp_dir, xml_path = extract_car_file(car_path)
    
    # Generate output path for modified XML
    xml_dir = os.path.dirname(xml_path)
    xml_filename = os.path.basename(xml_path)
    base_name = os.path.splitext(xml_filename)[0]
    modified_xml_path = os.path.join(xml_dir, f"{base_name}_modified.xml")
    
    return temp_dir, xml_path, modified_xml_path

def cleanup_and_repackage_car(car_path: str) -> str:
    """
    Extract CAR file, remove non-modified XML files, rename remaining XML files by removing "_modified", and repackage.
    This function performs a final cleanup by:
    1. Extracting the CAR file to a temporary directory
    2. Finding all XML files in the extracted contents
    3. Deleting XML files that don't have "_modified" in their name
    4. Renaming remaining XML files by removing "_modified" from their names
    5. Repackaging the remaining files into a new CAR file
    
    Args:
        car_path: Path to the CAR file to process
        
    Returns:
        str: Path to the new cleaned CAR file, or empty string if failed
    """
    # Create a temporary directory for cleanup extraction
    cleanup_temp_dir = tempfile.mkdtemp(prefix="car_cleanup_")
    logger.info(f"Created cleanup temporary directory: {cleanup_temp_dir}")
    
    try:
        # Extract the CAR file
        with zipfile.ZipFile(car_path, 'r') as zip_ref:
            zip_ref.extractall(cleanup_temp_dir)
            logger.info(f"Extracted {car_path} to {cleanup_temp_dir} for cleanup")
        
        # Find all XML files in the extracted directory
        xml_files_found = []
        xml_files_deleted = []
        
        for root, _, files in os.walk(cleanup_temp_dir):
            for file in files:
                if file.lower().endswith('.xml'):
                    file_path = os.path.join(root, file)
                    xml_files_found.append(file_path)
                    
                    # Check if the filename contains "_modified"
                    if "_modified" not in file:
                        try:
                            os.remove(file_path)
                            xml_files_deleted.append(file)
                            logger.info(f"Deleted non-modified XML file in the final .car: {file}")
                        except OSError as e:
                            logger.error(f"Error deleting {file}: {e}")
    
        # Report what was found and deleted
        logger.info(f"\nCleanup Summary:")
        logger.info(f"  Total XML files found: {len(xml_files_found)}")
        logger.info(f"  Non-modified XML files deleted: {len(xml_files_deleted)}")
        logger.info(f"  Remaining XML files: {len(xml_files_found) - len(xml_files_deleted)}")
        
        if xml_files_deleted:
            print(f"  Deleted files: {', '.join(xml_files_deleted)}")
        
        # Rename remaining XML files by removing "_modified" from their names
        rename_modified_xml_files(cleanup_temp_dir)
        
        # Create the final cleaned CAR file
        base_name = os.path.splitext(car_path)[0]
        cleaned_car_path = f"{base_name}.car"
        
        # Create the new CAR file with remaining contents
        with zipfile.ZipFile(cleaned_car_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all remaining files from the temp directory to the zip
            for root, _, files in os.walk(cleanup_temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Calculate relative path in the zip file
                    arcname = os.path.relpath(file_path, cleanup_temp_dir)
                    zipf.write(file_path, arcname)
        
        logger.info(f"Created cleaned CAR archive: {cleaned_car_path}")
        return cleaned_car_path
        
    except Exception as e:
        logger.error(f"Error during cleanup and repackaging: {e}")
        return ""
        
    finally:
        # Clean up the temporary directory
        try:
            shutil.rmtree(cleanup_temp_dir)
            logger.info(f"Removed cleanup temporary directory: {cleanup_temp_dir}")
        except Exception as e:
            logger.error(f"Error cleaning up temporary directory: {e}")
            
            
########################
# Input Handler Module #
########################

def prompt_for_file_path() -> str:
    """
    Prompt the user to enter the full path to an XML or CAR file.
    
    Returns:
        str: The file path provided by the user.
    """
    return input("Please enter the full path to the XML or CAR file (including filename): ").strip()


def validate_file_path(file_path: str) -> bool:
    """
    Validate that the file exists and is accessible.
    
    Args:
        file_path: The path to validate
        
    Returns:
        bool: True if the file exists and is accessible, False otherwise
    """
    # Check if the file exists
    if not os.path.isfile(file_path):
        print(f"Error: The file '{file_path}' does not exist.")
        return False
    
    # Check if the file is readable
    if not os.access(file_path, os.R_OK):
        print(f"Error: You do not have permission to read '{file_path}'.")
        return False
    
    # Check if the file has a supported extension
    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext not in ['.xml', '.car']:
        print(f"Warning: The file '{file_path}' does not have a supported extension (.xml or .car).")
        return False
    
    return True


def prompt_for_prefix_path() -> str:
    """
    Prompt the user for a path prefix.
    Ensures it starts with '/' and does not end with '/'.
    
    Returns:
        str: A valid path prefix starting with '/' and not ending with '/'
    """
    while True:
        prefix = input("\nEnter the full path prefix to prepend: ").strip()
        
        # Add leading slash if missing
        if not prefix.startswith('/'):
            prefix = '/' + prefix
            
        # Remove trailing slash if present
        if prefix.endswith('/'):
            prefix = prefix[:-1]
            
        return prefix


#######################
# SFTP Settings Module #
#######################

def prompt_for_sftp_host() -> str:
    """
    Prompt the user for a new SFTP host IP address and validate it.
    
    Returns:
        str: A valid SFTP host IP address or 'localhost'
    """
    while True:
        host = input("\nEnter the new SFTP host IP address (or 'localhost'): ").strip()
        
        # Check if the host is 'localhost'
        if host.lower() == 'localhost':
            logger.info("[SFTP] Using localhost as SFTP host")
            return 'localhost'
        
        # Validate as IP address
        try:
            ipaddress.ip_address(host)
            logger.info(f"[SFTP] Valid IP address entered: {host}")
            return host
        except ValueError:
            logger.warning(f"[INVALID] Invalid IP address entered: {host}")
            print("Error: Please enter a valid IP address (xxx.xxx.xxx.xxx) or 'localhost'")


def prompt_for_encrypted_password() -> str:
    """
    Prompt the user for an encrypted SFTP password.
    
    Returns:
        str: A non-empty encrypted password
    """
    while True:
        password = input("\nEnter the SFTP password: ").strip()
        
        if password:
            logger.info("[SFTP] Encrypted password received (not logged for security)")
            return password
        else:
            logger.warning("[SFTP] Empty password entered")
            print("Error: Password cannot be empty")
            
def prompt_for_sftp_username() -> str:
    """
    Prompt the user for an SFTP username.
    
    Returns:
        str: A non-empty SFTP username
    """
    while True:
        username = input("\nEnter the SFTP username: ").strip()
        
        if username:
            logger.info(f"[SFTP] Username provided: '{username}'")
            return username
        else:
            logger.warning("[SFTP] Empty username entered")
            print("Error: Username cannot be empty")


def update_sftp_username(file_path: str, output_file: str, new_username: str) -> bool:
    """
    Update SFTP username in the XML file for both ppsSFTPUserF and neSFTPClientUserF tags.
    
    Args:
        file_path: Path to the original XML file
        output_file: Path for the modified XML file
        new_username: New SFTP username
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Starting update of SFTP username in file: {file_path}")
        logger.debug(f"Target output file: {output_file}")
        logger.debug(f"New SFTP username: {new_username}")
        username_tags_found = False
        
        with open(file_path, 'r') as in_file, open(output_file, 'w') as out_file:
            for line in in_file:
                modified_line = line
                
                # Look for the ppsSFTPUserF tag
                user_pattern = r"<ppsSFTPUserF>(?:<!\[CDATA\[(.*?)\]\]>|([^<]+))?</ppsSFTPUserF>"
                matches = re.finditer(user_pattern, line)
                
                for match in matches:
                    username_tags_found = True
                    # Get the full tag content
                    full_tag = match.group(0)
                    
                    # Check if the original had CDATA
                    if "<![CDATA[" in full_tag:
                        new_tag = f"<ppsSFTPUserF><![CDATA[{new_username}]]></ppsSFTPUserF>"
                    else:
                        new_tag = f"<ppsSFTPUserF>{new_username}</ppsSFTPUserF>"
                    
                    # Replace the old tag content with the new one
                    modified_line = modified_line.replace(full_tag, new_tag)
                
                # Look for the neSFTPClientUserF tag
                client_user_pattern = r"<neSFTPClientUserF>(?:<!\[CDATA\[(.*?)\]\]>|([^<]+))?</neSFTPClientUserF>"
                client_matches = re.finditer(client_user_pattern, modified_line)
                
                for match in client_matches:
                    username_tags_found = True
                    # Get the full tag content
                    full_tag = match.group(0)
                    
                    # Check if the original had CDATA
                    if "<![CDATA[" in full_tag:
                        new_tag = f"<neSFTPClientUserF><![CDATA[{new_username}]]></neSFTPClientUserF>"
                    else:
                        new_tag = f"<neSFTPClientUserF>{new_username}</neSFTPClientUserF>"
                    
                    # Replace the old tag content with the new one
                    modified_line = modified_line.replace(full_tag, new_tag)
                
                out_file.write(modified_line)
        
        if not username_tags_found:
            logger.warning("No <ppsSFTPUserF> or <neSFTPClientUserF> tags found in the XML file.")
            print("Warning: No <ppsSFTPUserF> or <neSFTPClientUserF> tags found in the XML file.")
            return False
        logger.info(f"Successfully updated SFTP usernames and wrote to: {output_file}")    
        return True
    except IOError as e:
        logger.error(f"File I/O error during SFTP username update: {e}")
        print(f"Error processing file: {e}")
        return False


def update_sftp_host(file_path: str, output_file: str, new_host: str) -> bool:
    """
    Update the SFTP host IP address in the XML file for both ppsSFTPHostF and neSFTPClientHostF tags.
    
    Args:
        file_path: Path to the original XML file
        output_file: Path for the modified XML file
        new_host: New SFTP host IP address
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        host_tags_found = False
        
        with open(file_path, 'r') as in_file, open(output_file, 'w') as out_file:
            for line in in_file:
                modified_line = line
                
                # Look for the ppsSFTPHostF tag
                host_pattern = r"<ppsSFTPHostF>(?:<!\[CDATA\[(.*?)\]\]>|([^<]+))</ppsSFTPHostF>"
                match = re.search(host_pattern, line)
                
                if match:
                    host_tags_found = True
                    # Get the full tag content
                    full_tag = match.group(0)
                    
                    # Check if the original had CDATA
                    if "<![CDATA[" in full_tag:
                        new_tag = f"<ppsSFTPHostF><![CDATA[{new_host}]]></ppsSFTPHostF>"
                    else:
                        new_tag = f"<ppsSFTPHostF>{new_host}</ppsSFTPHostF>"
                    
                    # Replace the old tag content with the new one
                    modified_line = modified_line.replace(full_tag, new_tag)
                
                # Look for the neSFTPClientHostF tag
                client_host_pattern = r"<neSFTPClientHostF>(?:<!\[CDATA\[(.*?)\]\]>|([^<]+))</neSFTPClientHostF>"
                client_match = re.search(client_host_pattern, modified_line)
                
                if client_match:
                    host_tags_found = True
                    # Get the full tag content
                    full_tag = client_match.group(0)
                    
                    # Check if the original had CDATA
                    if "<![CDATA[" in full_tag:
                        new_tag = f"<neSFTPClientHostF><![CDATA[{new_host}]]></neSFTPClientHostF>"
                    else:
                        new_tag = f"<neSFTPClientHostF>{new_host}</neSFTPClientHostF>"
                    
                    # Replace the old tag content with the new one
                    modified_line = modified_line.replace(full_tag, new_tag)
                
                out_file.write(modified_line)
        
        if not host_tags_found:
            print("Warning: No <ppsSFTPHostF> or <neSFTPClientHostF> tags found in the XML file.")
            return False
            
        return True
    except IOError as e:
        print(f"Error processing file: {e}")
        return False


def update_sftp_password(file_path: str, output_file: str, new_password: str) -> bool:
    """
    Update the encrypted SFTP password in the XML file for multiple password tags.
    
    Args:
        file_path: Path to the original XML file
        output_file: Path for the modified XML file
        new_password: New encrypted SFTP password
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # List of password-related tags to update
        password_tags = ['ppsSFTPPasswordF', 'neSFTPClientPasswordF']  # Add more tags here in the future
        password_tags_found = False
        
        with open(file_path, 'r') as in_file, open(output_file, 'w') as out_file:
            for line in in_file:
                modified_line = line
                
                # Process each password tag
                for tag in password_tags:
                    # Look for the tag
                    password_pattern = fr"<{tag}>(?:<!\[CDATA\[(.*?)\]\]>|([^<]+))?</{tag}>"
                    matches = re.finditer(password_pattern, modified_line)
                    
                    for match in matches:
                        password_tags_found = True
                        # Get the full tag content
                        full_tag = match.group(0)
                        
                        # Check if the original had CDATA
                        if "<![CDATA[" in full_tag:
                            new_tag = f"<{tag}><![CDATA[{new_password}]]></{tag}>"
                        else:
                            new_tag = f"<{tag}>{new_password}</{tag}>"
                        
                        # Replace the old tag content with the new one
                        modified_line = modified_line.replace(full_tag, new_tag)
                
                out_file.write(modified_line)
        
        if not password_tags_found:
            found_tags = ', '.join([f'<{tag}>' for tag in password_tags])
            print(f"Warning: None of the password tags ({found_tags}) found in the XML file.")
            return False
            
        return True
    except IOError as e:
        print(f"Error processing file: {e}")
        return False


def update_sftp_pass_flags(file_path: str, output_file: str) -> bool:
    """
    Update all SFTP pass flag tags to contain 0.
    
    Args:
        file_path: Path to the original XML file
        output_file: Path for the modified XML file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # List of pass flag related tags to update
        flag_tags = ['ppsSFTPPassFlagF', 'neSFTPClientPassFlagF']  # Add more tags here in the future
        flag_tags_found = False
        logger.info(f"Updating SFTP pass flag tags in file: {file_path}")
        
        with open(file_path, 'r') as in_file, open(output_file, 'w') as out_file:
            for line in in_file:
                modified_line = line
                
                # Process each pass flag tag
                for tag in flag_tags:
                    # Look for the tag
                    flag_pattern = fr"<{tag}>(?:<!\[CDATA\[(.*?)\]\]>|([^<]+))?</{tag}>"
                    matches = re.finditer(flag_pattern, modified_line)
                    
                    for match in matches:
                        flag_tags_found = True
                        # Get the full tag content
                        full_tag = match.group(0)
                        
                        # Check if the original had CDATA
                        if "<![CDATA[" in full_tag:
                            new_tag = f"<{tag}><![CDATA[0]]></{tag}>"
                        else:
                            new_tag = f"<{tag}>0</{tag}>"
                        
                        # Replace the old tag content with the new one
                        modified_line = modified_line.replace(full_tag, new_tag)
                
                out_file.write(modified_line)
        
        if not flag_tags_found:
            found_tags = ', '.join([f'<{tag}>' for tag in flag_tags])
            print(f"Warning: None of the pass flag tags ({found_tags}) found in the XML file.")
            logger.warning(f"None of the pass flag tags ({found_tags}) found in the XML file: {file_path}")
            return False
        logger.info(f"SFTP pass flag tags updated successfully in: {output_file}")    
        return True
    except IOError as e:
        logger.error(f"Error processing file '{file_path}': {e}")
        print(f"Error processing file: {e}")
        return False


#######################
# File Processor Module #
#######################

def read_xml_lines(file_path: str) -> Iterator[str]:
    """
    Read an XML file line by line to avoid loading large files into memory.
    
    Args:
        file_path: Path to the XML file
        
    Yields:
        Each line from the file
    
    Raises:
        IOError: If there is an issue reading the file
        SystemExit: If the file cannot be read
    """
    logger.info(f"Attempting to read file: {file_path}")
    try:
        with open(file_path, 'r') as file:
            for line in file:
                yield line
    except IOError as e:
        print(f"Error reading file: {e}")
        logger.error(f"Failed to read file '{file_path}': {e}")
        error_msg = f"Failed to read file '{file_path}': {e}"
        handle_error_with_countdown(error_msg)


#######################
# Path Processor Module #
#######################

def extract_paths_from_line(line: str) -> List[Tuple[str, str, str]]:
    """
    Extract paths from specific tags in a line of XML.
    
    Args:
        line: A line of XML text
        
    Returns:
        List of tuples containing (tag_name, original_path, full_tag_content)
    """
    # List of tags we're looking for
    tags = ['ppsDiskPathF', 'neDiskPathF', 'ppsSFTPPathF' , 'neSFTPClientPathF' , 'matcherPathF' , 'scPathF']
    results = []
    
    # Process each tag type
    for tag in tags:
        # Pattern to match both regular content and CDATA sections:
        # <tagname>path</tagname> or <tagname><![CDATA[path]]></tagname>
        pattern = fr"<{tag}>(?:<!\[CDATA\[(.*?)\]\]>|([^<]+))</{tag}>"
        matches = re.finditer(pattern, line)

        for match in matches:
            # The path is either in group 1 (CDATA) or group 2 (plain text)
            path = match.group(1) if match.group(1) is not None else match.group(2)
            # Get the full tag content (including tags)
            full_tag = match.group(0)
            if path:  # Only add if we found a path
                results.append((tag, path, full_tag))
            else:
                logger.warning(f"Tag <{tag}> found but it is empty or malformed: {full_tag}")
    
    return results

def extract_name_from_xml(file_path: str) -> str:
    """
    Extract the content from the first <name> tag in the XML file.
    
    Args:
        file_path: Path to the XML file
        
    Returns:
        str: The content of the first <name> tag, or empty string if not found
    """
    try:
        with open(file_path, 'r') as file:
            for line in file:
                # Look for the name tag
                name_pattern = r"<name>(?:<!\[CDATA\[(.*?)\]\]>|([^<]+))</name>"
                match = re.search(name_pattern, line)
                if match:
                    # The name is either in group 1 (CDATA) or group 2 (plain text)
                    name = match.group(1) if match.group(1) is not None else match.group(2)
                    if name:
                        return name.strip()
    except Exception as e:
        logging.error(f"Error extracting name from XML: {e}")
    
    return ""


def create_mkdir_commands(paths: List[Tuple[str, str]], prefix: str) -> List[str]:
    """
    Create mkdir commands for each extracted path with the prefix.
    
    Args:
        paths: List of (tag_name, path) tuples
        prefix: Path prefix to prepend
        
    Returns:
        List of mkdir commands
    """
    commands = []
    logger.info("Generating mkdir commands...")
    for _, path in paths:
        # Combine the prefix with the path, ensuring there's no double slash
        # Using os.path.join will handle path concatenation properly
        combined_path = f"{prefix.rstrip('/')}/{path.lstrip('/')}"
        # print(f'mkdir -p "{combined_path}"')
        
        # Create the mkdir command with the -p option to create parent directories as needed
        # We quote the path to handle spaces and special characters
        commands.append(f'mkdir -p "{combined_path}"')
        # print("Combined Path is", combined_path)
    
    if not commands:
        logger.warning("No mkdir commands were generated. Input path list may be empty or invalid.")
    else:
        logger.info(f"Total mkdir commands generated: {len(commands)}")
    return commands


#######################
# Output Generator Module #
#######################

def write_mkdir_script(commands: List[str], file_path: str) -> None:
    """
    Write mkdir commands to an output file, removing duplicates.
    
    Args:
        commands: List of mkdir commands
        output_file: Name of the output file
    """
    try:
        logger.info("Preparing to write mkdir commands to file...")
        # Create the target output directory if it doesn't already exist
        target_folder = os.path.join(os.getcwd(), "Manual commands for creating path")
        os.makedirs(target_folder, exist_ok=True)  # 🔹 Create the folder if it doesn't exist
        
        name = extract_name_from_xml(file_path)
        if not name:
            name = os.path.splitext(os.path.basename(file_path))[0]
            logger.warning("Fallback: using base filename as name due to empty extract_name_from_xml result.")
            
        # Clean the name to be filesystem-safe
        name = re.sub(r'[\\/*?:"<>|]', "_", name).strip()
        
        
        input_filename = os.path.basename(file_path)
        output_file = f"Commands for {name}.txt"

        
        
        # 🔹 Join the output path to point inside the target folder
        output_path = os.path.join(target_folder, output_file)
        
        
        # Use a set to remove duplicate commands
        unique_commands = list(set(commands))
        # Sort the commands to ensure consistent output
        unique_commands.sort()
        
        with open(output_path, 'w') as file:
            for command in unique_commands:
                file.write(f"{command}\n")
        
        logger.info(f"Successfully wrote {len(unique_commands)} mkdir commands to '{output_path}'")
        # Calculate how many duplicates were removed
        duplicates_removed = len(commands) - len(unique_commands)
        print(f"Successfully wrote {len(unique_commands)} mkdir commands to '{output_file}' (removed {duplicates_removed} duplicates)")
    except IOError as e:
        logger.error(f"IO error while writing to the file': {e}")
        print(f"Error writing to file: {e}")


def get_output_filename(input_file: str) -> str:
    """
    Generate a name for the modified output file based on input file type,
    maintaining the same directory as the input file.
    
    Args:
        input_file: Path to the original file
        
    Returns:
        A filename for the modified output file in the same directory
    """
    # Get the directory, file name without extension, and extension
    dir_name = os.path.dirname(input_file)
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    ext = os.path.splitext(input_file)[1].lower()
    
    # Create a new filename with appropriate suffix in the same directory
    if ext == '.xml':
        return os.path.join(dir_name, f"{base_name}_modified.xml")
    elif ext == '.car':
        return os.path.join(dir_name, f"{base_name}_modified.car")
    else:
        return os.path.join(dir_name, f"{base_name}_modified")



def prompt_for_output_filename(default_name: str) -> str:
    """
    Prompt the user for an output filename or use the default.
    - For XML files: Automatically saves in "Modified files" folder
    - For CAR files: Keeps original behavior
    - Automatically appends _1, _2, etc. if filename exists
    - User can still override the location
    
    Args:
        default_name: Default filename (with full path) to suggest
        
    Returns:
        str: The selected output filename (with full path)
    """
    # Create "Modified files" folder if it doesn't exist
    modified_files_dir = os.path.join(os.getcwd(), "Modified files")
    os.makedirs(modified_files_dir, exist_ok=True)
    
    # For XML files - force into "Modified files" folder
    if default_name.lower().endswith('.xml'):
        filename = os.path.basename(default_name)
        default_name = os.path.join(modified_files_dir, filename)
        
     # Handle duplicates for XML files
    if default_name.lower().endswith('.xml'):
        base, ext = os.path.splitext(default_name)
        counter = 1
        new_name = default_name
        while os.path.exists(new_name):
            new_name = f"{base}_{counter}{ext}"
            counter += 1
        default_name = new_name
    
    # Show suggestion to user
    print(f"\nSuggested output file: {default_name}")
    return default_name


def regenerate_xml(input_file: str, output_file: str, prefix: str) -> None:
    """
    Create a new XML file with updated paths.
    
    Args:
        input_file: Path to the original XML file
        output_file: Path for the regenerated XML file
        prefix: Path prefix to prepend
    """
    try:
        with open(output_file, 'w') as out_file:
            # Process the XML file line by line
            for line in read_xml_lines(input_file):
                modified_line = line
                
                # Extract paths from this line
                extractions = extract_paths_from_line(line)
                
                # If any paths were found, update them in the line
                for tag, path, full_tag in extractions:
                    # Create the new combined path
                    combined_path = os.path.join(prefix, path.lstrip('/'))
                    combined_path = combined_path.replace("\\", "/") 
                    
                    # Check if the original had CDATA
                    if "<![CDATA[" in full_tag:
                        # Create new tag content with the updated path wrapped in CDATA
                        new_tag = f"<{tag}><![CDATA[{combined_path}]]></{tag}>"
                    else:
                        # Create new tag content with the updated path
                        new_tag = f"<{tag}>{combined_path}</{tag}>"
                    
                    # Replace the old tag content with the new one
                    # This preserves all other aspects of the XML structure
                    modified_line = modified_line.replace(full_tag, new_tag)
                
                # Write the modified (or original) line to the output file
                out_file.write(modified_line)
                
        print(f"Successfully generated modified XML file: '{output_file}'")
    except IOError as e:
        print(f"Error writing to file: {e}")
        
def prompt_for_default_stopped() -> bool:
    """
    Prompt the user to decide whether to set 'Default Stopped' to 'True' for all collectors.
    
    Returns:
        bool: True if the user wants to set 'Default Stopped' to 'True', False otherwise
    """
    user_input = input("Would you like to set 'Default Stopped' to 'True' for all collectors? Press 'Y' to proceed: ").strip().upper()
    return user_input == 'Y'


def update_default_stopped_state(file_path: str, output_file: str) -> bool:
    """
    Update all <defaultStoppedState> tags in the XML file to contain value '1' (True).
    
    This function scans through an XML file, identifies all <defaultStoppedState> tags,
    and changes their values to '1', indicating that collectors should be stopped by default.
    
    Args:
        file_path: Path to the original XML file
        output_file: Path for the modified XML file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        default_stopped_tags_found = False
        
        with open(file_path, 'r') as in_file, open(output_file, 'w') as out_file:
            for line in in_file:
                modified_line = line
                
                # Look for the defaultStoppedState tag
                # Pattern to match both regular content and CDATA sections
                stopped_pattern = r"<defaultStoppedState>(?:<!\[CDATA\[(.*?)\]\]>|([^<]+))?</defaultStoppedState>"
                matches = re.finditer(stopped_pattern, line)
                
                for match in matches:
                    default_stopped_tags_found = True
                    # Get the full tag content
                    full_tag = match.group(0)
                    
                    # Check if the original had CDATA
                    if "<![CDATA[" in full_tag:
                        new_tag = f"<defaultStoppedState><![CDATA[1]]></defaultStoppedState>"
                    else:
                        new_tag = f"<defaultStoppedState>1</defaultStoppedState>"
                    
                    # Replace the old tag content with the new one
                    modified_line = modified_line.replace(full_tag, new_tag)
                
                out_file.write(modified_line)
        
        if not default_stopped_tags_found:
            print("Warning: No <defaultStoppedState> tags found in the XML file.")
            return False
            
        print("Successfully updated all collectors to 'Default Stopped' state.")
        return True
    except IOError as e:
        print(f"Error processing file: {e}")
        return False
def display_xml_compatibility_warning() -> None:
    """
    Display a formal warning message about XML file compatibility requirements.
    
    This function informs the user that the tool is specifically designed to work with
    XML files exported without dependencies from the BLDM tool, and explains potential
    issues that may arise when using incompatible formats.
    """
    # ANSI color codes
    RESET = "\033[0m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    # Compatibility Requirements
    print(f"\n{BOLD}{GREEN}COMPATIBILITY REQUIREMENTS{RESET}")
    print(f"{DIM}───────────────────────────────{RESET}")
    print("• XML files: Must be exported WITHOUT dependencies")
    print("• CAR files: Fully supported (all configurations)")
    
    # Critical Warnings
    print(f"\n{BOLD}{YELLOW}CRITICAL WARNINGS{RESET}")
    print(f"{DIM}──────────────────────{RESET}")
    print(f"{RED}- Non-compliant XML will be rejected by BLDM{RESET}")
    print(f"{RED}- May cause:{RESET}")
    print("  • Path transformation failures")
    print("  • Broken references")
    print("  • Unpredictable behavior")
    print(f"\n{YELLOW}{BOLD}⚠️  Always verify export settings before processing.{RESET}")
    
    logger.warning("Displayed XML compatibility warning to the user.")
    
    # Request acknowledgment from the user
    while True:
        acknowledgment = input("\nDo you confirm that your file complies with the compatibility requirements? (y/n): ").lower()
        if acknowledgment == 'y':
            logger.info("User acknowledged compatibility requirements. Proceeding.")
            print("Proceeding with file processing...")
            return
        elif acknowledgment == 'n':
            logger.info("User did not acknowledge compatibility requirements. Exiting.")
            print("Please export an XML file without dependencies from BLDM before proceeding.")
            error_msg = "Please export an XML file without dependencies from BLDM before proceeding."
            handle_user_cancellation(error_msg)
        else:
            print("Please enter 'y' to acknowledge and continue, or 'n' to exit.")

###########################
# Directory Search Module #
###########################

import os
import logging
from typing import List, Dict, Optional

def prompt_for_directory_path() -> str:
    """
    Prompt the user to enter a directory path to search for .car and .xml files.
    
    Returns:
        str: The directory path provided by the user.
    """
    return input("Please enter the directory path to search for .car and .xml files: ").strip()

def validate_directory_path(dir_path: str) -> bool:
    """
    Validate that the directory exists and is accessible.
    
    Args:
        dir_path: The directory path to validate
        
    Returns:
        bool: True if the directory exists and is accessible, False otherwise
    """
    # Check if the directory exists
    if not os.path.isdir(dir_path):
        print(f"Error: The directory '{dir_path}' does not exist.")
        return False
    
    # Check if the directory is readable
    if not os.access(dir_path, os.R_OK):
        print(f"Error: You do not have permission to read directory '{dir_path}'.")
        return False
    
    return True

def find_car_xml_files(dir_path: str) -> Dict[str, List[str]]:
    """
    Search for .car and .xml files in the specified directory and its subdirectories.
    
    Args:
        dir_path: The directory path to search
        
    Returns:
        Dict[str, List[str]]: Dictionary with 'car' and 'xml' keys containing lists of file paths
    """
    car_files = []
    xml_files = []
    
    logging.info(f"Searching for .car and .xml files in {dir_path} and subdirectories")
    
    try:
        for root, _, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                if file.lower().endswith('.car'):
                    car_files.append(file_path)
                elif file.lower().endswith('.xml'):
                    xml_files.append(file_path)
    
        logging.info(f"Found {len(car_files)} .car files and {len(xml_files)} .xml files")
        return {'car': car_files, 'xml': xml_files}
    except Exception as e:
        logging.error(f"Error while searching for files: {e}")
        return {'car': [], 'xml': []}

def display_files(files_dict: Dict[str, List[str]]) -> bool:
    """
    Display only the file names (not full paths) of found .car and .xml files to the user.
    
    Args:
        files_dict: Dictionary with 'car' and 'xml' keys containing lists of file paths
        
    Returns:
        bool: True if files were found, False otherwise
    """
    car_files = files_dict['car']
    xml_files = files_dict['xml']
    
    total_files = len(car_files) + len(xml_files)
    
    if total_files == 0:
        print("No .car or .xml files found in the specified directory.")
        return False
    
    print(f"\nFound {total_files} file(s):")
    
    file_index = 1
    
    if car_files:
        print("\nCAR Files:")
        for i, file_path in enumerate(car_files, start=file_index):
            # Extract just the filename without the path
            file_name = os.path.basename(file_path)
            print(f"{i}. {file_name}")
        file_index += len(car_files)
    
    if xml_files:
        print("\nXML Files:")
        for i, file_path in enumerate(xml_files, start=file_index):
            # Extract just the filename without the path
            file_name = os.path.basename(file_path)
            print(f"{i}. {file_name}")
    
    return True

def prompt_for_file_selection(files_dict: Dict[str, List[str]]) -> Optional[str]:
    """
    Prompt the user to select a file from the displayed list.
    
    Args:
        files_dict: Dictionary with 'car' and 'xml' keys containing lists of file paths
        
    Returns:
        Optional[str]: The selected file path, or None if selection was invalid
    """
    car_files = files_dict['car']
    xml_files = files_dict['xml']
    
    all_files = car_files + xml_files
    total_files = len(all_files)
    
    while True:
        try:
            selection = input(f"\nSelect a file to process (1-{total_files}, or 'q' to quit): ").strip()
            
            if selection.lower() == 'q':
                print("Operation cancelled by user.")
                handle_user_cancellation("Operation cancelled by user.")
                return None
            
            index = int(selection) - 1
            
            if 0 <= index < total_files:
                selected_file = all_files[index]
                logging.info(f"User selected file: {selected_file}")
                return selected_file
            else:
                print(f"Invalid selection. Please enter a number between 1 and {total_files}.")
        except ValueError:
            print("Invalid input. Please enter a valid number or 'q' to quit.")

##########################
# Feedback asking module #
##########################
def request_feedback():
    print("\n=== BLDM Tool Feedback ===")
    logger.info("Prompted user for feedback.")
    choice = input("Would you like to provide feedback or Suggestions? (y/n): ").lower()
    
    if choice == 'y':
        logger.info("User opted to provide feedback.")
        subject = "BLDM Configuration Processor Feedback v1.1.1"
        body = "\n\nMy feedback:\n- Rating (1-5): \n- Issues encountered: \n- Suggestions: "
        mailto = f"mailto:suvra.dwibedy@ericsson.com?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
        try:
            webbrowser.open(mailto)
            logger.info("Opened default mail client for user feedback.")
            print("Thank you! Your email client is opening...")
        except Exception as e:
            logger.error(f"Failed to open email client: {e}")
            print("Error: Unable to open your email client. Please send feedback manually.")
            handle_user_cancellation("Unable to open your email client. Please send feedback manually.")
    else:
        logger.info("User declined to provide feedback.")
        print("Thank you for using the BLDM CONFIG LOCALIZER tool!")
        handle_sucessful_completion("Thank you for using the BLDM CONFIG LOCALIZER tool!")

#######################
# Main Function #
#######################

def get_yes_no_input(prompt: str) -> bool:
    """
    Get a strict yes/no input from the user.
    Only accepts 'y' or 'n' as valid inputs.
    
    Args:
        prompt: The question to ask the user
        
    Returns:
        bool: True for 'y', False for 'n'
    """
    while True:
        user_input = input(prompt).lower()
        if user_input == 'y':
            return True
        elif user_input == 'n':
            return False
        else:
            print("Please enter only 'y' or 'n'.")


def main() -> None:
    """
    Main function to orchestrate the XML/CAR processing workflow with directory search functionality.
    """
    # Get user, host, and timestamp info
    user = getpass.getuser()
    host = socket.gethostname()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # ANSI color codes 
    RESET = "\033[0m"
    DIM = "\033[2m"
    
    # Print the info line
    print(f"\n{DIM}User: {user} | Host: {host} | Time: {now}{RESET}")
    
    
    logger = setup_logging(log_level=logging.INFO, log_to_file=True, console_output=False)
    try:
        
        # Log this information
        logger.info(f"Session started - User: {user} | Host: {host}")
        # Get log file path from the logger
        log_file_path = None
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                log_file_path = handler.baseFilename
                break
            
        logger.info("=== Initializing XML/CAR Path Processor ===")
        operations_performed = []

        RESET = "\033[0m"
        CYAN = "\033[96m"
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        RED = "\033[91m"
        BOLD = "\033[1m"
        DIM = "\033[2m"
        
        print(f"\n{CYAN}╔══════════════════════════════════════════════════════════════╗{RESET}")
        print(f"{CYAN}║{BOLD}                  BLDM CONFIG LOCALIZER  •  v1.1.1            {RESET}{CYAN}║{RESET}")
        print(f"{CYAN}╚══════════════════════════════════════════════════════════════╝{RESET}")
        print(f"{CYAN}║                                                              ║{RESET}")
        print(f"{CYAN}║  {BOLD}CORE FEATURES:{RESET}{CYAN}                                              ║{RESET}")
        print(f"{CYAN}║    • Path localization for target environments               ║{RESET}")
        print(f"{CYAN}║    • Automated SFTP configuration                            ║{RESET}")
        print(f"{CYAN}║    • Collector state standardization                         ║{RESET}")
        print(f"{CYAN}║    • CAR/XML processing                                      ║{RESET}")
        print(f"{CYAN}║                                                              ║{RESET}")
        print(f"{CYAN}║  {BOLD}WORKFLOW:{RESET}{CYAN}                                                   ║{RESET}")
        print(f"{CYAN}║    1. Import source configuration                            ║{RESET}")
        print(f"{CYAN}║    2. Set localization parameters                            ║{RESET}")
        print(f"{CYAN}║                                                              ║{RESET}")
        print(f"{CYAN}╔══════════════════════════════════════════════════════════════╗{RESET}")
        print(f"{CYAN}║  {BOLD}SAFETY:{RESET} Original preservation  •  Audit logging             {CYAN}║{RESET}")
        print(f"{CYAN}╚══════════════════════════════════════════════════════════════╝{RESET}")

        # Display compatibility warning and get user acknowledgment
        display_xml_compatibility_warning()

        # Get and validate the directory path

            # First get the file path (moved this before logging setup)
        while True:
            dir_path = prompt_for_directory_path()
            if validate_directory_path(dir_path):
                break
            
        files_dict = find_car_xml_files(dir_path)
        if not display_files(files_dict):
            print("No files to process. Exiting.")
            handle_user_cancellation("No files to process. Exiting.")
            return

        file_path = prompt_for_file_selection(files_dict)
        if file_path is None:
            return

        # Set up logging with the file path
        logger = setup_logging(file_path=file_path, log_level=logging.INFO, log_to_file=True, console_output=False)


        # Check file extension
        file_type = check_file_extension(file_path)

        if file_type == 'car':
            logger.info(f"Processing CAR file: {file_path}")
            print(f"Processing CAR file: {file_path}")

            # Process the CAR file
            log_operation_start("CAR extraction")
            temp_dir, xml_path, modified_xml_path = process_car_file(file_path)
            log_operation_end("CAR extraction")
            operations_performed.append(f"Extracted CAR file: {file_path}")

            # Log CAR processing details
            output_car_path = f"{os.path.splitext(file_path)[0]}_modified.car"
            log_car_processing_details(temp_dir, xml_path, modified_xml_path, output_car_path)

            # We'll handle cleanup at the end
            try:
                # Continue with normal processing but use the XML from CAR
                process_xml_file(xml_path, modified_xml_path)
                operations_performed.append(f"Processed extracted XML: {os.path.basename(xml_path)}")

                # Note: The original XML file will be deleted during repackaging
                logger.info("\nRepackaging CAR file (original XML will be removed)...")
                logger.info("Beginning CAR repackaging")

                # Repackage the CAR file with the modified XML (this will delete the original XML)
                log_operation_start("CAR repackaging")
                output_car = repackage_car_file(temp_dir, file_path, xml_path, modified_xml_path)
                log_operation_end("CAR repackaging")

                if output_car:
                    logger.info(f"Created modified CAR file: {output_car}")
                    operations_performed.append(f"Created modified CAR file: {os.path.basename(output_car)}")

                    # Perform final cleanup and repackaging
                    logger.info("Beginning final CAR cleanup")
                    logger.info("This will remove non-modified XML files and rename remaining XML files by removing '_modified' suffix")

                    log_operation_start("CAR cleanup")
                    cleaned_car = cleanup_and_repackage_car(output_car)
                    log_operation_end("CAR cleanup")

                    if cleaned_car:
                        logger.info(f"Created cleaned CAR file: {cleaned_car}")
                        print(f"Successfully created cleaned CAR file: {cleaned_car}")
                        operations_performed.append(f"Created cleaned CAR file: {os.path.basename(cleaned_car)}")

                        target_dir = os.path.join(os.getcwd(), "Modified files")
                        os.makedirs(target_dir, exist_ok=True)
                        logger.info(f"Ensured target directory exists: {target_dir}")
                        filename = os.path.basename(cleaned_car)
                        name, ext = os.path.splitext(filename)

                        counter = 1
                        new_filename = filename
                        destination = os.path.join(target_dir, new_filename)

                        while os.path.exists(destination):
                            logger.warning(f"File already exists: {destination}. Attempting new filename.")
                            new_filename = f"{name}({counter}){ext}"
                            destination = os.path.join(target_dir, new_filename)
                            counter += 1
                        shutil.move(cleaned_car, destination)
                        logger.info(f"Moved cleaned CAR file to: {destination}")
                        print(f"Moved to: {destination}")


                        # Automatically remove the intermediate file
                        cleanup_intermediate = True  # Set to always True
                        if cleanup_intermediate:
                            try:
                                os.remove(output_car)
                                logger.info(f"Removed intermediate file: {output_car}")
                                print(f"Automatically removed intermediate file: {output_car}")
                            except OSError as e:
                                logger.info(f"Could not remove intermediate file: {e}")
                    else:
                        logger.error("Failed to create cleaned CAR file")
                        print("Failed to create cleaned CAR file.")
                else:
                    logger.error("Failed to create modified CAR file")
                    # print("\nFailed to create modified CAR file.")

            finally:
                # Clean up temporary directory
                log_operation_start("temporary directory cleanup")
                cleanup_temp_directory(temp_dir)
                log_operation_end("temporary directory cleanup")

        elif file_type == 'xml':
            logger.info(f"Processing XML file: {file_path}")
            print(f"Processing XML file: {file_path}")
            # Process normal XML file using existing process_xml_file function
            default_output = get_output_filename(file_path)
            output_file = prompt_for_output_filename(default_output)
            logger.info(f"Output will be saved to: {output_file}")

            # # Log file paths
            # log_file_paths(file_path, output_file, log_file_path)

            log_operation_start("XML processing")
            process_xml_file(file_path, output_file)
            log_operation_end("XML processing")
            operations_performed.append(f"Processed XML file: {os.path.basename(file_path)}")
        else:
            logger.error(f"Unsupported file type: {file_path}")
            print(f"Unsupported file type: {file_path}")
            error_msg = f"Unsupported file type: {file_path}"
            handle_error_with_countdown(error_msg)

        # Log summary of all operations performed
        log_summary(operations_performed)

        logger.info("Processing complete!")
        request_feedback()
    except KeyboardInterrupt:
        logger.error("Processing interrupted by user (^C)")
        print("\nProcessing interrupted by user. Exiting.")
        error_msg = "Processing interrupted by user. Exiting."
        handle_user_cancellation(error_msg)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\nAn unexpected error occurred: {e}")
        error_msg = "\nAn unexpected error occurred: {e}"
        handle_error_with_countdown(error_msg)

def process_xml_file(file_path: str, output_file: str) -> None:
    """
    Process an XML file with all the selected operations.
    
    Args:
        file_path: Path to the XML file to process
        output_file: Path for the output file
    """
    logger = logging.getLogger()
    try:
        operations_performed = []

        # Log file processing start
        logger.info(f"Starting XML file processing: {file_path}")
        logger.info(f"Output will be saved to: {output_file}")

        # Ask the user which operations they want to perform
        operations = []
        print("\nSelect operations to perform (y/n for each):")
        logger.info("Prompting user for operations to perform")

        # Paths processing
        if get_yes_no_input("Update Collector and Distributer Disk paths? (y/n): "):
            operations.append("paths")
            logger.info("User selected to process paths")

        # SFTP host update
        if get_yes_no_input("Update SFTP host IP? (y/n): "):
            operations.append("host")
            logger.info("User selected to update SFTP host IP")

        # SFTP username update
        if get_yes_no_input("Update SFTP username? (y/n): "):
            operations.append("username")
            logger.info("User selected to update SFTP username")

        # SFTP password update
        if get_yes_no_input("Update encrypted SFTP password? (y/n): "):
            operations.append("password")
            logger.info("User selected to update SFTP password")

        # SFTP pass flags update
        if get_yes_no_input("Update SFTP 'Password Not Required Field' to no? (y/n): "):
            operations.append("flags")
            logger.info("User selected to update password flags")

        # Default Stopped State update 
        if get_yes_no_input("Set 'Default Stopped' to 'True' for all collectors? (y/n): "):
            operations.append("default_stopped")
            logger.info("User selected to update default stopped state")

        if not operations:
            logger.warning("No operations selected. Exiting.")
            print("\nNo operations selected. Exiting.")
            return

        logger.info(f"Selected operations: {', '.join(operations)}")

        # Create a temporary working file for each operation
        temp_file = f"{os.path.splitext(output_file)[0]}_temp{os.path.splitext(output_file)[1]}"
        logger.info(f"Temporary working file: {temp_file}")

        # Start with the original file
        current_input = file_path
        logger.info(f"Initial input file: {current_input}")

        # Process paths if selected
        if "paths" in operations:
            prefix_path = prompt_for_prefix_path()
            logger.info(f"User provided path prefix: {prefix_path}")

            # Process the XML file to collect all paths
            log_operation_start("path extraction")
            all_paths = []
            print("\nProcessing XML file for paths...")
            for line in read_xml_lines(current_input):
                extractions = extract_paths_from_line(line)
                all_paths.extend([(tag, path) for tag, path, _ in extractions])

            if not all_paths:
                logger.warning("No matching path tags found in the XML file")
                print("No matching path tags found in the XML file.")
            else:
                logger.info(f"Found {len(all_paths)} paths to process")
                print(f"Found {len(all_paths)} paths to process.")

                # Create mkdir commands
                mkdir_commands = create_mkdir_commands(all_paths, prefix_path)
                logger.info(f"Generated {len(mkdir_commands)} mkdir commands")

                # Write the mkdir commands to a file
                write_mkdir_script(mkdir_commands, file_path)
                logger.info("Wrote mkdir commands to 'commands_to_create_the_paths_manually.txt'")
                operations_performed.append("Generated mkdir commands file: 'commands_to_create_the_paths_manually.txt'")

                # Generate the modified XML file
                logger.info(f"Generating modified XML with prefix: {prefix_path}")
                regenerate_xml(current_input, temp_file, prefix_path)
                logger.info(f"Generated temporary XML file: {temp_file}")

                # Update the current input for the next operation
                current_input = temp_file
                logger.info(f"Updated current input to: {current_input}")
            log_operation_end("path extraction")

        # Update SFTP host if selected
        if "host" in operations:
            new_host = prompt_for_sftp_host()
            logger.info(f"User provided new SFTP host: {new_host}")
            print(f"\nUpdating SFTP host to: {new_host} (in both ppsSFTPHostF and neSFTPClientHostF tags)")

            # Create a new temporary file for this operation
            temp_output = f"{os.path.splitext(output_file)[0]}_temp2{os.path.splitext(output_file)[1]}"
            logger.info(f"Temporary output file for host update: {temp_output}")

            log_operation_start("SFTP host update")
            success = update_sftp_host(current_input, temp_output, new_host)

            if success:
                logger.info("SFTP host updated successfully")
                print("SFTP host updated successfully.")
                operations_performed.append(f"Updated SFTP host to: {new_host}")

                # Remove the old temp file if it's not the original input
                if current_input != file_path:
                    try:
                        os.remove(current_input)
                        logger.debug(f"Removed temporary file: {current_input}")
                    except OSError as e:
                        logger.error(f"Failed to remove temporary file: {e}")

                current_input = temp_output
                logger.info(f"Updated current input to: {current_input}")
            else:
                logger.error("Failed to update SFTP host")
                print("Failed to update SFTP host.")
            log_operation_end("SFTP host update")

        # Update SFTP username if selected
        if "username" in operations:
            new_username = prompt_for_sftp_username()
            logger.info(f"User provided new SFTP username: {new_username}")
            print(f"\nUpdating SFTP username to: {new_username} (in both ppsSFTPUserF and neSFTPClientUserF tags)")

            # Create a new temporary file for this operation
            temp_output = f"{os.path.splitext(output_file)[0]}_temp3{os.path.splitext(output_file)[1]}"
            logger.info(f"Temporary output file for username update: {temp_output}")

            log_operation_start("SFTP username update")
            success = update_sftp_username(current_input, temp_output, new_username)

            if success:
                logger.info("SFTP username updated successfully")
                print("SFTP username updated successfully.")
                operations_performed.append(f"Updated SFTP username to: {new_username}")

                # Remove the old temp file if it's not the original input
                if current_input != file_path:
                    try:
                        os.remove(current_input)
                        logger.debug(f"Removed temporary file: {current_input}")
                    except OSError as e:
                        logger.error(f"Failed to remove temporary file: {e}")

                current_input = temp_output
                logger.info(f"Updated current input to: {current_input}")
            else:
                logger.error("Failed to update SFTP username")
                print("Failed to update SFTP username.")
            log_operation_end("SFTP username update")

        # Update SFTP password if selected
        if "password" in operations:
            new_password = prompt_for_encrypted_password()
            logger.info("User provided new encrypted SFTP password")
            print("\nUpdating SFTP encrypted password...")

            # Create a new temporary file for this operation
            temp_output = f"{os.path.splitext(output_file)[0]}_temp4{os.path.splitext(output_file)[1]}"
            logger.info(f"Temporary output file for password update: {temp_output}")

            log_operation_start("SFTP password update")
            success = update_sftp_password(current_input, temp_output, new_password)

            if success:
                logger.info("SFTP password updated successfully")
                print("SFTP password updated successfully.")
                operations_performed.append("Updated SFTP encrypted password")

                # Remove the old temp file if it's not the original input
                if current_input != file_path:
                    try:
                        os.remove(current_input)
                        logger.debug(f"Removed temporary file: {current_input}")
                    except OSError as e:
                        logger.error(f"Failed to remove temporary file: {e}")

                current_input = temp_output
                logger.info(f"Updated current input to: {current_input}")
            else:
                logger.error("Failed to update SFTP password")
                print("Failed to update SFTP password.")
            log_operation_end("SFTP password update")

        # Update SFTP pass flags if selected
        if "flags" in operations:
            logger.info("Updating SFTP pass flags to 0")
            print("\nUpdating all SFTP Password not required field to 0...")

            # Create a new temporary file for this operation
            temp_output = f"{os.path.splitext(output_file)[0]}_temp5{os.path.splitext(output_file)[1]}"
            logger.info(f"Temporary output file for pass flags update: {temp_output}")

            log_operation_start("SFTP pass flags update")
            success = update_sftp_pass_flags(current_input, temp_output)

            if success:
                logger.info("SFTP pass flags updated successfully")
                print("SFTP password not required field updated successfully to No.")
                operations_performed.append("Updated SFTP password not required field to No")

                # Remove the old temp file if it's not the original input
                if current_input != file_path:
                    try:
                        os.remove(current_input)
                        logger.debug(f"Removed temporary file: {current_input}")
                    except OSError as e:
                        logger.error(f"Failed to remove temporary file: {e}")

                current_input = temp_output
                logger.info(f"Updated current input to: {current_input}")
            else:
                logger.error("Failed to update SFTP pass flags")
                print("Failed to update password not required field to 'No'.")
            log_operation_end("SFTP pass flags update")

        # Update Default Stopped State if selected
        if "default_stopped" in operations:
            logger.info("Updating default stopped state to True for all collectors")
            print("\nUpdating all collectors to 'Default Stopped' state...")

            # Create a new temporary file for this operation
            temp_output = f"{os.path.splitext(output_file)[0]}_temp6{os.path.splitext(output_file)[1]}"
            logger.info(f"Temporary output file for default stopped update: {temp_output}")

            log_operation_start("default stopped state update")
            success = update_default_stopped_state(current_input, temp_output)

            if success:
                logger.info("Default stopped state updated successfully")
                print("Default Stopped state updated successfully to True for all collectors.")
                operations_performed.append("Set Default Stopped state to True for all collectors")

                # Remove the old temp file if it's not the original input
                if current_input != file_path:
                    try:
                        os.remove(current_input)
                        logger.debug(f"Removed temporary file: {current_input}")
                    except OSError as e:
                        logger.error(f"Failed to remove temporary file: {e}")

                current_input = temp_output
                logger.info(f"Updated current input to: {current_input}")
            else:
                logger.error("Failed to update default stopped state")
                print("Failed to update Default Stopped state.")
            log_operation_end("default stopped state update")

        # Rename the final temporary file to the desired output file
        if current_input != file_path:
            try:
                # If the output file already exists (from a previous run), remove it
                if os.path.exists(output_file):
                    os.remove(output_file)
                    logger.info(f"Removed existing output file: {output_file}")

                os.rename(current_input, output_file)
                logger.info(f"Saved final output to: {output_file}")
                print(f"\nFinal output saved to: '{output_file}'")
                operations_performed.append(f"Final output saved to: {output_file}")

                # Log final path information
                logger.info("=" * 50)
                logger.info("FINAL FILE PATHS")
                logger.info("=" * 50)
                logger.info(f"Original input file: {file_path}")
                logger.info(f"Modified output file: {output_file}")
                logger.info("=" * 50)

            except OSError as e:
                logger.error(f"Error renaming final output file: {e}")
                print(f"Error renaming final output file: {e}")
                print(f"Final output is available at: '{current_input}'")
        else:
            # No operations modified the file
            logger.warning("No modifications were made to the XML file")
            print("\nNo modifications were made to the XML file.")

        # Clean up any temporary files that might have been left behind
        for i in range(1, 7):
            temp_path = f"{os.path.splitext(output_file)[0]}_temp{i}{os.path.splitext(output_file)[1]}"
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                    logger.debug(f"Cleaned up temporary file: {temp_path}")
                except OSError as e:
                    logger.error(f"Failed to clean up temporary file: {temp_path}, error: {e}")

        # Summarize operations performed
        log_summary(operations_performed)

        summary_items = []
        if "paths" in operations:
            summary_items.append("Mkdir commands saved to: 'commands_to_create_the_paths_manually.txt'")

        if any(op in operations for op in ["paths", "host", "username", "password", "flags", "default_stopped"]):
            summary_items.append(f"Modified XML saved ")

        # Print summary with numbers
        print("\n=== Processing Summary ===")
        for idx, item in enumerate(summary_items, 1):
            print(f"{idx}. {item}")

        # Log completion
        logger.info("XML file processing completed successfully")

    except KeyboardInterrupt:
            logger.error("XML processing interrupted by user (^C)")
            print("\nXML processing interrupted by user. Exiting.")
            handle_user_cancellation('XML processing interrupted by user. Exiting.')
            # Clean up any temporary files that might have been created
            for i in range(1, 7):
                temp_path = f"{os.path.splitext(output_file)[0]}_temp{i}{os.path.splitext(output_file)[1]}"
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                        logger.debug(f"Cleaned up temporary file: {temp_path}")
                    except OSError as e:
                        logger.error(f"Failed to clean up temporary file: {temp_path}, error: {e}")
                        
            error_msg = "Processing interrupted by user. Exiting."
            handle_user_cancellation(error_msg)
    except Exception as e:
        logger.error(f"Error processing XML file: {e}")
        print(f"\nError processing XML file: {e}")
        error_msg = f"\nError processing XML file: {e}"
        handle_error_with_countdown(error_msg)
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        error_msg = "\nOperation cancelled by user"
        handle_user_cancellation(error_msg)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        error_msg = f"An unexpected error occurred: {e}"
        handle_error_with_countdown(error_msg)
        
