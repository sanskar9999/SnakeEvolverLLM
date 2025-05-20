import os
import hashlib
from collections import defaultdict
import time # For modification times

def get_file_hash(filepath):
    """Calculates the SHA256 hash of a file's content."""
    hasher = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(4096)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()
    except IOError:
        print(f"Error: Could not read file {filepath}")
        return None

def find_and_remove_duplicates(folder_path, dry_run=False):
    """
    Finds files with duplicate content in the given folder,
    keeps the oldest, and removes the rest after confirmation.
    Only considers .py files.
    """
    if not os.path.isdir(folder_path):
        print(f"Error: Folder '{folder_path}' not found.")
        return

    # Store tuples of (filepath, modification_time)
    file_details_by_hash = defaultdict(list)
    files_processed_count = 0
    deleted_files_count = 0

    print(f"Scanning folder: {folder_path} for .py files...")

    for filename in os.listdir(folder_path):
        if filename.endswith(".py"):
            filepath = os.path.join(folder_path, filename)
            if os.path.isfile(filepath):
                file_hash = get_file_hash(filepath)
                if file_hash:
                    try:
                        # Get last modification time
                        mod_time = os.path.getmtime(filepath)
                        file_details_by_hash[file_hash].append((filepath, mod_time))
                        files_processed_count += 1
                    except OSError as e:
                        print(f"Error getting modification time for {filepath}: {e}")

    if files_processed_count == 0:
        print("No .py files found to process.")
        return

    print(f"\n--- Processing Duplicates (Oldest will be kept) ---")
    found_any_duplicates = False

    for file_hash, file_infos in file_details_by_hash.items():
        if len(file_infos) > 1:
            found_any_duplicates = True
            # Sort files by modification time (oldest first)
            # file_infos is a list of (filepath, mod_time) tuples
            file_infos.sort(key=lambda item: item[1])

            oldest_file_path, oldest_mod_time = file_infos[0]
            print(f"\nDuplicate set (Hash: {file_hash}):")
            print(f"  Keeping (oldest): {os.path.basename(oldest_file_path)} (Modified: {time.ctime(oldest_mod_time)})")

            files_to_remove = file_infos[1:] # All files except the oldest

            for file_to_remove_path, mod_time in files_to_remove:
                print(f"  Identified for removal: {os.path.basename(file_to_remove_path)} (Modified: {time.ctime(mod_time)})")
                if not dry_run:
                    confirm = input(f"    Confirm removal of '{os.path.basename(file_to_remove_path)}'? (yes/no): ").strip().lower()
                    if confirm == 'yes':
                        try:
                            os.remove(file_to_remove_path)
                            print(f"    REMOVED: {os.path.basename(file_to_remove_path)}")
                            deleted_files_count += 1
                        except OSError as e:
                            print(f"    Error removing {os.path.basename(file_to_remove_path)}: {e}")
                    else:
                        print(f"    SKIPPED removal of {os.path.basename(file_to_remove_path)}")
                else:
                    print(f"    DRY RUN: Would remove {os.path.basename(file_to_remove_path)}")
            print("-" * 30)

    if not found_any_duplicates:
        print("\nNo duplicate .py files found by content.")
    else:
        if dry_run:
            print(f"\n--- Dry Run Summary ---")
            print(f"If not a dry run, {len([fi for fi_list in file_details_by_hash.values() for fi in fi_list[1:]])} files would have been candidates for removal.")
        else:
            print(f"\n--- Summary ---")
            print(f"Total .py files processed: {files_processed_count}")
            print(f"Total files removed: {deleted_files_count}")

if __name__ == "__main__":
    target_folder = input("Enter the path to the folder containing Python files: ")

    if target_folder and os.path.isdir(target_folder):
        print("\n" + "="*50)
        print("WARNING: This script can delete files.")
        print("It will identify duplicate .py files by content, keep the oldest,")
        print("and ask for confirmation before deleting the newer duplicates.")
        print("="*50 + "\n")

        mode = input("Run in (D)ry run mode (shows what would be deleted) or (R)eal mode (will delete files)? (d/r): ").strip().lower()

        if mode == 'd':
            print("\n--- Starting DRY RUN ---")
            find_and_remove_duplicates(target_folder, dry_run=True)
        elif mode == 'r':
            confirm_real = input(f"ARE YOU SURE you want to proceed with REAL mode for folder '{target_folder}'? This will delete files. (yes/no): ").strip().lower()
            if confirm_real == 'yes':
                print("\n--- Starting REAL MODE (files will be deleted after confirmation) ---")
                find_and_remove_duplicates(target_folder, dry_run=False)
            else:
                print("Real mode not confirmed. Exiting.")
        else:
            print("Invalid mode selected. Exiting. Please choose 'd' or 'r'.")
    else:
        print("Invalid folder path provided or folder does not exist.")