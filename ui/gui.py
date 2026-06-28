import customtkinter as ctk
import sqlite3
import threading
import random
from datetime import datetime, timedelta

# ვაიმპორტებთ ჩვენს ლოგიკებს core ფოლდერიდან
from core.pos_terminal import EcrTerminalClient
from core.printer import send_to_printer


class ShiftCloseDialog(ctk.CTkToplevel):
    def __init__(self, parent, dashboard):
        super().__init__(parent)
        self.dashboard = dashboard
        self.title("ცვლის დახურვა")
        self.geometry("450x200")
        self.attributes("-topmost", True)
        self.resizable(False, False)
        
        ctk.CTkLabel(self, text="გსურთ ცვლის დახურვა და Z-რეპორტის ბეჭდვა?", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(30, 20))
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        ctk.CTkButton(btn_frame, text="✅ დიახ და გასვლა", fg_color="#27ae60", hover_color="#2ecc71", 
                      command=self.close_shift).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🚪 მხოლოდ გასვლა", fg_color="#e67e22", hover_color="#d35400", 
                      command=self.just_logout).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="გაუქმება", fg_color="#7f8c8d", hover_color="#95a5a6", 
                      command=self.destroy).pack(side="left", padx=10)

    def close_shift(self):
        self.dashboard.print_z_report()
        self.dashboard.perform_logout()
        self.destroy()

    def just_logout(self):
        self.dashboard.perform_logout()
        self.destroy()


class ReportsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("📊 ფინანსური სტატისტიკა და რეპორტები")
        self.geometry("800x650")
        self.attributes("-topmost", True)
        
        filter_frame = ctk.CTkFrame(self)
        filter_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(filter_frame, text="აირჩიეთ პერიოდი:", font=ctk.CTkFont(size=14)).pack(side="left", padx=10, pady=10)
        
        self.period_var = ctk.StringVar(value="დღეს")
        self.period_combo = ctk.CTkComboBox(filter_frame, variable=self.period_var, 
                                            values=["დღეს", "ბოლო 7 დღე", "ბოლო 30 დღე", "მთლიანი ისტორია"],
                                            command=self.load_statistics)
        self.period_combo.pack(side="left", padx=10, pady=10)
        
        self.stats_frame = ctk.CTkFrame(self)
        self.stats_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.create_stat_cards()
        self.load_statistics(self.period_var.get())

    def create_stat_cards(self):
        self.rev_frame = ctk.CTkFrame(self.stats_frame, corner_radius=10, fg_color="#2c3e50")
        self.rev_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(self.rev_frame, text="💰 ჯამური შემოსავალი", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        self.lbl_total = ctk.CTkLabel(self.rev_frame, text="0.00 ₾", font=ctk.CTkFont(size=24, weight="bold"), text_color="#f1c40f")
        self.lbl_total.pack()
        self.lbl_cash = ctk.CTkLabel(self.rev_frame, text="Cash: 0.00 ₾")
        self.lbl_cash.pack(pady=(10, 0))
        self.lbl_tbc = ctk.CTkLabel(self.rev_frame, text="TBC: 0.00 ₾")
        self.lbl_tbc.pack()
        self.lbl_bog = ctk.CTkLabel(self.rev_frame, text="BOG: 0.00 ₾")
        self.lbl_bog.pack(pady=(0, 10))

        self.source_frame = ctk.CTkFrame(self.stats_frame, corner_radius=10, fg_color="#2c3e50")
        self.source_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(self.source_frame, text="📈 შემოსავლის წყარო", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        self.lbl_time_rev = ctk.CTkLabel(self.source_frame, text="დროიდან: 0.00 ₾")
        self.lbl_time_rev.pack(pady=5)
        self.lbl_bar_rev = ctk.CTkLabel(self.source_frame, text="ბარიდან: 0.00 ₾")
        self.lbl_bar_rev.pack(pady=5)
        self.lbl_ps_vs_bill = ctk.CTkLabel(self.source_frame, text="ბილიარდი: 0 | PS: 0", text_color="#bdc3c7")
        self.lbl_ps_vs_bill.pack(pady=(15, 10))

        self.top_frame = ctk.CTkFrame(self.stats_frame, corner_radius=10, fg_color="#2c3e50")
        self.top_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(self.top_frame, text="🏆 ტოპ მაჩვენებლები", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        self.lbl_top_space = ctk.CTkLabel(self.top_frame, text="ყველაზე მოთხოვნადი სივრცე: -", font=ctk.CTkFont(size=14))
        self.lbl_top_space.pack(pady=5)
        self.lbl_top_product = ctk.CTkLabel(self.top_frame, text="ყველაზე გაყიდვადი პროდუქტი: -", font=ctk.CTkFont(size=14))
        self.lbl_top_product.pack(pady=10)

        self.stats_frame.grid_columnconfigure(0, weight=1)
        self.stats_frame.grid_columnconfigure(1, weight=1)

    def load_statistics(self, period):
        now = datetime.now()
        if period == "დღეს":
            date_filter = (now.replace(hour=0, minute=0, second=0, microsecond=0)).strftime('%Y-%m-%d %H:%M:%S')
        elif period == "ბოლო 7 დღე":
            date_filter = (now - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
        elif period == "ბოლო 30 დღე":
            date_filter = (now - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
        else:
            date_filter = '2000-01-01 00:00:00'

        conn = sqlite3.connect('nante_club.db')
        cursor = conn.cursor()

        cursor.execute('''SELECT SUM(total_paid), SUM(cash_amount), 
                          SUM(CASE WHEN terminal_type='TBC' THEN card_amount ELSE 0 END),
                          SUM(CASE WHEN terminal_type='BOG' THEN card_amount ELSE 0 END)
                          FROM Transactions WHERE transaction_date >= ?''', (date_filter,))
        totals = cursor.fetchone()
        t_total, t_cash, t_tbc, t_bog = [x or 0.0 for x in totals]

        self.lbl_total.configure(text=f"{t_total:.2f} ₾")
        self.lbl_cash.configure(text=f"Cash: {t_cash:.2f} ₾")
        self.lbl_tbc.configure(text=f"TBC: {t_tbc:.2f} ₾")
        self.lbl_bog.configure(text=f"BOG: {t_bog:.2f} ₾")

        cursor.execute("SELECT SUM(time_amount) FROM Sessions WHERE status='Completed' AND end_time >= ?", (date_filter,))
        time_rev = cursor.fetchone()[0] or 0.0

        cursor.execute('''SELECT SUM(so.subtotal) FROM SessionOrders so
                          JOIN Sessions s ON so.session_id = s.id
                          WHERE s.status='Completed' AND s.end_time >= ?''', (date_filter,))
        bar_rev = cursor.fetchone()[0] or 0.0

        self.lbl_time_rev.configure(text=f"დროიდან: {time_rev:.2f} ₾")
        self.lbl_bar_rev.configure(text=f"ბარიდან: {bar_rev:.2f} ₾")

        cursor.execute('''SELECT sp.type, SUM(s.time_amount) FROM Sessions s
                          JOIN Spaces sp ON s.space_id = sp.id
                          WHERE s.status='Completed' AND s.end_time >= ? GROUP BY sp.type''', (date_filter,))
        type_rev = cursor.fetchall()
        bill_rev = sum([r[1] for r in type_rev if 'Billiard' in r[0]])
        ps_rev = sum([r[1] for r in type_rev if 'PS' in r[0]])
        self.lbl_ps_vs_bill.configure(text=f"ბილიარდი: {bill_rev:.2f}₾ | PS: {ps_rev:.2f}₾")

        cursor.execute('''SELECT sp.name, SUM(s.time_amount) as total FROM Sessions s
                          JOIN Spaces sp ON s.space_id = sp.id
                          WHERE s.status='Completed' AND s.end_time >= ?
                          GROUP BY sp.id ORDER BY total DESC LIMIT 1''', (date_filter,))
        top_space = cursor.fetchone()
        self.lbl_top_space.configure(text=f"ყველაზე შემოსავლიანი სივრცე: {top_space[0]} ({top_space[1]:.2f}₾)" if top_space else "ყველაზე შემოსავლიანი სივრცე: -")

        cursor.execute('''SELECT p.name, SUM(so.quantity) as qty FROM SessionOrders so
                          JOIN Sessions s ON so.session_id = s.id JOIN Products p ON so.product_id = p.id
                          WHERE s.status='Completed' AND s.end_time >= ?
                          GROUP BY p.id ORDER BY qty DESC LIMIT 1''', (date_filter,))
        top_prod = cursor.fetchone()
        self.lbl_top_product.configure(text=f"ყველაზე გაყიდვადი პროდუქტი: {top_prod[0]} ({top_prod[1]} ცალი)" if top_prod else "ყველაზე გაყიდვადი პროდუქტი: -")
        
        conn.close()


class CartWindow(ctk.CTkToplevel):
    def __init__(self, parent, space_name, session_id):
        super().__init__(parent)
        self.title(f"🛒 ბარი - {space_name}")
        self.geometry("500x500")
        self.session_id = session_id
        
        self.products_frame = ctk.CTkScrollableFrame(self, width=220)
        self.products_frame.pack(side="left", fill="y", padx=10, pady=10)
        ctk.CTkLabel(self.products_frame, text="მენიუ", font=ctk.CTkFont(weight="bold")).pack(pady=5)

        self.cart_frame = ctk.CTkScrollableFrame(self, width=220)
        self.cart_frame.pack(side="right", fill="y", padx=10, pady=10)
        ctk.CTkLabel(self.cart_frame, text="მაგიდის კალათა", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        self.load_products()
        self.load_cart()

    def load_products(self):
        conn = sqlite3.connect('nante_club.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, price, stock_quantity FROM Products WHERE stock_quantity > 0")
        for prod_id, name, price, stock in cursor.fetchall():
            btn = ctk.CTkButton(self.products_frame, text=f"{name} - {price}₾", 
                                command=lambda p_id=prod_id, p_price=price: self.add_to_cart(p_id, p_price))
            btn.pack(pady=5)
        conn.close()

    def add_to_cart(self, product_id, price):
        conn = sqlite3.connect('nante_club.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO SessionOrders (session_id, product_id, quantity, subtotal) VALUES (?, ?, 1, ?)", 
                       (self.session_id, product_id, price))
        conn.commit()
        conn.close()
        self.load_cart() 

    def load_cart(self):
        for widget in self.cart_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                widget.destroy()

        conn = sqlite3.connect('nante_club.db')
        cursor = conn.cursor()
        cursor.execute('''SELECT so.id, p.name, so.quantity, so.subtotal FROM SessionOrders so
                          JOIN Products p ON so.product_id = p.id WHERE so.session_id = ?''', (self.session_id,))
        
        for order_id, name, qty, subtotal in cursor.fetchall():
            row = ctk.CTkFrame(self.cart_frame)
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{name} x{qty} = {subtotal}₾").pack(side="left", padx=5)
            ctk.CTkButton(row, text="X", width=30, fg_color="#c0392b", hover_color="#e74c3c",
                          command=lambda o_id=order_id: self.remove_from_cart(o_id)).pack(side="right", padx=5)
        conn.close()

    def remove_from_cart(self, order_id):
        conn = sqlite3.connect('nante_club.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM SessionOrders WHERE id=?", (order_id,))
        conn.commit()
        conn.close()
        self.load_cart()


class InventoryWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("📦 მარაგების მართვა")
        self.geometry("600x500")
        self.attributes("-topmost", True)
        self.grid_columnconfigure(0, weight=1)
        
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.refresh_list()

    def refresh_list(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        conn = sqlite3.connect('nante_club.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, price, stock_quantity FROM Products")
        
        for p_id, name, price, stock in cursor.fetchall():
            row = ctk.CTkFrame(self.scroll_frame)
            row.pack(fill="x", pady=5)
            ctk.CTkLabel(row, text=f"{name} ({price}₾) - მარაგშია: {stock} ცალი", width=300).pack(side="left", padx=10)
            ctk.CTkButton(row, text="+10", width=50, command=lambda idx=p_id: self.add_stock(idx, 10)).pack(side="right", padx=5)
            ctk.CTkButton(row, text="+1", width=50, command=lambda idx=p_id: self.add_stock(idx, 1)).pack(side="right", padx=5)
        conn.close()

    def add_stock(self, product_id, amount):
        conn = sqlite3.connect('nante_club.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE Products SET stock_quantity = stock_quantity + ? WHERE id = ?", (amount, product_id))
        conn.commit()
        conn.close()
        self.refresh_list()


class CheckoutWindow(ctk.CTkToplevel):
    TERMINAL_CONFIGS = {
        "TBC": {"host": "192.168.1.50", "port": 20008},
        "BOG": {"host": "192.168.1.51", "port": 20008}
    }

    def __init__(self, parent, space_card):
        super().__init__(parent)
        self.title(f"💳 გადახდა - {space_card.name}")
        self.geometry("600x550")
        self.attributes("-topmost", True)
        
        self.space_card = space_card
        self.session_id = space_card.session_id
        
        self.end_time = datetime.now()
        elapsed = self.end_time - self.space_card.start_time
        self.total_hours = elapsed.total_seconds() / 3600
        self.time_cost = self.total_hours * self.space_card.rate
        
        self.bar_orders = []
        self.bar_cost = 0.0
        self.total_amount = 0.0

        self.fetch_bar_orders()
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def fetch_bar_orders(self):
        conn = sqlite3.connect('nante_club.db')
        cursor = conn.cursor()
        cursor.execute('''SELECT p.id, p.name, so.quantity, so.subtotal 
                          FROM SessionOrders so JOIN Products p ON so.product_id = p.id
                          WHERE so.session_id = ?''', (self.session_id,))
        self.bar_orders = cursor.fetchall()
        self.bar_cost = sum(order[3] for order in self.bar_orders)
        self.total_amount = self.time_cost + self.bar_cost
        conn.close()

    def create_widgets(self):
        receipt_frame = ctk.CTkFrame(self, width=280)
        receipt_frame.pack(side="left", fill="y", padx=10, pady=10)
        
        ctk.CTkLabel(receipt_frame, text="🧾 დეტალური ჩეკი", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        
        time_text = f"დრო: {int(self.total_hours)}სთ {int((self.total_hours*60)%60)}წთ\nთანხა: {self.time_cost:.2f} ₾"
        ctk.CTkLabel(receipt_frame, text=time_text, justify="left").pack(anchor="w", padx=10, pady=5)
        
        if self.bar_orders:
            ctk.CTkLabel(receipt_frame, text="--- ბარი ---").pack(pady=5)
            for order in self.bar_orders:
                _, name, qty, subtotal = order
                ctk.CTkLabel(receipt_frame, text=f"{name} (x{qty}) - {subtotal:.2f} ₾").pack(anchor="w", padx=10)
                
        ctk.CTkLabel(receipt_frame, text="-"*30).pack(pady=10)
        ctk.CTkLabel(receipt_frame, text=f"სულ გადასახდელი:\n{self.total_amount:.2f} ₾", 
                     font=ctk.CTkFont(size=20, weight="bold"), text_color="#f39c12").pack(pady=10)

        payment_frame = ctk.CTkFrame(self, width=280)
        payment_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(payment_frame, text="გადახდის მეთოდი", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        ctk.CTkLabel(payment_frame, text="ნაღდი ფული (Cash) ₾:").pack(anchor="w", padx=20, pady=(10, 0))
        self.cash_entry = ctk.CTkEntry(payment_frame)
        self.cash_entry.pack(fill="x", padx=20, pady=5)
        self.cash_entry.insert(0, f"{self.total_amount:.2f}") 
        
        ctk.CTkLabel(payment_frame, text="ბარათი (Card) ₾:").pack(anchor="w", padx=20, pady=(10, 0))
        self.card_entry = ctk.CTkEntry(payment_frame)
        self.card_entry.pack(fill="x", padx=20, pady=5)
        self.card_entry.insert(0, "0.00")
        
        ctk.CTkLabel(payment_frame, text="რომელ ტერმინალზე გატარდა?").pack(anchor="w", padx=20, pady=(10, 0))
        self.terminal_combo = ctk.CTkComboBox(payment_frame, values=["None", "TBC", "BOG"])
        self.terminal_combo.pack(fill="x", padx=20, pady=5)

        self.error_label = ctk.CTkLabel(payment_frame, text="", text_color="red")
        self.error_label.pack(pady=5)

        self.confirm_btn = ctk.CTkButton(payment_frame, text="✅ გადახდის დასრულება", fg_color="#27ae60", hover_color="#2ecc71", 
                      command=self.confirm_payment)
        self.confirm_btn.pack(pady=20, padx=20, fill="x")

    def format_receipt_text(self, cash_paid, card_paid, total):
        receipt = "\n"
        receipt += "       NANTE CLUB       \n"
        receipt += "------------------------\n"
        receipt += f"თარიღი: {self.end_time.strftime('%Y-%m-%d %H:%M')}\n"
        receipt += f"მაგიდა: {self.space_card.name}\n"
        receipt += f"მოლარე: {self.space_card.cashier_name}\n"
        receipt += "------------------------\n"
        receipt += f"დრო ({int(self.total_hours)}სთ {int((self.total_hours*60)%60)}წთ): {self.time_cost:.2f} GEL\n"
        
        if self.bar_orders:
            receipt += "ბარი:\n"
            for order in self.bar_orders:
                _, name, qty, subtotal = order
                receipt += f"{name} (x{qty}) - {subtotal:.2f} GEL\n"
                
        receipt += "------------------------\n"
        receipt += f"სულ ჯამი:     {total:.2f} GEL\n"
        receipt += f"ნაღდი ფული:   {cash_paid:.2f} GEL\n"
        receipt += f"ბარათი:       {card_paid:.2f} GEL\n"
        receipt += "------------------------\n"
        receipt += "  გმადლობთ სტუმრობისთვის!  \n"
        receipt += "\n\n\n\n\n"
        return receipt

    def run_terminal_payment_thread(self, card_amount, terminal_type):
        config = self.TERMINAL_CONFIGS.get(terminal_type)
        if not config:
            self.after(0, lambda: self.payment_failure_callback("ტერმინალის კონფიგურაცია ვერ მოიძებნა!"))
            return

        amount_minor = int(round(card_amount * 100))
        txn_number = (self.session_id % 1000) if self.session_id else random.randint(1, 999)

        try:
            with EcrTerminalClient(config["host"], config["port"]) as ecr:
                result = ecr.sale(amount_minor=amount_minor, txn_number=txn_number)
                if result.approved:
                    self.after(0, self.payment_success_callback)
                else:
                    self.after(0, lambda: self.payment_failure_callback(f"უარყოფილია: {result.error_code}"))
        except Exception as e:
            err_msg = f"კავშირი ვერ დამყარდა: {e}\nშეამოწმეთ IP და ქსელი!"
            self.after(0, lambda: self.payment_failure_callback(err_msg))

    def payment_success_callback(self):
        self.save_transaction_to_db()

    def payment_failure_callback(self, error_message):
        self.confirm_btn.configure(state="normal", text="✅ გადახდის დასრულება")
        self.cash_entry.configure(state="normal")
        self.card_entry.configure(state="normal")
        self.terminal_combo.configure(state="normal")
        self.error_label.configure(text=error_message, text_color="red")

    def save_transaction_to_db(self):
        cash_amount = float(self.cash_entry.get() if self.cash_entry.get() else 0)
        card_amount = float(self.card_entry.get() if self.card_entry.get() else 0)
        terminal = self.terminal_combo.get()
        total_needed = round(self.total_amount, 2)
        cashier = self.space_card.cashier_name

        conn = sqlite3.connect('nante_club.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('''INSERT INTO Transactions (session_id, cash_amount, card_amount, terminal_type, total_paid, cashier_name) 
                              VALUES (?, ?, ?, ?, ?, ?)''', 
                           (self.session_id, cash_amount, card_amount, terminal, total_needed, cashier))
            cursor.execute("UPDATE Sessions SET end_time=?, time_amount=?, status='Completed' WHERE id=?", 
                           (self.end_time.strftime('%Y-%m-%d %H:%M:%S'), self.time_cost, self.session_id))
            cursor.execute("UPDATE Spaces SET is_active=0 WHERE id=?", (self.space_card.space_id,))
            
            cursor.execute("SELECT product_id, quantity FROM SessionOrders WHERE session_id=?", (self.session_id,))
            for product_id, quantity in cursor.fetchall():
                cursor.execute("UPDATE Products SET stock_quantity = stock_quantity - ? WHERE id = ?", (quantity, product_id))
            
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            self.payment_failure_callback(f"ბაზის შეცდომა: {e}")
            return
        finally:
            conn.close()

        # აქ ვიყენებთ import-ს `core.printer`-დან
        receipt_text = self.format_receipt_text(cash_amount, card_amount, total_needed)
        send_to_printer(receipt_text, "Nante Receipt")

        self.space_card.finalize_stop()
        self.destroy()

    def confirm_payment(self):
        try:
            cash_amount = float(self.cash_entry.get() if self.cash_entry.get() else 0)
            card_amount = float(self.card_entry.get() if self.card_entry.get() else 0)
            terminal = self.terminal_combo.get()
            
            total_input = round(cash_amount + card_amount, 2)
            total_needed = round(self.total_amount, 2)
            
            if total_input < total_needed:
                self.error_label.configure(text=f"შეყვანილი თანხა აკლია ჯამს!", text_color="red")
                return
                
            if card_amount > 0 and (terminal == "None" or not terminal):
                self.error_label.configure(text="აირჩიეთ ტერმინალი (TBC/BOG)!", text_color="red")
                return

            if card_amount > 0:
                self.error_label.configure(text="დაუკავშირდით ტერმინალს, გაატარეთ ბარათი...", text_color="orange")
                self.confirm_btn.configure(state="disabled", text="⏳ მიმდინარეობს გადახდა...")
                self.cash_entry.configure(state="disabled")
                self.card_entry.configure(state="disabled")
                self.terminal_combo.configure(state="disabled")
                self.update() 
                threading.Thread(target=self.run_terminal_payment_thread, args=(card_amount, terminal), daemon=True).start()
            else:
                self.save_transaction_to_db()

        except ValueError:
            self.error_label.configure(text="გთხოვთ შეიყვანოთ სწორი რიცხვები!", text_color="red")

    def on_close(self):
        self.space_card.resume_timer()
        self.destroy()


class SpaceCard(ctk.CTkFrame):
    def __init__(self, parent, space_id, name, rate, is_active, session_start_time=None, cashier_name=""):
        super().__init__(parent, corner_radius=10, border_width=2, border_color="#34495e")
        self.space_id, self.name, self.rate, self.is_active = space_id, name, rate, is_active
        self.start_time, self.timer_id, self.session_id = None, None, None
        self.cashier_name = cashier_name
        
        if session_start_time:
            self.start_time = datetime.strptime(session_start_time, '%Y-%m-%d %H:%M:%S.%f') if '.' in session_start_time else datetime.strptime(session_start_time, '%Y-%m-%d %H:%M:%S')
            self.fetch_active_session_id()

        self.name_label = ctk.CTkLabel(self, text=self.name, font=ctk.CTkFont(size=18, weight="bold"))
        self.name_label.pack(pady=(15, 5))
        self.rate_label = ctk.CTkLabel(self, text=f"{self.rate:g} ₾ / 1 სთ", text_color="#7f8c8d").pack()
        self.status_label = ctk.CTkLabel(self, text="🟢 თავისუფალი", font=ctk.CTkFont(size=14))
        self.status_label.pack(pady=5)
        self.time_label = ctk.CTkLabel(self, text="00:00:00", font=ctk.CTkFont(size=24, weight="bold"))
        self.time_label.pack(pady=(10, 0))
        self.cost_label = ctk.CTkLabel(self, text="0.00 ₾", font=ctk.CTkFont(size=20, weight="bold"), text_color="#f39c12")
        self.cost_label.pack(pady=(0, 10))
        
        self.bar_btn = ctk.CTkButton(self, text="🛒 ბარი", fg_color="#2980b9", hover_color="#3498db", command=self.open_cart)
        self.action_btn = ctk.CTkButton(self, text="▶ Start", fg_color="#27ae60", hover_color="#2ecc71", command=self.toggle_session)
        self.action_btn.pack(pady=(5, 15), padx=20, fill="x")

        if self.is_active:
            self.set_active_ui()
            self.update_timer()

    def fetch_active_session_id(self):
        conn = sqlite3.connect('nante_club.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM Sessions WHERE space_id=? AND status='Active'", (self.space_id,))
        res = cursor.fetchone()
        if res: self.session_id = res[0]
        conn.close()

    def toggle_session(self):
        if not self.is_active: self.start_session()
        else: self.stop_session()

    def start_session(self):
        self.start_time = datetime.now()
        self.is_active = True
        
        conn = sqlite3.connect('nante_club.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE Spaces SET is_active=1 WHERE id=?", (self.space_id,))
        cursor.execute("INSERT INTO Sessions (space_id, start_time, status) VALUES (?, ?, 'Active')", (self.space_id, self.start_time.strftime('%Y-%m-%d %H:%M:%S')))
        self.session_id = cursor.lastrowid
        conn.commit()
        conn.close()

        self.set_active_ui()
        self.update_timer()

    def stop_session(self):
        if self.timer_id:
            self.after_cancel(self.timer_id)
            self.timer_id = None
        CheckoutWindow(self, self)

    def resume_timer(self):
        self.update_timer()

    def finalize_stop(self):
        self.is_active = False
        self.session_id = None
        self.set_inactive_ui()

    def set_active_ui(self):
        self.configure(border_color="#e74c3c")
        self.status_label.configure(text="🔴 დაკავებული", text_color="#e74c3c")
        self.action_btn.configure(text="⏹ Stop", fg_color="#c0392b", hover_color="#e74c3c")
        self.bar_btn.pack(before=self.action_btn, pady=(0, 5), padx=20, fill="x")

    def set_inactive_ui(self):
        self.configure(border_color="#34495e")
        self.status_label.configure(text="🟢 თავისუფალი", text_color="white")
        self.action_btn.configure(text="▶ Start", fg_color="#27ae60", hover_color="#2ecc71")
        self.time_label.configure(text="00:00:00")
        self.cost_label.configure(text="0.00 ₾")
        self.bar_btn.pack_forget()

    def update_timer(self):
        if self.is_active:
            elapsed = datetime.now() - self.start_time
            total_seconds = int(elapsed.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.time_label.configure(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            self.cost_label.configure(text=f"{(elapsed.total_seconds() / 3600) * self.rate:.2f} ₾")
            self.timer_id = self.after(1000, self.update_timer)
            
    def open_cart(self):
        if self.session_id: CartWindow(self, self.name, self.session_id)


class DashboardApp(ctk.CTk):
    def __init__(self, username, role):
        super().__init__()
        self.title("NANTE - მთავარი პანელი")
        self.geometry("1200x800")
        
        self.username = username
        self.login_time = datetime.now()
        
        self.top_frame = ctk.CTkFrame(self, height=60)
        self.top_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(self.top_frame, text=f"👤 ოპერატორი: {username} | ცვლა დაიწყო: {self.login_time.strftime('%H:%M')}", 
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=20, pady=15)
        
        if role == 'Admin':
            ctk.CTkButton(self.top_frame, text="📊 სტატისტიკა", fg_color="#27ae60", command=self.open_reports).pack(side="right", padx=10, pady=15)
            ctk.CTkButton(self.top_frame, text="📦 მარაგები", fg_color="#34495e", command=lambda: InventoryWindow(self)).pack(side="right", padx=10, pady=15)
            
        ctk.CTkButton(self.top_frame, text="🚪 გასვლა", fg_color="#c0392b", hover_color="#e74c3c", width=100, 
                      command=self.logout).pack(side="right", padx=10, pady=15)

        self.spaces_frame = ctk.CTkScrollableFrame(self)
        self.spaces_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.load_spaces()

    def load_spaces(self):
        conn = sqlite3.connect('nante_club.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, rate_per_hour, is_active FROM Spaces")
        spaces = cursor.fetchall()
        
        col_count, row_count, col_index = 4, 0, 0

        for space_id, name, rate, is_active in spaces:
            session_start_time = None
            if is_active:
                cursor.execute("SELECT start_time FROM Sessions WHERE space_id=? AND status='Active'", (space_id,))
                active_session = cursor.fetchone()
                if active_session: session_start_time = active_session[0]

            card = SpaceCard(self.spaces_frame, space_id, name, rate, is_active, session_start_time, cashier_name=self.username)
            card.grid(row=row_count, column=col_index, padx=15, pady=15, sticky="nsew")
            self.spaces_frame.grid_columnconfigure(col_index, weight=1)
            
            col_index += 1
            if col_index >= col_count:
                col_index = 0
                row_count += 1
                
        conn.close()

    def open_reports(self): 
        ReportsWindow(self)
        
    def logout(self):
        ShiftCloseDialog(self, self)

    def print_z_report(self):
        conn = sqlite3.connect('nante_club.db')
        cursor = conn.cursor()
        
        date_filter = self.login_time.strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''SELECT SUM(cash_amount), SUM(card_amount) 
                          FROM Transactions 
                          WHERE cashier_name=? AND transaction_date >= ?''', 
                       (self.username, date_filter))
        res = cursor.fetchone()
        cash_total = res[0] or 0.0
        card_total = res[1] or 0.0
        conn.close()

        receipt = "\n"
        receipt += "       NANTE CLUB       \n"
        receipt += "      ცვლის დახურვა     \n"
        receipt += "------------------------\n"
        receipt += f"მოლარე: {self.username}\n"
        receipt += f"შესვლის დრო: {self.login_time.strftime('%H:%M')}\n"
        receipt += f"გასვლის დრო: {datetime.now().strftime('%H:%M')}\n"
        receipt += "------------------------\n"
        receipt += f"სულ ნაღდი (Cash): {cash_total:.2f} GEL\n"
        receipt += f"სულ ბარათი:       {card_total:.2f} GEL\n"
        receipt += f"ჯამური ბრუნვა:    {cash_total + card_total:.2f} GEL\n"
        receipt += "------------------------\n"
        receipt += "      Z-REPORT OK       \n\n\n\n"

        # აქ ვიყენებთ import-ს `core.printer`-დან
        send_to_printer(receipt, "Z-Report")

    def perform_logout(self):
        self.destroy()
        LoginApp().mainloop()


class LoginApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("NANTE - ავტორიზაცია")
        self.geometry("400x500")
        self.resizable(False, False)
        
        ctk.CTkLabel(self, text="NANTE Club", font=ctk.CTkFont(size=30, weight="bold")).pack(pady=(60, 10))
        ctk.CTkLabel(self, text="მართვის სისტემა", font=ctk.CTkFont(size=16)).pack(pady=(0, 40))

        self.username_entry = ctk.CTkEntry(self, placeholder_text="მომხმარებლის სახელი", width=250, height=40)
        self.username_entry.pack(pady=10)
        self.password_entry = ctk.CTkEntry(self, placeholder_text="პაროლი", width=250, height=40, show="*")
        self.password_entry.pack(pady=10)

        self.error_label = ctk.CTkLabel(self, text="", text_color="red")
        self.error_label.pack(pady=5)

        ctk.CTkButton(self, text="სისტემაში შესვლა", width=250, height=40, command=self.login_event).pack(pady=20)

    def login_event(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            self.error_label.configure(text="გთხოვთ, შეავსოთ ყველა ველი")
            return

        try:
            conn = sqlite3.connect('nante_club.db')
            cursor = conn.cursor()
            cursor.execute("SELECT role FROM Users WHERE username=? AND password=?", (username, password))
            user = cursor.fetchone()
            conn.close()

            if user:
                role = user[0]
                self.destroy()
                DashboardApp(username, role).mainloop()
            else:
                self.error_label.configure(text="არასწორი სახელი ან პაროლი")
        except Exception as e:
            self.error_label.configure(text=f"შეცდომა ბაზასთან: {e}")