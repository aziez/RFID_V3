
import re
import customtkinter
import serial.tools.list_ports

class Main(customtkinter.CTk):
    stateScan = "disabled"
    stateSet = "disabled"
    statePort = "disabled"

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
        customtkinter.set_default_color_theme("blue")
        self.configure()

    def get_available_ports(self):
        ports = list(serial.tools.list_ports.comports())
        filtered_ports = [port for port, desc, hwid in ports if "CH340" in desc]
        port = filtered_ports
        if not filtered_ports:
            port = ["Port Tidak Terdeteksi"]
        else :
            port = port
            self.statePort = "active"

        return port

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
        # self.filtered_ports = [port for port in self.portCom if "USB SERIAL CH340" in port]

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

        # Set up the trace to monitor changes in the input field
        self.inputPosVar = customtkinter.StringVar()
        self.inputPos.configure(textvariable=self.inputPosVar)
        self.inputPosVar.trace("w", self.on_pos_entry_change)

    def on_pos_entry_change(self, *args):
        pos = self.inputPosVar.get()
        if pos:
            self.stateSet = "active"
        else:
            self.stateSet = "disabled"

        # Update the state of the buttons
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
        self.dataVariable.set("0909888817817718787")

        self.dataUid = customtkinter.CTkButton(self, width=500, height=20, state="disabled", corner_radius=0, text_color_disabled="#0dc900", text="0909888817817718787", font=customtkinter.CTkFont(weight="bold", size=36),)
        self.dataUid.grid(row=0, column=1, columnspan=2, pady=(5, 20), sticky="nsew")
        self.labelLatest = customtkinter.CTkLabel(self, text="LATEST USER ID",
                                                  font=customtkinter.CTkFont(size=18, weight="bold"))
        self.labelLatest.grid(row=1, column=1, pady=(0, 10))
        self.entry = customtkinter.CTkEntry(self, state="disabled", placeholder_text="Demo Data in here",textvariable=self.dataVariable, font=customtkinter.CTkFont(family="Arial", size=30))
        self.entry.grid(row=2, column=1, columnspan=2, padx=(20, 20), pady=(0, 10), sticky="nsew")

        self.scanBtn = customtkinter.CTkButton(self, state=self.stateScan, text="SCAN DATA", width=200, height=50, font=customtkinter.CTkFont(weight="bold"), hover_color="darkgreen", command=self.trigerScan)
        self.scanBtn.grid(row=3, column=1, padx=20, pady=0)

    def trigerScan(self):
        self.dataVariable.set("DATA BERASIL NERUBAHHH")

    def setReader(self):
        port = self.listPort.get()
        pos = self.inputPos.get()
        self.stateScan = "active"  # Set stateScan to "active" when the button is clicked
        self.portLabel = customtkinter.CTkLabel(self.tabView.tab("PORT"), text=port,
                                                font=customtkinter.CTkFont(size=28, weight="bold"))
        self.portLabel.grid(row=0, column=0, padx=20, pady=20)

        self.posLabel = customtkinter.CTkLabel(self.tabView.tab("POS"), text=pos,
                                               font=customtkinter.CTkFont(size=28, weight="bold"))
        self.posLabel.grid(row=0, column=0, padx=20, pady=20)
        self.scanBtn.configure(state=self.stateScan)

if __name__ == "__main__":
    app = Main()
    app.mainloop()