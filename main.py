

import re
import customtkinter
import requests
import serial.tools.list_ports
import threading
from CTkMessagebox import CTkMessagebox
from serial import *
import serial
from apscheduler.schedulers.background import BlockingScheduler


class Main(customtkinter.CTk):
    stateScan = "disabled"
    stateSet = "disabled"
    statePort = "disabled"

    # VARIABLE
    port = ""
    pos = ""
    no_reader = 'FF'
    uid_str = None
    start = False
    thread = None
    test_serial = None
    console = None
    epcValue = None
    uidLatest = "00000000"
    sendApi = None
    twin = False

    # PRESET RFID
    PRESET_Value = 0xFFFF
    POLYMONIAL = 0x8408

    # PROTOCOL SCANNER RFID
    # scan
    INVENTORY1 = f'06 {no_reader} 01 00 06'  # Membaca TID
    INVENTORY2 = f'04 {no_reader} 0F'  # Membaca EPC

    # Read EPC
    readTagMem = f'12 {no_reader} 02 02 11 22 33 44 01 00 04 00 00 00 00 00 02'

    # Change EPC
    writeEpc = '0F 03 04 03 00 00 00 00 11 22 33 44 55 66'

    # Set Data
    setAddress = '05 03 24 00'

    # API SENDER VARIABLE
    url = 'https://registrasi.ptbi.co.id/web/rfid'
    data_kartu = []

    @staticmethod
    def crc(cmd):
        cmd = bytes.fromhex(cmd)
        uiCrcValue = Main.PRESET_Value
        for x in range((len(cmd))):
            uiCrcValue = uiCrcValue ^ cmd[x]
            for y in range(8):
                if (uiCrcValue & 0x0001):
                    uiCrcValue = (uiCrcValue >> 1) ^ Main.POLYMONIAL
                else:
                    uiCrcValue = uiCrcValue >> 1
        crc_H = (uiCrcValue >> 8) & 0xFF
        crc_L = uiCrcValue & 0xFF
        cmd = cmd + bytes([crc_L])
        cmd = cmd + bytes([crc_H])
        return cmd

    def __init__(self):
        super().__init__()
        self.geometry("800x400")
        self.title("Power RFID V.3 By: Aziz")
        self.set_color_theme()
        self.grid_columnconfigure(1, weight=1)
        self.columnconfigure((2, 3), weight=0)
        self.rowconfigure((1, 2), weight=0)

        self.portCom = self.get_available_ports()

        self.create_sidebar()
        self.create_main_content()

    def set_color_theme(self):
        customtkinter.set_appearance_mode("Light")
        customtkinter.set_default_color_theme("blue")
        self.configure()

    def get_available_ports(self):
        ports = list(serial.tools.list_ports.comports())
        filtered_ports = [port.device for port in ports if "CH340" in port.description]
        if not filtered_ports:
            filtered_ports = ["Port Tidak Terdeteksi"]
        else:
            self.statePort = "active"
        return filtered_ports

    def create_sidebar(self):
        self.sidebar_frame = customtkinter.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        self.create_sidebar_components()

    def create_sidebar_components(self):
        self.create_logo_label()
        self.create_com_label()
        self.create_list_port_option_menu()
        self.create_pos_label()
        self.create_input_pos_entry()
        self.create_sidebar_button()
        self.create_tab_view()

    def create_logo_label(self):
        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="KONFIGURASI RFID",
                                                 font=customtkinter.CTkFont(size=15, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

    def create_com_label(self):
        self.comLabel = customtkinter.CTkLabel(self.sidebar_frame, text="PORT",
                                               font=customtkinter.CTkFont(size=10, weight="bold"))
        self.comLabel.grid(row=1, column=0)

    def create_list_port_option_menu(self):
        self.listPort = customtkinter.CTkOptionMenu(self.sidebar_frame, state=self.statePort, values=self.portCom)
        self.listPort.grid(row=2, column=0, padx=20, pady=(0, 10))

    def create_pos_label(self):
        self.posLabel = customtkinter.CTkLabel(self.sidebar_frame, text="POSISI",
                                               font=customtkinter.CTkFont(size=10, weight="bold"))
        self.posLabel.grid(row=3, column=0)

    def create_input_pos_entry(self):
        def validate_numeric_input(new_value):
            return re.match("^[0-9]*$", new_value) is not None

        validate_command = self.register(validate_numeric_input)

        self.inputPos = customtkinter.CTkEntry(self.sidebar_frame, validate="key",
                                               validatecommand=(validate_command, "%P"))
        self.inputPos.grid(row=4, column=0, pady=(0, 25))

        self.inputPosVar = customtkinter.StringVar()
        self.inputPos.configure(textvariable=self.inputPosVar)
        self.inputPosVar.trace("w", self.on_pos_entry_change)

    def on_pos_entry_change(self, *args):
        global test_serial, pos
        pos = self.inputPosVar.get()
        test_serial = Serial().close()

        if pos:
            self.stateSet = "active"
            self.sidebar_button_1.configure(state=self.stateSet)
        else:
            self.stateSet = "disabled"
            self.sidebar_button_1.configure(state=self.stateSet)

    def create_sidebar_button(self):
        self.sidebar_button_1 = customtkinter.CTkButton(self.sidebar_frame, state=self.stateSet, text="SET READER", width=100, height=50, font=customtkinter.CTkFont(weight="bold"), command=self.setReader, hover_color="blue")
        self.sidebar_button_1.grid(row=5, column=0, padx=20, pady=10)

    def create_tab_view(self):
        self.tabView = customtkinter.CTkTabview(self.sidebar_frame, width=120, height=80)
        self.tabView.grid(row=7, column=0)
        self.tabView.add("PORT")
        self.tabView.add("POS")
        self.tabView.tab("PORT").grid_columnconfigure(0, weight=1)
        self.tabView.tab("POS").grid_columnconfigure(0, weight=1)

    def create_main_content(self):
        self.dataVariable = customtkinter.StringVar()
        self.dataVariable.set("0000000")

        self.dataUid = customtkinter.CTkButton(self, width=500, height=20, state="disabled", corner_radius=0, text_color_disabled="#0dc900", text=self.uidLatest, font=customtkinter.CTkFont(weight="bold", size=36))
        self.dataUid.grid(row=0, column=1, columnspan=2, pady=(5, 20), sticky="nsew")
        self.labelLatest = customtkinter.CTkLabel(self, text="USER ID DATA", font=customtkinter.CTkFont(size=18, weight="bold"))
        self.labelLatest.grid(row=1, column=1, pady=(0, 10))
        self.entry = customtkinter.CTkEntry(self, state="disabled", placeholder_text="Demo Data in here", textvariable=self.dataVariable, font=customtkinter.CTkFont(family="Arial", size=30))
        self.entry.grid(row=2, column=1, columnspan=2, padx=(20, 20), pady=(0, 10), sticky="nsew")

        self.scanBtn = customtkinter.CTkButton(self, state=self.stateScan, text="SCAN DATA", width=200, height=50, font=customtkinter.CTkFont(weight="bold"), hover_color="darkgreen", command=self.triggerScan)
        self.scanBtn.grid(row=3, column=1, padx=20, pady=0)

    def setReader(self):
        global test_serial, pos
        self.stateSet = "disabled"
        self.sidebar_button_1.configure(state=self.stateSet)

        try:
            port = self.listPort.get()
            pos = self.inputPos.get()
            test_serial = Serial(port, 57600, timeout=0.1)
            self.portLabel = customtkinter.CTkLabel(self.tabView.tab("PORT"), text=port,
                                                    font=customtkinter.CTkFont(size=28, weight="bold"))
            self.portLabel.grid(row=0, column=0, padx=20, pady=20)
            self.posLabel = customtkinter.CTkLabel(self.tabView.tab("POS"), text=pos,
                                                   font=customtkinter.CTkFont(size=28, weight="bold"))
            self.posLabel.grid(row=0, column=0, padx=20, pady=20)
            self.scanBtn.configure(state="active")
        except serial.SerialException as e:
            CTkMessagebox(title="PORT TIDAK TERBUKA", message=e)
            self.listPort.set("Port Tidak Terdeteksi")
            self.inputPos.delete(0, "end")
            self.inputPos.focus()
            self.scanBtn.configure(state="disabled")
        except TypeError as e:
            print(f"Port Closed{e}")
            self.scanBtn.configure(state="disabled")

    def triggerScan(self):
        if self.start:
            self.start = False
            self.inputPos.configure(state="normal")
            self.scanBtn.configure(text="START SCAN")

        else:
            self.start = True
            self.scanBtn.configure(text="STOP SCAN")
            self.inputPos.configure(state="disabled")
            self.dataVariable.set("")
            self.sendData()


    def send_cmd(self, cmd):
        global test_serial, dataVariable, uidLatest, pos, url, dataUid

        data_scan = self.crc(cmd)
        test_serial.write(data_scan)
        response = test_serial.read(512)
        response_hex = response.hex().upper()
        hex_list = [response_hex[i:i + 2] for i in range(0, len(response_hex), 2)]
        hex_space = ' '.join(hex_list)
        uid = hex_space[-6:]
        uid_str = uid.replace(" ", "")
        data_scan = {
            'kode': uid_str,
            'pos': pos
        }

        if hex_space.find("FB") != -1:
            self.dataVariable.set("")
            self.dataVariable.set("Kartu Tidak Terdeteksi \n")
        elif hex_space.find("FE") != -1:
            self.dataVariable.set("")
            self.dataVariable.set("Kartu Tidak Terdeteksi \n")
        elif hex_space == "":
            self.thread.cancel()  # Check if self.thread exists before canceling it
            self.start = False
            self.sidebar_button_1.configure(state="actived")
            self.dataVariable.set("")
            self.dataVariable.set("PORT TIDAK TERDETEKSI \n")
            self.inputPos.delete(3, "end")
            self.inputPos.focus()
            self.scanBtn.configure(text="START SCAN")
        else:
            if uid_str == self.uidLatest:
                self.dataVariable.set("")
                self.dataVariable.set("PASS DOUBLE DATA \n")
            else:
                self.uidLatest = uid_str
                sendApi = requests.get(self.url, params={'pos': self.pos, 'kode': self.uid_str})
                self.dataUid.configure(text=f"{self.uidLatest}")
                self.dataVariable.set("")
                self.dataVariable.set(f"UID : {uid_str} \n Status : {sendApi} \n")

    def sendData(self):
        if self.start:
            self.send_cmd(self.INVENTORY1)
            self.thread = threading.Timer(0, self.sendData)
            self.thread.start()
        elif self.thread is not None and isinstance(self.thread, threading.Timer):
            self.thread.cancel()
            self.thread = None
            self.dataVariable.set("SCANNER STOPPED")

if __name__ == "__main__":
    app = Main()
    app.mainloop()
