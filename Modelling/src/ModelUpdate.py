# Called by task scheduler periodically to handle updating the operational model to the next time iteration,
# and discard the preceding model outputs to prevent storage overflow.

import subprocess
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    filename='../data/op_model_log.txt',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def delete_file_if_exists(directory, filename):
    """
    Deletes a file from the specified directory if it exists.

    Parameters:
    - directory: str, path to the directory
    - filename: str, name of the file to delete
    """
    file_path = os.path.join(directory, filename)
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
            logging.info(f"Deleted file: {file_path}")
        else:
            logging.info(f"File not found (nothing to delete): {file_path}")
    except Exception as e:
        logging.error(f"Error deleting file {file_path}: {e}")


def rename_file_if_exists(directory, old_name, new_name):
    """
    Renames a file in the specified directory if it exists.

    Parameters:
    - directory: str, path to the directory
    - old_name: str, current name of the file
    - new_name: str, new name for the file
    """
    old_path = os.path.join(directory, old_name)
    new_path = os.path.join(directory, new_name)
    try:
        if os.path.isfile(old_path):
            os.rename(old_path, new_path)
            logging.info(f"Renamed file: {old_path} → {new_path}")
        else:
            logging.info(f"File to rename not found: {old_path}")
    except Exception as e:
        logging.error(f"Error renaming file {old_path} to {new_path}: {e}")



def run_batch_file(batch_path):
    """
    Runs a Windows batch file and waits for it to complete.

    Parameters:
    - batch_path: str, full path to the .bat file
    """
    try:
        subprocess.run(batch_path, check=True, shell=True)
        logging.info(f"Batch file executed successfully: {batch_path}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Batch file failed with return code {e.returncode}: {batch_path}")
    except FileNotFoundError:
        logging.error(f"Batch file not found: {batch_path}")



def updateMDU(filename, updates):
    """
    Applies tag-value replacements in a file and inserts a timestamped comment and empty line at line 3.

    Parameters:
    - filename: str, path to the file to edit
    - updates: dict, where keys are tags and values are the new values
    """
    # Read the file
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        updated_lines = []
        for line in lines:
            stripped = line.strip()
            replaced = False
            for tag, new_value in updates.items():
                if stripped.startswith(tag):
                    if '#' in line:
                        content, comment = line.split('#', 1)
                        comment = '#' + comment
                    else:
                        content, comment = line, ''
                    prefix = content[:len(tag)]
                    updated_line = f"{prefix}{new_value}{comment}\n"
                    updated_lines.append(updated_line)
                    replaced = True
                    break
            if not replaced:
                updated_lines.append(line)

        # Replace line 3 (index 2) with a timestamped comment
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        comment_line = f"# Updated on {timestamp}\n"
        if len(updated_lines) >= 3:
            updated_lines[2] = comment_line
        else:
            logging.warning(f"File {filename} has fewer than 3 lines; cannot replace line 3.")

        with open(filename, 'w', encoding='utf-8') as file:
            file.writelines(updated_lines)

        logging.info(f"File updated successfully: {filename}")
    except Exception as e:
        logging.error(f"Error updating file {filename}: {e}")


from datetime import datetime, timedelta


def update_times(data, key, name_prefix="name"):
    """
    Updates the value for a given key in the dictionary with a timestamped filename.

    Parameters:
    - data: dict, the dictionary to update
    - key: str, the key whose value should be replaced
    - name_prefix: str, the prefix for the filename (default is 'name')
    """
    timestamp = datetime.now() + timedelta(hours=1)
    formatted_time = timestamp.strftime("%Y%m%d_%H%M%S")
    filename = f"{name_prefix}_{formatted_time}_rst.nc"
    data[key] = filename


def update_forcings(directory, old_name, new_name):
    """
    Updates the forcing files by deleting the old one and renaming the new one.

    Parameters:
    - directory: str, path to the directory containing the forcing files
    - old_name: str, name of the old forcing file to delete
    - new_name: str, name of the new forcing file to rename
    """
    delete_file_if_exists(directory, old_name)
    rename_file_if_exists(directory, new_name, old_name)


# Model parameters
batch_file = "../data/FlowFM.bat"  # Path to the batch file, which calls the DIMR file, which specifies the model.
TUnit = "S"  # Time unit for the model, e.g., 'S' for seconds
update_interval = 3600  # How frequently is the model re-run, in TUnit (3600 s = 1 hour)
run_duration = 259200  # Run duration in TUnit (259200 s = 72 hours)
map_interval = 3600  # Map file output interval in TUnit
his_interval = 3600  # History file output interval in TUnit
forcing_directory = "../data/forcings"

# All .mdu fields which must be updated for the next model iteration:
new_values = {
    "RestartFile                       = ": "FlowFM_20240425_000000_rst.nc",
    "TStart                            = ": "FlowAM_nyet.nc",
    "TStop                             = ": "7",
}

if __name__ == "__main__":
    # update_times()
    updateMDU("../data/FlowFM.mdu", new_values)
    # run_batch_file(r"C:\path.bat")
