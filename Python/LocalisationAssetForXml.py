"""
XML Path Processor

This script processes XML files by extracting paths from specific tags,
prepending a user-defined prefix to these paths, generating mkdir commands,
and creating a modified XML file with updated paths.

The script is organized into modules within the same file for easier distribution
and to avoid import errors.

Usage:
    Run the script and follow the interactive prompts.
"""


import os
import sys
import re
import ipaddress
from typing import List, Tuple, Optional, Iterator

#######################
# Input Handler Module #
#######################

def prompt_for_file_path() -> str:
    """
    Prompt the user to enter the full path to an XML file.
    
    Returns:
        str: The file path provided by the user.
    """
    return input("Please enter the full path to the XML file (including filename): ").strip()


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
    
    # Check if the file has a .xml extension (optional validation)
    if not file_path.lower().endswith('.xml'):
        print(f"Warning: The file '{file_path}' does not have an .xml extension.")
        # We don't return False here as the file might still be a valid XML file
    
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
            return 'localhost'
        
        # Validate as IP address
        try:
            ipaddress.ip_address(host)
            return host
        except ValueError:
            print("Error: Please enter a valid IP address (xxx.xxx.xxx.xxx) or 'localhost'")


def prompt_for_encrypted_password() -> str:
    """
    Prompt the user for an encrypted SFTP password.
    
    Returns:
        str: A non-empty encrypted password
    """
    while True:
        password = input("\nEnter the encrypted SFTP password: ").strip()
        
        if password:
            return password
        else:
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
            return username
        else:
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
            print("Warning: No <ppsSFTPUserF> or <neSFTPClientUserF> tags found in the XML file.")
            return False
            
        return True
    except IOError as e:
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
                    password_pattern = f"<{tag}>(?:<!\[CDATA\[(.*?)\]\]>|([^<]+))?</{tag}>"
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
        
        with open(file_path, 'r') as in_file, open(output_file, 'w') as out_file:
            for line in in_file:
                modified_line = line
                
                # Process each pass flag tag
                for tag in flag_tags:
                    # Look for the tag
                    flag_pattern = f"<{tag}>(?:<!\[CDATA\[(.*?)\]\]>|([^<]+))?</{tag}>"
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
            return False
            
        return True
    except IOError as e:
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
    try:
        with open(file_path, 'r') as file:
            for line in file:
                yield line
    except IOError as e:
        print(f"Error reading file: {e}")
        sys.exit(1)


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
        pattern = f"<{tag}>(?:<!\[CDATA\[(.*?)\]\]>|([^<]+))</{tag}>"
        matches = re.finditer(pattern, line)
        
        for match in matches:
            # The path is either in group 1 (CDATA) or group 2 (plain text)
            path = match.group(1) if match.group(1) is not None else match.group(2)
            # Get the full tag content (including tags)
            full_tag = match.group(0)
            if path:  # Only add if we found a path
                results.append((tag, path, full_tag))
    
    return results


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
    for _, path in paths:
        # Combine the prefix with the path, ensuring there's no double slash
        # Using os.path.join will handle path concatenation properly
        combined_path = f"{prefix.rstrip('/')}/{path.lstrip('/')}"
        print(f'mkdir -p "{combined_path}"')
        
        # Create the mkdir command with the -p option to create parent directories as needed
        # We quote the path to handle spaces and special characters
        commands.append(f'mkdir -p "{combined_path}"')
        # print("Combined Path is", combined_path)
    return commands


#######################
# Output Generator Module #
#######################

def write_mkdir_script(commands: List[str], output_file: str = "commands_to_create_the_paths_manually") -> None:
    """
    Write mkdir commands to an output file, removing duplicates.
    
    Args:
        commands: List of mkdir commands
        output_file: Name of the output file
    """
    try:
        # Use a set to remove duplicate commands
        unique_commands = list(set(commands))
        # Sort the commands to ensure consistent output
        unique_commands.sort()
        
        with open(output_file, 'w') as file:
            for command in unique_commands:
                file.write(f"{command}\n")
        
        # Calculate how many duplicates were removed
        duplicates_removed = len(commands) - len(unique_commands)
        print(f"Successfully wrote {len(unique_commands)} mkdir commands to '{output_file}' (removed {duplicates_removed} duplicates)")
    except IOError as e:
        print(f"Error writing to file: {e}")


def get_output_filename(input_file: str) -> str:
    """
    Generate a name for the modified XML output file.
    
    Args:
        input_file: Path to the original XML file
        
    Returns:
        A filename for the modified XML file
    """
    # Get the file name without extension
    base_name = os.path.splitext(input_file)[0]
    # Create a new filename with "_modified.xml" suffix
    return f"{base_name}_modified.xml"


