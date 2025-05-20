import os
import hashlib
from collections import defaultdict

def get_file_hash(filepath):
    """Calculates the SHA256 hash of a file's content."""
    hasher = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f: # Open in binary mode for hashing
            while True:
                chunk = f.read(4096) # Read in chunks to handle potentially larger files
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()
    except IOError:
        print(f"Error: Could not read file {filepath}")
        return None

def find_duplicate_files(folder_path):
    """
    Finds files with duplicate content in the given folder.
    Only considers .py files.
    """
    if not os.path.isdir(folder_path):
        print(f"Error: Folder '{folder_path}' not found.")
        return

    hashes = defaultdict(list) # A dictionary where keys are hashes, values are lists of filenames
    duplicate_sets = []

    print(f"Scanning folder: {folder_path} for .py files...")

    for filename in os.listdir(folder_path):
        if filename.endswith(".py"):
            filepath = os.path.join(folder_path, filename)
            if os.path.isfile(filepath): # Ensure it's a file, not a sub-directory
                file_hash = get_file_hash(filepath)
                if file_hash:
                    hashes[file_hash].append(filename)

    found_duplicates = False
    for file_hash, filenames in hashes.items():
        if len(filenames) > 1:
            if not found_duplicates:
                print("\n--- Duplicate Files Found ---")
                found_duplicates = True
            print(f"Content hash: {file_hash}")
            print("Files with this content:")
            for name in filenames:
                print(f"  - {name}")
            print("-" * 20)
            duplicate_sets.append(filenames) # Store for potential further processing

    if not found_duplicates:
        print("\nNo duplicate .py files found by content.")

    return duplicate_sets # Returns a list of lists, where each inner list contains names of duplicate files

if __name__ == "__main__":
    # Get folder path from user input
    target_folder = input("Enter the path to the folder containing Python files: ")

    # Or, you can hardcode it for testing:
    # target_folder = "./my_python_files" # Make sure this folder exists and has .py files

    if target_folder:
        duplicates = find_duplicate_files(target_folder)
        # if duplicates:
        #     print("\nSummary of duplicate sets:")
        #     for i, dup_set in enumerate(duplicates):
        #         print(f"Set {i+1}: {', '.join(dup_set)}")
    else:
        print("No folder path provided.")