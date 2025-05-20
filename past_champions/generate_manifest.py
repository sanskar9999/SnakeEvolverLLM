import os
import json
import re

def create_champion_name(filename):
    """
    Creates a more human-readable name from the Python filename.
    Example: "CautiousCobra_Gen1.py" -> "CautiousCobra Gen1"
             "my_snake_ai.py" -> "My Snake Ai"
    """
    name_without_extension = filename.replace(".py", "")
    # Replace underscores with spaces
    name_with_spaces = name_without_extension.replace("_", " ")
    # Attempt to capitalize words (simple version)
    parts = name_with_spaces.split(' ')
    capitalized_parts = []
    for part in parts:
        if part: # Avoid empty strings if there are multiple spaces
            # Handle "GenX" specifically to keep it as "GenX" not "Genx"
            if part.lower().startswith("gen") and len(part) > 3 and part[3:].isdigit():
                capitalized_parts.append(part[:3].capitalize() + part[3:])
            else:
                capitalized_parts.append(part.capitalize())
    return " ".join(capitalized_parts)

def generate_manifest(directory="."):
    """
    Scans the given directory for .py files and generates a champions_manifest.json.
    """
    champions = []
    print(f"Scanning directory: {os.path.abspath(directory)}")

    for filename in os.listdir(directory):
        if filename.endswith(".py") and filename != os.path.basename(__file__): # Exclude this script itself
            champion_name = create_champion_name(filename)
            champions.append({
                "name": champion_name,
                "file": filename
            })
            print(f"  Found: {filename} -> Named: {champion_name}")

    if not champions:
        print("No .py files (potential champions) found in this directory.")
        return

    # Sort by name for a consistent manifest (optional)
    champions.sort(key=lambda x: x["name"])

    manifest_filepath = os.path.join(directory, "champions_manifest.json")
    try:
        with open(manifest_filepath, "w") as f:
            json.dump(champions, f, indent=4)
        print(f"\nSuccessfully generated '{manifest_filepath}' with {len(champions)} champions.")
    except IOError as e:
        print(f"\nError writing manifest file: {e}")

if __name__ == "__main__":
    # Assuming this script is run from within the past_champions directory
    generate_manifest()
    input("Press Enter to exit...") # Keeps window open on Windows if run by double-click