def prompt_for_output_filename(default_name: str) -> str:
    """
    Prompt the user for an output filename or use the default.
    
    Args:
        default_name: Default filename to suggest
        
    Returns:
        str: The selected output filename
    """
    suggestion = default_name
    user_input = input(f"\nEnter output filename (default: '{suggestion}'): ").strip()
    
    if not user_input:
        return suggestion
    
    # Ensure XML extension
    if not user_input.lower().endswith('.xml'):
        user_input += ".xml"
        
    return user_input


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
    print("\n" + "=" * 80)
    print(" " * 20 + "IMPORTANT COMPATIBILITY NOTICE")
    print("=" * 80)
    print("This utility is specifically designed to process XML files that have been exported")
    print("without dependencies from the BLDM tool. Processing XML files with dependencies")
    print("or from other sources may result in incomplete transformations, missed references,")
    print("or other unexpected behavior.")
    print("Ensure the generated XML maintains proper reference integrity")
    print("\nProceeding with incompatible XML formats may lead to partial or incorrect results.")
    print("=" * 80)
    
    # Request acknowledgment from the user
    while True:
        acknowledgment = input("\nDo you confirm that your XML file complies with the compatibility requirements? (y/n): ").lower()
        if acknowledgment == 'y':
            print("Proceeding with file processing...")
            return
        elif acknowledgment == 'n':
            print("Please export an XML file without dependencies from BLDM before proceeding.")
            sys.exit(0)
        else:
            print("Please enter 'y' to acknowledge and continue, or 'n' to exit.")

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
    Main function to orchestrate the XML processing workflow.
    """
    print("=== XML Path Processor ===")
    print("This program will:")
    print("1. Extract paths from specific XML tags")
    print("2. Generate mkdir commands with a prefix")
    print("3. Create a modified XML file with updated paths")
    print("4. Update SFTP host IP (optional)")
    print("5. Update SFTP username (optional)")
    print("6. Update encrypted SFTP password (optional)")
    print("7. Update Password not required field to 'No'(optional)")
    print("8. Set 'Default Stopped' to 'True' for all collectors (optional)")
    print("===========================")
    
    # Display compatibility warning and get user acknowledgment
    display_xml_compatibility_warning()
    
    # Get and validate the XML file path
    while True:
        file_path = prompt_for_file_path()
        if validate_file_path(file_path):
            break
        # Get and validate the XML file path
        file_path = prompt_for_file_path()
        if validate_file_path(file_path):
            break
    
    # Ask the user which operations they want to perform
    operations = []
    print("\nSelect operations to perform (y/n for each):")
    
    # Paths processing
    if get_yes_no_input("Process paths in XML? (y/n): "):
        operations.append("paths")
    
    # SFTP host update
    if get_yes_no_input("Update SFTP host IP? (y/n): "):
        operations.append("host")
    
    # SFTP username update
    if get_yes_no_input("Update SFTP username? (y/n): "):
        operations.append("username")
    
    # SFTP password update
    if get_yes_no_input("Update encrypted SFTP password? (y/n): "):
        operations.append("password")
    
    # SFTP pass flags update
    if get_yes_no_input("Update SFTP 'Password Not Required Field' to no? (y/n): "):
        operations.append("flags")
    
    # Default Stopped State update 
    if get_yes_no_input("Set 'Default Stopped' to 'True' for all collectors? (y/n): "):
        operations.append("default_stopped")
        
    if not operations:
        print("No operations selected. Exiting.")
        return
    
    # Prompt for output file name
    default_output = get_output_filename(file_path)
    output_file = prompt_for_output_filename(default_output)
    
    # Create a temporary working file for each operation
    temp_file = f"{os.path.splitext(output_file)[0]}_temp{os.path.splitext(output_file)[1]}"
    
    # Start with the original file
    current_input = file_path
    
    # Process paths if selected
    if "paths" in operations:
        prefix_path = prompt_for_prefix_path()
        
        # Process the XML file to collect all paths
        all_paths = []
        print("\nProcessing XML file for paths...")
        for line in read_xml_lines(current_input):
            extractions = extract_paths_from_line(line)
            all_paths.extend([(tag, path) for tag, path, _ in extractions])
        
        if not all_paths:
            print("No matching path tags found in the XML file.")
        else:
            print(f"Found {len(all_paths)} paths to process.")
            
            # Create mkdir commands
            mkdir_commands = create_mkdir_commands(all_paths, prefix_path)
            
            # Write the mkdir commands to a file
            write_mkdir_script(mkdir_commands)
            
            # Generate the modified XML file
            regenerate_xml(current_input, temp_file, prefix_path)
            
            # Update the current input for the next operation
            current_input = temp_file
    
    # Update SFTP host if selected
    if "host" in operations:
        new_host = prompt_for_sftp_host()
        print(f"\nUpdating SFTP host to: {new_host} (in both ppsSFTPHostF and neSFTPClientHostF tags)")
        
        # Create a new temporary file for this operation
        temp_output = f"{os.path.splitext(output_file)[0]}_temp2{os.path.splitext(output_file)[1]}"
        
        success = update_sftp_host(current_input, temp_output, new_host)
        
        if success:
            print("SFTP host updated successfully.")
            
            # Remove the old temp file if it's not the original input
            if current_input != file_path:
                try:
                    os.remove(current_input)
                except OSError:
                    pass
                    
            current_input = temp_output
        else:
            print("Failed to update SFTP host.")
    
    # Update SFTP username if selected
    if "username" in operations:
        new_username = prompt_for_sftp_username()
        print(f"\nUpdating SFTP username to: {new_username} (in both ppsSFTPUserF and neSFTPClientUserF tags)")
        
        # Create a new temporary file for this operation
        temp_output = f"{os.path.splitext(output_file)[0]}_temp3{os.path.splitext(output_file)[1]}"
        
        success = update_sftp_username(current_input, temp_output, new_username)
        
        if success:
            print("SFTP username updated successfully.")
            
            # Remove the old temp file if it's not the original input
            if current_input != file_path:
                try:
                    os.remove(current_input)
                except OSError:
                    pass
                    
            current_input = temp_output
        else:
            print("Failed to update SFTP username.")
    
    # Update SFTP password if selected
    if "password" in operations:
        new_password = prompt_for_encrypted_password()
        print("\nUpdating SFTP encrypted password...")
        
        # Create a new temporary file for this operation
        temp_output = f"{os.path.splitext(output_file)[0]}_temp4{os.path.splitext(output_file)[1]}"
        
        success = update_sftp_password(current_input, temp_output, new_password)
        
        if success:
            print("SFTP password updated successfully.")
            
            # Remove the old temp file if it's not the original input
            if current_input != file_path:
                try:
                    os.remove(current_input)
                except OSError:
                    pass
                    
            current_input = temp_output
        else:
            print("Failed to update SFTP password.")
    
    # Update SFTP pass flags if selected
    if "flags" in operations:
        print("\nUpdating all SFTP Password not required field to 0...")
        
        # Create a new temporary file for this operation
        temp_output = f"{os.path.splitext(output_file)[0]}_temp5{os.path.splitext(output_file)[1]}"
        
        success = update_sftp_pass_flags(current_input, temp_output)
        
        if success:
            print("SFTP password not required field updated successfully to No.")
            
            # Remove the old temp file if it's not the original input
            if current_input != file_path:
                try:
                    os.remove(current_input)
                except OSError:
                    pass
                    
            current_input = temp_output
        else:
            print("Failed to update password not required field to 'No'.")
    
    # Update Default Stopped State if selected (new section)
    if "default_stopped" in operations:
        print("\nUpdating all collectors to 'Default Stopped' state...")
        
        # Create a new temporary file for this operation
        temp_output = f"{os.path.splitext(output_file)[0]}_temp6{os.path.splitext(output_file)[1]}"
        
        success = update_default_stopped_state(current_input, temp_output)
        
        if success:
            print("Default Stopped state updated successfully to True for all collectors.")
            
            # Remove the old temp file if it's not the original input
            if current_input != file_path:
                try:
                    os.remove(current_input)
                except OSError:
                    pass
                    
            current_input = temp_output
        else:
            print("Failed to update Default Stopped state.")
    
    # Rename the final temporary file to the desired output file
    if current_input != file_path:
        try:
            # If the output file already exists (from a previous run), remove it
            if os.path.exists(output_file):
                os.remove(output_file)
                
            os.rename(current_input, output_file)
            print(f"\nFinal output saved to: '{output_file}'")
        except OSError as e:
            print(f"Error renaming final output file: {e}")
            print(f"Final output is available at: '{current_input}'")
    else:
        # No operations modified the file
        print("\nNo modifications were made to the XML file.")
    
    # Clean up any temporary files that might have been left behind
    for i in range(1, 7):  # Now check up to _temp6 since we added another operation
        temp_path = f"{os.path.splitext(output_file)[0]}_temp{i}{os.path.splitext(output_file)[1]}"
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
    
    print("\nProcessing complete!")
    
    # Summarize operations performed
    summary_items = []
    if "paths" in operations:
        summary_items.append("Mkdir commands saved to: 'commands_to_create_the_paths_manually'")
    
    if any(op in operations for op in ["paths", "host", "username", "password", "flags", "default_stopped"]):
        summary_items.append(f"Modified XML saved to: '{output_file}'")
    
    # Print summary with numbers
    for idx, item in enumerate(summary_items, 1):
        print(f"{idx}. {item}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)
        