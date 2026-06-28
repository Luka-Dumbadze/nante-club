import customtkinter as ctk
from core.database import initialize_db
from ui.gui import LoginApp

if __name__ == "__main__":
    # 1. ვაინიციალიზებთ მონაცემთა ბაზას და მარაგებს
    initialize_db()
    
    # 2. ვაყენებთ პროგრამის დიზაინის თემას
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    
    # 3. ვუშვებთ აპლიკაციას ავტორიზაციის ფანჯრიდან
    app = LoginApp()
    app.mainloop()