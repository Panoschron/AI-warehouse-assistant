from importlib import metadata
import subprocess
import sys

def read_requirements(file_path):
    """Reads a requirements file and returns a list of dependencies."""
    try:
        with open(file_path, 'r') as file:
            requirements = [line.strip() for line in file if line.strip() and not line.startswith('#')]
        return requirements
    except FileNotFoundError:
        print(f"Error: Could not find {file_path}")
        return []
    except Exception as e:
        print(f"Error reading file: {e}")
        return []
    
print("Reading dependencies from requirements.txt...")

def check_installed_packages(dependencies):
    "check if the required packages are installed"
    print("Checking installed packages...")

    for dep in dependencies:
        pkg_name = dep.split('==')[0]  # Get package name without version
        try:
            installed_version = metadata.version(pkg_name)
            print(f"Package '{pkg_name}' is installed with version {installed_version}.")
        except metadata.PackageNotFoundError:
            print(f"Package '{pkg_name}' is NOT installed.")

def install_missing_packages(dependencies):
    "install missing packages using pip"

    for dep in dependencies:
        pkg_name = dep.split('==')[0]  # Get package name without version
        try:
            metadata.version(pkg_name)
        except metadata.PackageNotFoundError:
            print(f"Installing missing package: {dep}")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', dep])

if __name__ == "__main__":  # Fixed syntax
    
    dependencies =read_requirements('requirements.txt')
    check_installed_packages(dependencies)
    install_missing_packages(dependencies)