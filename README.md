# RFID Reader Project

Welcome to the **RFID Reader Project**! This project is built with Python and uses a range of libraries to create a robust RFID reading application. It includes a graphical user interface (GUI) built with **CustomTkinter** and serial communication with **pyserial**. The project can be easily packaged into an executable using **PyInstaller**.

## Features
- **CustomTkinter**: A modern GUI framework built on Tkinter for creating attractive interfaces.
- **Pyserial**: Communicates with RFID hardware via serial port.
- **CTkMessagebox**: To display interactive message boxes in the GUI.
- **Requests**: For making HTTP requests if required by the application.
- **PyInstaller**: To package the project into a standalone executable.

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [How to Build the Executable](#how-to-build-the-executable)
- [Dependencies](#dependencies)
- [Driver Installation](#driver-installation)
- [Contributing](#contributing)
- [License](#license)

## Installation

### Step 1: Clone the repository

First, clone the repository to your local machine:
#### git clone https://github.com/aziez/RFID_V3.git cd rfid-reader

### Step 2: Set Up Virtual Environment

It’s recommended to use a virtual environment to manage dependencies. Run the following commands to create and activate the virtual environment.

#### For Windows: 
python -m venv venv venv\Scripts\activate


#### For macOS/Linux:
python3 -m venv venv source venv/bin/activate


### Step 3: Install Dependencies

Once the virtual environment is activated, install the required dependencies by running:

pip install -r requirements.txt

This will install the following packages:
- `customtkinter`
- `pyserial`
- `requests`
- `pyinstaller`
- `CTkMessagebox`

## Usage

### Running the Application

To run the application, simply execute the main Python script:
python main.py

This will start the RFID reader application with the GUI.

### How to Build the Executable

If you want to package the application as a standalone executable using **PyInstaller**, follow these steps:

1. Make sure you have installed the dependencies by running:
pip install -r requirements.txt

2. Run the following command to create the executable:
python build_executable.py

This will generate a single executable in the `dist` folder with the name `RFIDReader` (or whatever name you set in `build_executable.py`).

### Driver Installation

The application communicates with an RFID reader via a serial port. You may need to install a USB-to-serial driver for the communication to work correctly. Download the driver from [this link](https://www.wch.cn/downloads/file/65.html) and follow the installation instructions for your operating system.

- **Windows Driver Installation**:
    1. Download the driver from the link above.
    2. Run the installer and follow the on-screen instructions.
    3. After installation, restart your computer (if necessary).

## Dependencies

The following Python packages are required to run the application:
customtkinter pyserial requests pyinstaller CTkMessagebox

You can install them all at once by running:
pip install -r requirements.txt

## Contributing

We welcome contributions to this project! If you’d like to contribute, follow these steps:

1. Fork the repository on GitHub.
2. Clone your fork to your local machine.
3. Create a new branch (`git checkout -b feature-branch`).
4. Make your changes and commit them (`git commit -am 'Add new feature'`).
5. Push your changes to your fork (`git push origin feature-branch`).
6. Open a pull request on GitHub.

### Reporting Issues

If you encounter any bugs or issues, please report them by creating a new issue on the [GitHub Issues](https://github.com/yourusername/rfid-reader/issues) page.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Thank you for using the RFID Reader Project! We hope you find it useful. If you have any questions or need assistance, feel free to reach out.










