import re
import threading
import tkinter as tk
import customtkinter as ctk
import serial
import serial.tools.list_ports
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
        self.geometry("800x400")
        self.title("Power RFID V.3 By: Aziz")
        ctk.set_appearance_mode("Light")
        ctk.set_default_color_theme("green")
        self.grid_columnconfigure(1, weight=1)

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

    def _setup_ui(self):
        """Set up the entire user interface."""
        self._create_sidebar()
        self._create_main_content()
        self._refresh_available_ports()

    def _create_sidebar(self):
        """Create the sidebar frame and its components."""
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        self._create_sidebar_components()

    def _create_sidebar_components(self):
        """Create individual sidebar components."""
        self._create_logo_label()
        self._create_port_section()
        self._create_position_section()
        self._create_set_reader_button()
        self._create_tab_view()

    def _create_logo_label(self):
        ctk.CTkLabel(
            self.sidebar_frame,
            text="KONFIGURASI RFID",
            font=ctk.CTkFont(size=15, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(20, 10))

    def _create_port_section(self):
        """Create port selection components."""
        ctk.CTkLabel(
            self.sidebar_frame,
            text="PORT",
            font=ctk.CTkFont(size=10, weight="bold")
        ).grid(row=1, column=0)

        self.port_menu = ctk.CTkOptionMenu(
            self.sidebar_frame,
            state=self.port_state,
            values=["Select Port"]
        )
        self.port_menu.grid(row=2, column=0, padx=20, pady=(0, 10))

    def _create_position_section(self):
        """Create position input components."""
        ctk.CTkLabel(
            self.sidebar_frame,
            text="POSISI",
            font=ctk.CTkFont(size=10, weight="bold")
        ).grid(row=3, column=0)

        self.position_entry = self._create_numeric_entry()
        self.position_entry.grid(row=4, column=0, pady=(0, 25))

    def _create_numeric_entry(self):
        """Create a numeric-only entry field."""
        validate_cmd = self.register(self._validate_numeric)
        entry = ctk.CTkEntry(
            self.sidebar_frame,
            validate="key",
            validatecommand=(validate_cmd, "%P")
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

    def _create_set_reader_button(self):
        """Create the 'SET READER' button."""
        self.set_reader_button = ctk.CTkButton(
            self.sidebar_frame,
            state=self.set_state,
            text="SET READER",
            width=100,
            height=50,
            font=ctk.CTkFont(weight="bold"),
            command=self._configure_reader,
            hover_color="blue"
        )
        self.set_reader_button.grid(row=5, column=0, padx=20, pady=10)

    def _create_tab_view(self):
        """Create a tab view for port and position display."""
        self.tab_view = ctk.CTkTabview(self.sidebar_frame, width=120, height=80)
        self.tab_view.grid(row=7, column=0)
        self.tab_view.add("PORT")
        self.tab_view.add("POS")

    def _create_main_content(self):
        """Create the main content area."""
        self.uid_var = ctk.StringVar(value="0000000")

        # UID Display Button
        self.uid_display = ctk.CTkButton(
            self, width=500, height=20,
            state="disabled",
            corner_radius=0,
            text_color_disabled="#0dc900",
            text=self.latest_uid,
            font=ctk.CTkFont(weight="bold", size=36)
        )
        self.uid_display.grid(row=0, column=1, columnspan=2, pady=(5, 20), sticky="nsew")

        # Latest UID Label
        ctk.CTkLabel(
            self, text="USER ID DATA",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=1, column=1, pady=(0, 10))

        # Data Entry
        self.data_entry = ctk.CTkEntry(
            self,
            state="disabled",
            placeholder_text="Scan RFID Tag",
            textvariable=self.uid_var,
            font=ctk.CTkFont(family="Arial", size=30)
        )
        self.data_entry.grid(row=2, column=1, columnspan=2, padx=(20, 20), pady=(0, 10), sticky="nsew")

        # Scan Button
        self.scan_button = ctk.CTkButton(
            self,
            state=self.scan_state,
            text="SCAN DATA",
            width=200, height=50,
            font=ctk.CTkFont(weight="bold"),
            hover_color="darkgreen",
            command=self._toggle_scan
        )
        self.scan_button.grid(row=3, column=1, padx=20, pady=0)

    def _refresh_available_ports(self):
        """Refresh and list available ports."""
        ports = [port.device for port in serial.tools.list_ports.comports() if "CH340" in port.description]
        ports = ports if ports else ["Port Tidak Terdeteksi"]

        self.port_menu.configure(values=ports)
        self.port_state = "active" if ports != ["Port Tidak Terdeteksi"] else "disabled"
        self.port_menu.configure(state=self.port_state)

    def _configure_reader(self):
        """Configure the RFID reader connection."""
        try:
            port = self.port_menu.get()
            position = self.position_entry.get()

            self.serial_connection = serial.Serial(port, 57600, timeout=0.1)
            self.current_port = port
            self.current_position = position

            # Update tab view with current port and position
            ctk.CTkLabel(
                self.tab_view.tab("PORT"),
                text=port,
                font=ctk.CTkFont(size=28, weight="bold")
            ).grid(row=0, column=0, padx=20, pady=20)

            ctk.CTkLabel(
                self.tab_view.tab("POS"),
                text=position,
                font=ctk.CTkFont(size=28, weight="bold")
            ).grid(row=0, column=0, padx=20, pady=20)

            self.scan_button.configure(state="active")
            self.scan_state = "active"

        except (serial.SerialException, TypeError) as e:
            CTkMessagebox(title="PORT ERROR", message=str(e))
            self.port_menu.set("Port Tidak Terdeteksi")
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
        self.scan_button.configure(text="STOP SCAN")
        self.uid_var.set("")
        self.is_scanning = True
        self._scan_loop()

    def _stop_scanning(self):
        """Stop the RFID scanning process."""
        self.set_reader_button.configure(state='normal')
        self.scan_button.configure(text="START SCAN")
        self.uid_var.set("")
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
            self.uid_var.set("Card Not Detected")
            return None

        return hex_space[-6:].replace(" ", "")

    def _handle_uid(self, uid):
        """Handle detected UID."""
        if uid == self.latest_uid:
            self.uid_var.set("DUPLICATE DATA")
            return

        self.latest_uid = uid
        self.uid_display.configure(text=self.latest_uid)
        self.uid_var.set(f"UID: {uid}")
        self.uid_var.set(f"UID: {uid}\nPosition: {self.current_position}")

    def _handle_no_response(self):
        """Handle scenarios with no serial response."""
        self.set_reader_button.configure(state='normal')
        self.uid_var.set("NO PORT DETECTED")
        self.scan_button.configure(text="START SCAN")
        self.is_scanning = False


def main():
    app = RFIDReaderApp()
    app.mainloop()


if __name__ == "__main__":
    main()