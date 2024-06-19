import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog
from wallet_app.Wallet import Wallet
import pyperclip
from core.protocol import Protocol

from net.ConnectManager import ConnectManager
import os
import json

class WalletApp(tk.Tk):
    def __init__(self, server='5.35.98.126:9333'):
        super().__init__()

        self.connect_manager = ConnectManager()
        self.connect_manager.start_ping_thread()


        self.server = server
        self.wallet = Wallet(servers=self.server, connect_manager = self.connect_manager)
        self.title("Кошелек")
        self.geometry("800x450")  # Увеличил размер для лучшего отображения вкладок
        self.password = None
        self.create_widgets()
        self.current_page = 0
        self.transactions_per_page = 10


        # self.request_password_and_load_wallet()

    def request_password_and_load_wallet(self, filename=None):
        if filename is None:
            filename = filedialog.askopenfilename(
                title="Выберите файл кошелька",
                filetypes=(("Wallet files", "*.dat"), ("All files", "*.*")),
                initialdir=os.getcwd()  # Использование текущей рабочей директории
            )
            if not filename:  # Пользователь отменил выбор файла
                self.update_status("Загрузка кошелька отменена.")
                return

        self.password = simpledialog.askstring("Пароль", "Введите пароль кошелька:", show='*')
        if self.password:
            try:
                self.wallet = Wallet(filename=filename, servers=self.server)  # Создаем экземпляр кошелька с указанием файла
                self.wallet.load_from_file(self.password)
                self.populate_first_address()
                self.update_balance_info()
                self.update_status("Кошелек успешно загружен.")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
                self.update_status(f"Ошибка: {str(e)}")  # Вывод сообщения об ошибке в строке состояния
                # self.quit()
        else:
            self.update_status("Требуется ввод пароля для доступа к кошельку!")
            # self.quit()

    def populate_first_address(self):
        addresses = self.wallet.keys_address()
        if addresses:
            self.combo_address['values'] = addresses
            self.combo_address.current(0)
            self.update_balance_info()

    def update_balance_info(self, event=None):
        address = self.combo_address.get()
        if address:
            try:
                info = self.wallet.info(address, transactions_start=self.current_page * self.transactions_per_page,
                                        transactions_end=(self.current_page + 1) * self.transactions_per_page)
                self.lbl_balance.config(
                    text=f"Баланс: {info.balance / 10000000} coins, Нонс: {info.nonce} ,Всего подписей: {Protocol.address_max_sign(address)}")

                for item in self.tree_transactions.get_children():
                    self.tree_transactions.delete(item)  # Очистить таблицу перед обновлением

                for tx in info.transactions:
                    tx_data = json.loads(tx.json_data)
                    tx_type = "IN" if address in tx_data['toAddress'] else "OUT"
                    tx_hash_short = f"{tx_data['txhash'][:3]}...{tx_data['txhash'][-3:]}"
                    amount = tx_data['amounts'][0] / 10000000

                    if tx_type == "IN":
                        # from_address = f"{tx_data['fromAddress'][:3]}...{tx_data['fromAddress'][-3:]}"
                        from_address = tx_data['fromAddress']
                        self.tree_transactions.insert("", tk.END, values=(tx_type, tx_hash_short, from_address, "", amount))
                    else:
                        # to_address = f"{tx_data['toAddress'][0][:3]}...{tx_data['toAddress'][0][-3:]}"
                        to_address = tx_data['toAddress']
                        self.tree_transactions.insert("", tk.END, values=(tx_type, tx_hash_short, "", to_address, amount))

                self.update_status(f"Страница {self.current_page + 1}")
            except Exception as e:
                return  # Возвращаемся, если произошла ошибка, чтобы избежать бесконечного цикла
        self.after(5000, self.update_balance_info)

    def next_page(self):
        self.current_page += 1
        self.update_balance_info()

    def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_balance_info()

    def create_widgets(self):
        input_width = 70
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both')

        self.menu_bar = tk.Menu(self)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Открыть кошелек", command=self.open_wallet)
        self.file_menu.add_command(label="Сохранить кошелек", command=self.save_wallet)
        self.menu_bar.add_cascade(label="Файл", menu=self.file_menu)
        self.config(menu=self.menu_bar)

        # Создание вкладок
        self.tab_main = ttk.Frame(self.notebook)
        self.tab_transaction = ttk.Frame(self.notebook)
        self.tab_key_info = ttk.Frame(self.notebook)
        self.tab_new_address = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_main, text='Основная')
        self.notebook.add(self.tab_transaction, text='Создание транзакции')
        self.notebook.add(self.tab_key_info, text='Данные о ключе')
        self.notebook.add(self.tab_new_address, text='Добавление нового адреса')

        # Основная вкладка
        self.lbl_address = tk.Label(self.tab_main, text="Адрес кошелька:")
        self.lbl_address.grid(row=0, column=0, sticky="e", padx=10, pady=10)
        self.combo_address = ttk.Combobox(self.tab_main, width=input_width)
        self.combo_address.grid(row=0, column=1, sticky="we", padx=(10, 10))
        self.combo_address.bind('<<ComboboxSelected>>', self.update_balance_info)  # Привязка события выбора к обновлению баланса
        self.btn_copy = tk.Button(self.tab_main, text="Копировать", command=self.copy_address)
        self.btn_copy.grid(row=0, column=2, padx=(5, 10), pady=10)
        self.lbl_balance = tk.Label(self.tab_main, text="")
        self.lbl_balance.grid(row=1, column=0, columnspan=3, sticky="ew", padx=10, pady=10)

        # Добавление таблицы транзакций
        self.tree_transactions = ttk.Treeview(self.tab_main, columns=("Type", "Hash", "From", "To", "Amount"), show='headings')
        self.tree_transactions.heading("Type", text="Тип")
        self.tree_transactions.heading("Hash", text="Хеш")
        self.tree_transactions.heading("From", text="От")
        self.tree_transactions.heading("To", text="Кому")
        self.tree_transactions.heading("Amount", text="Сумма")
        self.tree_transactions.column("Type", width=40, minwidth=40, stretch=tk.NO)
        self.tree_transactions.column("Hash", width=30, minwidth=30, stretch=tk.YES)
        self.tree_transactions.column("From", width=100, minwidth=100, stretch=tk.YES)
        self.tree_transactions.column("To", width=100, minwidth=100, stretch=tk.YES)
        self.tree_transactions.column("Amount", width=50, minwidth=50, stretch=tk.NO)
        self.tree_transactions.grid(row=2, column=0, columnspan=3, sticky="ew", padx=10, pady=10)

        self.btn_prev_page = tk.Button(self.tab_main, text="Предыдущая страница", command=self.previous_page)
        self.btn_prev_page.grid(row=3, column=0, padx=(10, 5), pady=10)

        self.btn_next_page = tk.Button(self.tab_main, text="Следующая страница", command=self.next_page)
        self.btn_next_page.grid(row=3, column=2, padx=(5, 10), pady=10)

        # Вкладка создания транзакции
        self.lbl_send_to = tk.Label(self.tab_transaction, text="Отправить на адрес:")
        self.lbl_send_to.grid(row=0, column=0, sticky="e", padx=10)
        self.entry_send_to = tk.Entry(self.tab_transaction, width=input_width)
        self.entry_send_to.grid(row=0, column=1, sticky="we", padx=(10, 10))
        self.lbl_amount = tk.Label(self.tab_transaction, text="Сумма:")
        self.lbl_amount.grid(row=1, column=0, sticky="e", padx=10)
        self.entry_amount = tk.Entry(self.tab_transaction, width=input_width)
        self.entry_amount.grid(row=1, column=1, sticky="we", padx=(10, 10))
        self.lbl_message = tk.Label(self.tab_transaction, text="Сообщение:")
        self.lbl_message.grid(row=2, column=0, sticky="e", padx=10)
        self.entry_message = tk.Entry(self.tab_transaction, width=60)
        self.entry_message.grid(row=2, column=1, sticky="we", padx=(10, 10))
        self.btn_send = tk.Button(self.tab_transaction, text="Отправить", command=self.send_transaction)
        self.btn_send.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=10)



        # Вкладка данных о ключе
        self.lbl_private_key = tk.Label(self.tab_key_info, text="Секретный ключ:")
        self.lbl_private_key.grid(row=0, column=0, sticky="e", padx=10, pady=10)
        self.txt_private_key = tk.Text(self.tab_key_info, height=1, width=input_width)
        self.txt_private_key.grid(row=0, column=1, sticky="we", padx=(10, 10))
        self.lbl_seed_phrase = tk.Label(self.tab_key_info, text="Сид-фраза:")
        self.lbl_seed_phrase.grid(row=1, column=0, sticky="e", padx=10)
        self.txt_seed_phrase = tk.Text(self.tab_key_info, height=1, width=input_width)
        self.txt_seed_phrase.grid(row=1, column=1, sticky="we", padx=(10, 10))
        self.btn_show_info = tk.Button(self.tab_key_info, text="Показать информацию", command=self.show_key_info)
        self.btn_show_info.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

        # Вкладка добавления нового адреса
        self.lbl_key_type = tk.Label(self.tab_new_address, text="Тип ключа:")
        self.lbl_key_type.grid(row=0, column=0, sticky="e", padx=10)
        self.combo_key_type = ttk.Combobox(self.tab_new_address,
                                           values=["По ключу", "По сид-фразе", "Случайное значение"], state="readonly")
        self.combo_key_type.grid(row=0, column=1, sticky="we", padx=(10, 10))
        self.lbl_key_or_seed = tk.Label(self.tab_new_address, text="Ключ или Сид-фраза:")
        self.lbl_key_or_seed.grid(row=1, column=0, sticky="e", padx=10)
        self.entry_key_or_seed = tk.Entry(self.tab_new_address, width=input_width)
        self.entry_key_or_seed.grid(row=1, column=1, sticky="we", padx=(10, 10))
        self.btn_add_address = tk.Button(self.tab_new_address, text="Добавить адрес", command=self.add_address)
        self.btn_add_address.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        self.btn_save = tk.Button(self.tab_new_address, text="Сохранить",
                                  command=self.save_wallet)
        self.btn_save.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

        self.lbl_height = tk.Label(self.tab_new_address, text="Высота адреса:")
        self.lbl_height.grid(row=3, column=0, sticky="e", padx=10)
        self.entry_height = tk.Entry(self.tab_new_address, width=input_width)
        self.entry_height.grid(row=3, column=1, sticky="w", padx=(10, 0))
        self.entry_height.insert(0, "6")  # Значение по умолчанию для высоты

        self.btn_add_address.grid(row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        self.btn_save.grid(row=5, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

        # Добавление строки состояния
        self.status_bar = tk.Label(self, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def update_status(self, message):
        """ Обновляет текст в строке состояния """
        self.status_bar.config(text=message)
        self.status_bar.update_idletasks()

    def open_wallet(self):
        # Запрашиваем имя файла для загрузки кошелька
        filename = filedialog.askopenfilename(title="Выберите файл кошелька",
                                              filetypes=(("Wallet files", "*.dat"), ("All files", "*.*")))
        if filename:
            self.request_password_and_load_wallet(filename)

    def save_wallet(self):
        if not self.password:
            # Запрос пароля, если он не был установлен
            self.password = simpledialog.askstring("Пароль", "Введите пароль кошелька для сохранения:", show='*')
            if not self.password:
                self.update_status("Сохранение кошелька отменено: пароль не введен.")
                return

        filename = filedialog.asksaveasfilename(
            title="Сохранить кошелек как",
            filetypes=(("Wallet files", "*.dat"), ("All files", "*.*")),
            defaultextension=".dat",
            initialdir=os.getcwd()
        )
        if filename:
            try:
                self.wallet.save_to_file(self.password, filename)
                self.update_status("Кошелек успешно сохранен.")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
                self.update_status(f"Ошибка при сохранении кошелька: {str(e)}")
        else:
            self.update_status("Сохранение отменено.")

    def copy_address(self):
        address = self.combo_address.get()
        pyperclip.copy(address)
        # messagebox.showinfo("Копирование", "Адрес скопирован в буфер обмена.")


    def send_transaction(self):
        from_address = self.combo_address.get()
        to_address = self.entry_send_to.get()
        amount = int(self.entry_amount.get()) * 10000000  # Предполагается, что сумма вводится в монетах
        message = self.entry_message.get()
        try:
            xmss = self.wallet.keys[from_address] if from_address in self.wallet.keys else None
            if not xmss:
                raise Exception("Некорректный адрес отправителя")
            self.wallet.make_transaction(xmss=xmss, address_to=to_address, amount=amount, message=message, fee=0)
            messagebox.showinfo("Успех", "Транзакция отправлена")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def show_key_info(self):
        address = self.combo_address.get()
        if address:
            try:
                xmss = self.wallet.keys[address]
                self.txt_private_key.delete('1.0', tk.END)
                self.txt_private_key.insert(tk.END, xmss.private_key.hex())
                self.txt_seed_phrase.delete('1.0', tk.END)
                self.txt_seed_phrase.insert(tk.END, xmss.seed_phrase)
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    def add_address(self):
        key_type = self.combo_key_type.get()
        key_or_seed = self.entry_key_or_seed.get()
        height = int(self.entry_height.get())  # Читаем высоту из поля ввода
        try:
            if key_type == "По ключу":
                self.wallet.add_key(key=key_or_seed, height=height)
            elif key_type == "По сид-фразе":
                self.wallet.add_key(seed_phrase=key_or_seed, height=height)
            elif key_type == "Случайное значение":
                self.wallet.add_key(height=height)  # Добавление ключа с заданной высотой
            self.populate_first_address()
            messagebox.showinfo("Успех", "Новый адрес добавлен")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

# Инициализация и запуск приложения
wallet = Wallet()  # Замените этим ваш объект кошелька
# app = WalletApp(server='192.168.0.26:9334')
app = WalletApp()
app.mainloop()
