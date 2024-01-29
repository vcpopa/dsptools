[![Build Status](https://github.com/vpopaRWH/dsptools/actions/workflows/black.yml/badge.svg)](https://github.com/vpopaRWH/dsptools/actions/workflows/black.yml)

[![Pylint Status](https://github.com/vpopaRWH/dsptools/actions/workflows/pylint.yml/badge.svg)](https://github.com/vpopaRWH/dsptools/actions/workflows/pylint.yml)

[![pytest Status](https://github.com/vpopaRWH/dsptools/actions/workflows/pytest.yml/badge.svg)](https://github.com/vpopaRWH/dsptools/actions/workflows/pytest.yml)

## Requirements

- [Putty.exe](https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html): You must have Putty.exe installed and added to your system's PATH. This executable is required for some functionalities in this package.

## Installation

1. **Install Python Package:** Install this Python package using `pip`:

    ```bash
    cd path/to/root/dsptools
    pip install . -e
    ```

2. **Install Putty.exe:** Download Putty.exe from the official website [here](https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html) if you don't already have it installed.

3. **Add Putty.exe to PATH:**
   - Add the path to Putty.exe to your system's PATH environment variable. The exact steps for doing this depend on your operating system.
   - You can test if Putty.exe is correctly added to PATH by opening a command prompt and running `putty -h`. If it displays the Putty help message, it's configured correctly.

4. **Use the Package:** You can now use the package with the Putty.exe dependency properly configured.
