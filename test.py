import os

def list_directory(path="."):
    try:
        files = os.listdir(path)
        print(f"Contents of '{path}':")
        for f in files:
            print(f)
    except FileNotFoundError:
        print(f"Error: The directory '{path}' does not exist.")
    except PermissionError:
        print(f"Error: You don't have permission to access '{path}'.")

# Example usage
list_directory(r"C:\Users\Aby Sebastian\Downloads\MeterialIcons\src\device\4g_mobiledata")  # current directory
