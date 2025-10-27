from importlib import metadata
import subprocess
import sys
from pathlib import Path
import os



from app_settings import REQUIREMENTS_FILE

def check_and_install_packages(requirements_file=REQUIREMENTS_FILE):
    """Main function to handle package dependencies check and installation"""
    print(f"\nStarting package management process...")
    
    # Read requirements
    try:
        with open(requirements_file, 'r') as file:
            dependencies = [line.strip() for line in file if line.strip() and not line.startswith('#')]
        if not dependencies:
            print("No dependencies found in requirements file.")
            return False
    except FileNotFoundError:
        print(f"Error: Could not find {requirements_file}")
        return False
    except Exception as e:
        print(f"Error reading requirements file: {e}")
        return False

    print("\nChecking and installing packages...")
    for dep in dependencies:
        pkg_name = dep.split('==')[0]
        
        # Check if package is installed
        try:
            installed_version = metadata.version(pkg_name)
            print(f"✓ Package '{pkg_name}' is installed (version {installed_version})")
            continue
        except metadata.PackageNotFoundError:
            print(f"→ Installing missing package: {dep}")
            
            # Install package
            try:
                subprocess.check_call(
                    [sys.executable, '-m', 'pip', 'install', dep],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE
                )
                print(f"✓ Successfully installed {dep}")
            except subprocess.CalledProcessError as e:
                print(f"✗ Error installing {dep}: {e.stderr.decode()}")
                return False
    
    print("\n✓ All packages are now installed and up to date!")
    return True

if __name__ == "__main__":
    success = check_and_install_packages()
    if not success:
        print("\n✗ Package installation process failed")
        sys.exit(1)
    sys.exit(0)