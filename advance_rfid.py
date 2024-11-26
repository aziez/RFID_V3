import re
import threading
import tkinter as tk
import customtkinter as ctk
import serial
import serial.tools.list_ports
import requests
from typing import List, Optional
from CTkMessagebox import CTkMessagebox


class RFIDReaderConfig:
    """Configuration constants and utility methods for RFID reader."""
    PRESET_VALUE = 0xFFFF
    POLYNOMIAL = 0x8408
    NO_READER = 'FF'

    @staticmethod
    def calculate_crc(cmd: str) -> bytes:
        """Calculate CRC for RFID command."""
        cmd_bytes = bytes.fromhex(cmd)
        crc_value = RFIDReaderConfig.PRESET_VALUE

        for byte in cmd_bytes:
            crc_value ^= byte
            for _ in range(8):
                if crc_value & 0x0001:
                    crc_value = (crc_value >> 1) ^ RFIDReaderConfig.POLYNOMIAL
                else:
                    crc_value >>= 1

        crc_h = (crc_value >> 8) & 0xFF
        crc_l = crc_value & 0xFF

        return cmd_bytes + bytes([crc_l, crc_h])


class RFIDCommands:
    """RFID communication command templates."""

    def __init__(self, no_reader: str):
        self.INVENTORY1 = f'06 {no_reader} 01 00 06'  # Read TID
        self.INVENTORY2 = f'04 {no_reader} 0F'  # Read EPC
        self.READ_TAG_MEM = f'12 {no_reader} 02 02 11 22 33 44 01 00 04 00 00 00 00 00 02'
        self.WRITE_EPC = '0F 03 04 03 00 00 00 00 11 22 33 44 55 66'
        self.SET_ADDRESS = '05 03 24 00'


class RFIDReaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self._setup_window()
        self._initialize_variables()
        self._setup_ui()

    def _setup_window(self):
        """Configure main window settings."""
        self.geometry("1000x600")
        self.title("Advanced RFID Reader")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.grid_columnconfigure((1, 2), weight=1)
        self.grid_rowconfigure(2, weight=1)

    def _initialize_variables(self):
        """Initialize application state variables."""
        self.port_state = "disabled"
        self.set_state = "disabled"
        self.scan_state = "disabled"

        self.current_port = ""
        self.current_position = ""
        self.latest_uid = "00000000"

        self.serial_connection = None
        self.scan_thread = None

        self.rfid_config = RFIDReaderConfig()
        self.rfid_commands = RFIDCommands(RFIDReaderConfig.NO_READER)

        # API Configuration
        self.api_enabled = ctk.BooleanVar(value=False)
        self.api_url = ctk.StringVar(value='https://registrasi.ptbi.co.id/web/rfid')

    def _setup_ui(self):
        """Set up the entire user interface."""
        self._create_sidebar()
        self._create_main_content()
        self._create_api_config_frame()
        self._refresh_available_ports()

    def _create_sidebar(self):
        """Create the sidebar frame and its components."""
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=10)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew", padx=10, pady=10)
        self.sidebar_frame.grid_rowconfigure(6, weight=1)

        self._create_sidebar_components()

    def _create_sidebar_components(self):
        """Create individual sidebar components."""
        # Logo and Title
        ctk.CTkLabel(
            self.sidebar_frame,
            text="RFID READER CONFIG",
            font=ctk.CTkFont(size=20, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Port Selection
        ctk.CTkLabel(
            self.sidebar_frame,
            text="Serial Port",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=1, column=0, padx=20, pady=(10, 5), sticky="w")

        self.port_menu = ctk.CTkOptionMenu(
            self.sidebar_frame,
            state=self.port_state,
            values=["Select Port"],
            width=200
        )
        self.port_menu.grid(row=2, column=0, padx=20, pady=(0, 10))

        # Position Input
        ctk.CTkLabel(
            self.sidebar_frame,
            text="Position",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=3, column=0, padx=20, pady=(10, 5), sticky="w")

        self.position_entry = self._create_numeric_entry()
        self.position_entry.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Set Reader Button
        self.set_reader_button = ctk.CTkButton(
            self.sidebar_frame,
            text="CONFIGURE READER",
            command=self._configure_reader,
            state=self.set_state,
            width=200
        )
        self.set_reader_button.grid(row=5, column=0, padx=20, pady=10)

    def _create_numeric_entry(self):
        """Create a numeric-only entry field."""
        validate_cmd = self.register(self._validate_numeric)
        entry = ctk.CTkEntry(
            self.sidebar_frame,
            validate="key",
            validatecommand=(validate_cmd, "%P"),
            placeholder_text="Enter Position Number"
        )
        entry.bind("<KeyRelease>", self._on_position_change)
        return entry

    @staticmethod
    def _validate_numeric(value: str) -> bool:
        """Validate that input is numeric."""
        return bool(re.match(r"^[0-9]*$", value))

    def _on_position_change(self, event):
        """Update UI state when position changes."""
        self.set_state = "active" if self.position_entry.get() else "disabled"
        self.set_reader_button.configure(state=self.set_state)

    def _create_main_content(self):
        """Create the main content area."""
        # UID Display Frame
        uid_frame = ctk.CTkFrame(self, corner_radius=10)
        uid_frame.grid(row=0, column=1, columnspan=2, padx=10, pady=10, sticky="nsew")

        # UID Label
        ctk.CTkLabel(
            uid_frame,
            text="Detected User ID",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 5))

        # UID Display
        self.uid_display = ctk.CTkLabel(
            uid_frame,
            text=self.latest_uid,
            font=ctk.CTkFont(weight="bold", size=36),
            text_color="#0dc900"
        )
        self.uid_display.pack(pady=10)

        # Scan Control Frame
        scan_frame = ctk.CTkFrame(self, corner_radius=10)
        scan_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        # Scan Button
        self.scan_button = ctk.CTkButton(
            scan_frame,
            text="START SCAN",
            command=self._toggle_scan,
            state=self.scan_state,
            width=250,
            height=50,
            font=ctk.CTkFont(weight="bold", size=16)
        )
        self.scan_button.pack(padx=20, pady=20)

    def _create_api_config_frame(self):
        """Create API configuration frame."""
        api_frame = ctk.CTkFrame(self, corner_radius=10)
        api_frame.grid(row=1, column=2, padx=10, pady=10, sticky="nsew")

        # API Enable Toggle
        self.api_toggle = ctk.CTkSwitch(
            api_frame,
            text="Enable API Integration",
            variable=self.api_enabled,
            command=self._toggle_api
        )
        self.api_toggle.pack(padx=20, pady=(20, 10))

        # API URL Entry
        ctk.CTkLabel(
            api_frame,
            text="API Endpoint URL",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(padx=20, pady=(10, 5))

        self.api_url_entry = ctk.CTkEntry(
            api_frame,
            textvariable=self.api_url,
            width=300
        )
        self.api_url_entry.pack(padx=20, pady=(0, 10))

        # Request Status Label
        self.api_status_label = ctk.CTkLabel(
            api_frame,
            text="",
            text_color="#0dc900"
        )
        self.api_status_label.pack(padx=20, pady=10)

    def _toggle_api(self):
        """Toggle API functionality."""
        is_enabled = self.api_enabled.get()
        self.api_url_entry.configure(state="normal" if is_enabled else "disabled")
        if not is_enabled:
            self.api_status_label.configure(text="API Disabled")

    def _refresh_available_ports(self):
        """Refresh and list available ports."""
        ports = [port.device for port in serial.tools.list_ports.comports() if "CH340" in port.description]
        ports = ports if ports else ["No Port Detected"]

        self.port_menu.configure(values=ports)
        self.port_state = "active" if ports != ["No Port Detected"] else "disabled"
        self.port_menu.configure(state=self.port_state)

    def _configure_reader(self):
        """Configure the RFID reader connection."""
        try:
            port = self.port_menu.get()
            position = self.position_entry.get()

            self.serial_connection = serial.Serial(port, 57600, timeout=0.1)
            self.current_port = port
            self.current_position = position

            self.scan_button.configure(state="active")
            self.scan_state = "active"
            CTkMessagebox(title="Success", message=f"Connected to port {port}")

        except (serial.SerialException, TypeError) as e:
            CTkMessagebox(title="PORT ERROR", message=str(e))
            self.port_menu.set("No Port Detected")
            self.position_entry.delete(0, tk.END)
            self.scan_button.configure(state="disabled")
            self.scan_state = "disabled"

    def _toggle_scan(self):
        """Toggle scanning state."""
        if not hasattr(self, 'is_scanning'):
            self.is_scanning = False

        if not self.is_scanning:
            self._start_scanning()
        else:
            self._stop_scanning()

    def _start_scanning(self):
        """Start the RFID scanning process."""
        self.set_reader_button.configure(state='disabled')
        self.scan_button.configure(text="STOP SCAN", fg_color="red")
        self.is_scanning = True
        self._scan_loop()

    def _stop_scanning(self):
        """Stop the RFID scanning process."""
        self.set_reader_button.configure(state='normal')
        self.scan_button.configure(text="START SCAN", fg_color=None)
        self.is_scanning = False
        if self.scan_thread:
            self.scan_thread.cancel()

    def _scan_loop(self):
        """Continuous scanning loop."""
        if not self.is_scanning:
            return

        try:
            self._send_scan_command()
        except Exception as e:
            print(f"Scan error: {e}")
            self._stop_scanning()

        self.scan_thread = threading.Timer(1.0, self._scan_loop)
        self.scan_thread.start()

    def _send_scan_command(self):
        """Send scan command and process response."""
        if not self.serial_connection:
            return

        data_scan = self.rfid_config.calculate_crc(self.rfid_commands.INVENTORY1)
        self.serial_connection.write(data_scan)
        response = self.serial_connection.read(512)

        if not response:
            self._handle_no_response()
            return

        uid = self._process_response(response)
        if uid:
            self._handle_uid(uid)

    def _process_response(self, response):
        """Process serial response and extract UID."""
        response_hex = response.hex().upper()
        hex_list = [response_hex[i:i + 2] for i in range(0, len(response_hex), 2)]
        hex_space = ' '.join(hex_list)

        if "FB" in hex_space or "FE" in hex_space or not hex_space:
            return None

        return hex_space[-6:].replace(" ", "")

    def _handle_uid(self, uid):
        """Handle detected UID."""
        if uid == self.latest_uid:
            return

        self.latest_uid = uid
        self.uid_display.configure(text=self.latest_uid)

        # API Integration (Optional)
        if self.api_enabled.get():
            try:
                response = requests.get(
                    self.api_url.get(),
                    params={'pos': self.current_position, 'kode': uid}
                )
                status = f"API Response: {response.status_code}"
                status_color = "#0dc900" if response.status_code == 200 else "red"
                self.api_status_label.configure(text=status, text_color=status_color)
            except Exception as e:
                self.api_status_label.configure(
                    text=f"API Error: {e}",
                    text_color="red"
                )

    def _handle_no_response(self):
        """Handle scenarios with no serial response."""
        self.set_reader_button.configure(state='normal')
        self.scan_button.configure(text="START SCAN", fg_color=None)
        self.is_scanning = False


def main():
    app = RFIDReaderApp()
    app.mainloop()


if __name__ == "__main__":
    main()