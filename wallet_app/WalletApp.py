import tkinter as tk
from wallet_app.Wallet import Wallet
from tkinter import simpledialog, messagebox
from tkinter import ttk
import pyperclip


class WalletApp(tk.Tk):
    def __init__(self, wallet):
        super().__init__()
        self.wallet = wallet
        self.title("Кошелек")
        self.geometry("650x300")

        self.create_widgets()
        # Запрашиваем пароль сразу после инициализации
        self.request_password_and_load_wallet()

    def request_password_and_load_wallet(self):
        password = simpledialog.askstring("Пароль", "Введите пароль кошелька:", show='*')
        if password is not None:
            try:
                self.wallet.load_from_file(password)
                self.populate_first_address()
                self.update_balance_info()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
                self.quit()
        else:
            messagebox.showinfo("Внимание", "Требуется ввод пароля для доступа к кошельку!")
            self.quit()

    def populate_first_address(self):
        addresses = self.wallet.keys_address()
        if addresses:
            self.combo_address['values'] = addresses
            self.combo_address.current(0)
            self.combo_address.bind('<<ComboboxSelected>>', self.update_info_on_selection)
            self.update_balance_info()

    def update_info_on_selection(self, event=None):
        self.get_info()
        self.update_balance_info()

    def update_balance_info(self):
        self.get_info()
        self.after(5000, self.update_balance_info)  # Запланировать следующий вызов через 5 секунд

    def create_widgets(self):
        self.lbl_address = tk.Label(self, text="Адрес кошелька:")
        self.lbl_address.grid(row=0, column=0, sticky="e", padx=10, pady=10)

        # Увеличиваем ширину Combobox до 60 символов
        self.combo_address = ttk.Combobox(self, width=60)
        self.combo_address.grid(row=0, column=1, sticky="we", padx=(10, 10))

        self.btn_copy = tk.Button(self, text="Копировать", command=self.copy_address)
        self.btn_copy.grid(row=0, column=2, padx=(5, 10), pady=10)  # Маленькая кнопка для копирования адреса


        self.lbl_balance = tk.Label(self, text="")
        self.lbl_balance.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

        self.lbl_send_to = tk.Label(self, text="Отправить на адрес:")
        self.lbl_send_to.grid(row=3, column=0, sticky="e", padx=10)

        # Увеличиваем ширину поля для ввода адреса отправки до 60 символов
        self.entry_send_to = tk.Entry(self, width=60)
        self.entry_send_to.grid(row=3, column=1, sticky="we", padx=(10, 10))

        self.lbl_amount = tk.Label(self, text="Сумма:")
        self.lbl_amount.grid(row=4, column=0, sticky="e", padx=10)

        # Увеличиваем ширину поля для ввода суммы до 60 символов
        self.entry_amount = tk.Entry(self, width=60)
        self.entry_amount.grid(row=4, column=1, sticky="we", padx=(10, 10))

        self.lbl_message = tk.Label(self, text="Сообщение:")
        self.lbl_message.grid(row=5, column=0, sticky="e", padx=10)

        # Увеличиваем ширину поля для ввода сообщения до 60 символов
        self.entry_message = tk.Entry(self, width=60)
        self.entry_message.grid(row=5, column=1, sticky="we", padx=(10, 10))

        self.btn_send = tk.Button(self, text="Отправить", command=self.send_transaction)
        self.btn_send.grid(row=6, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

    def copy_address(self):
        address = self.combo_address.get()
        pyperclip.copy(address)  # Копируем адрес в буфер обмена
        messagebox.showinfo("Копирование", "Адрес скопирован в буфер обмена.")

    def get_info(self):
        address = self.combo_address.get()
        if address:
            try:
                info = self.wallet.info(address)
                self.lbl_balance.config(text=f"Баланс: {info.balance / 10000000}, Нонс: {info.nonce}")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
        else:
            self.lbl_balance.config(text="Выберите адрес кошелька.")

    def send_transaction(self):
        from_address = self.combo_address.get()
        to_address = self.entry_send_to.get()
        amount = int(self.entry_amount.get())*10000000
        message = self.entry_message.get()
        # Предполагаем, что XMSS объект уже существует
        xmss = self.wallet.keys[from_address] if from_address in self.wallet.keys else None
        if not xmss:
            messagebox.showerror("Ошибка", "Некорректный адрес отправителя")
            return
        try:
            self.wallet.make_transaction(xmss=xmss, address_to=to_address, ammount=amount, message=message, fee=0)
            messagebox.showinfo("Успех", "Транзакция отправлена")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))


# Создаем объект кошелька
wallet_tk = Wallet()
print(wallet_tk.keys_address())

# Запускаем приложение
app = WalletApp(wallet_tk)
app.mainloop()
