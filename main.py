import tkinter
import tkinter.messagebox
import customtkinter

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("green")


class Main(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("800x400")
        self.title("Power RFID V.3 By: Aziz")

        self.grid_columnconfigure(1, weight=1)
        self.columnconfigure((2, 3), weight=0)
        self.rowconfigure((1, 1, 2), weight=1)

        # SIDEBAR FRAME
        self.sidebar_frame = customtkinter.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)
        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="KONFIGURASI RFID",
                                                 font=customtkinter.CTkFont(size=15, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.comLabel = customtkinter.CTkLabel(self.sidebar_frame, text="PORT",
                                               font=customtkinter.CTkFont(size=10, weight="bold"))
        self.comLabel.grid(row=1, column=0)

        self.input_RFID = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["COM1", "COM2", "COM3", "COM4"])
        self.input_RFID.grid(row=2, column=0, padx=20, pady=(0, 10))

        self.posLabel = customtkinter.CTkLabel(self.sidebar_frame, text="POSISI",
                                               font=customtkinter.CTkFont(size=10, weight="bold"))
        self.posLabel.grid(row=3, column=0)

        self.input_POS = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["1", "2", "3", "4"])
        self.input_POS.grid(row=4, column=0, pady=(0, 25))

        self.sidebar_button_1 = customtkinter.CTkButton(self.sidebar_frame, text="Set RFID")
        self.sidebar_button_1.grid(row=5, column=0, padx=20, pady=10)


app = Main()
app.mainloop()
