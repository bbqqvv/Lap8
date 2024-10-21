import tkinter as tk
from tkinter import messagebox
import requests

# Địa chỉ server
SERVER_URL = 'http://localhost:5000'  # Thay đổi thành địa chỉ server tương ứng

# Chức năng đăng ký tài khoản
def register_account():
    account_name = entry_register_account_name.get()

    response = requests.post(f"{SERVER_URL}/register", json={'username': account_name})

    if response.status_code == 200:
        message = response.json()['message']
        messagebox.showinfo("Đăng ký thành công", message)
    else:
        message = response.json()['message']
        messagebox.showerror("Lỗi", message)

# Chức năng đăng nhập
def login():
    account_id = entry_login_id.get()
    account_name = entry_login_account_name.get()

    response = requests.post(f"{SERVER_URL}/login", json={'account_id': account_id, 'account_name': account_name})

    if response.status_code == 200:
        messagebox.showinfo("Thành công", response.json()['message'])
    else:
        messagebox.showerror("Lỗi", response.json()['message'])

# Chức năng đăng xuất
def logout():
    account_name = entry_login_account_name.get()
    response = requests.post(f"{SERVER_URL}/logout", json={'account_name': account_name})

    if response.status_code == 200:
        messagebox.showinfo("Thành công", response.json()['message'])
    else:
        messagebox.showerror("Lỗi", response.json()['message'])

# Chức năng rút tiền
def withdraw_money():
    account_name = entry_login_account_name.get()
    amount = float(entry_withdraw_amount.get())

    response = requests.post(f"{SERVER_URL}/withdraw", json={'account_name': account_name, 'amount': amount})

    if response.status_code == 200:
        messagebox.showinfo("Thành công", response.json()['message'])
    else:
        messagebox.showerror("Lỗi", response.json()['message'])

# Chức năng chuyển tiền
def transfer_money():
    from_account = entry_from_account.get()
    to_account = entry_to_account.get()
    amount = float(entry_transfer_amount.get())

    response = requests.post(f"{SERVER_URL}/transfer", json={'from_account': from_account, 'to_account': to_account, 'amount': amount})

    if response.status_code == 200:
        messagebox.showinfo("Thành công", response.json()['message'])
    else:
        messagebox.showerror("Lỗi", response.json()['message'])

# Chức năng nạp tiền
def deposit_money():
    account_name = entry_login_account_name.get()
    amount = float(entry_deposit_amount.get())

    response = requests.post(f"{SERVER_URL}/deposit", json={'account_name': account_name, 'amount': amount})

    if response.status_code == 200:
        messagebox.showinfo("Thành công", response.json()['message'])
    else:
        messagebox.showerror("Lỗi", response.json()['message'])

# Giao diện Tkinter
root = tk.Tk()
root.title("Banking Application")

# Đăng ký tài khoản

tk.Label(root, text="Đăng ký Tài khoản:", font=('Helvetica', 12)).grid(row=0, column=0, padx=10, pady=10)
entry_register_account_name = tk.Entry(root)
entry_register_account_name.grid(row=0, column=1, padx=10, pady=10)

btn_register = tk.Button(root, text="Đăng ký", command=register_account)
btn_register.grid(row=0, column=2, padx=10, pady=10)

# Đăng nhập
tk.Label(root, text="ID tài khoản:", font=('Helvetica', 12)).grid(row=1, column=0, padx=10, pady=10)
entry_login_id = tk.Entry(root)
entry_login_id.grid(row=1, column=1, padx=10, pady=10)

tk.Label(root, text="Tên tài khoản:", font=('Helvetica', 12)).grid(row=2, column=0, padx=10, pady=10)
entry_login_account_name = tk.Entry(root)
entry_login_account_name.grid(row=2, column=1, padx=10, pady=10)

btn_login = tk.Button(root, text="Đăng nhập", command=login)
btn_login.grid(row=2, column=2, padx=10, pady=10)

btn_logout = tk.Button(root, text="Đăng xuất", command=logout)
btn_logout.grid(row=3, column=2, padx=10, pady=10)

# Rút tiền
tk.Label(root, text="Rút tiền", font=('Helvetica', 16)).grid(row=4, column=0, columnspan=4, pady=10)

tk.Label(root, text="Số tiền:").grid(row=5, column=0, padx=10, pady=5)
entry_withdraw_amount = tk.Entry(root)
entry_withdraw_amount.grid(row=5, column=1, padx=10, pady=5)

btn_withdraw = tk.Button(root, text="Rút tiền", command=withdraw_money)
btn_withdraw.grid(row=5, column=2, padx=10, pady=5)

# Chuyển tiền
tk.Label(root, text="Chuyển tiền", font=('Helvetica', 16)).grid(row=6, column=0, columnspan=4, pady=10)

tk.Label(root, text="Từ tài khoản:").grid(row=7, column=0, padx=10, pady=5)
entry_from_account = tk.Entry(root)
entry_from_account.grid(row=7, column=1, padx=10, pady=5)

tk.Label(root, text="Đến tài khoản:").grid(row=8, column=0, padx=10, pady=5)
entry_to_account = tk.Entry(root)
entry_to_account.grid(row=8, column=1, padx=10, pady=5)

tk.Label(root, text="Số tiền:").grid(row=9, column=0, padx=10, pady=5)
entry_transfer_amount = tk.Entry(root)
entry_transfer_amount.grid(row=9, column=1, padx=10, pady=5)

btn_transfer = tk.Button(root, text="Chuyển tiền", command=transfer_money)
btn_transfer.grid(row=10, column=1, padx=10, pady=10)

# Nạp tiền
tk.Label(root, text="Nạp tiền", font=('Helvetica', 16)).grid(row=11, column=0, columnspan=4, pady=10)

tk.Label(root, text="Số tiền:").grid(row=12, column=0, padx=10, pady=5)
entry_deposit_amount = tk.Entry(root)
entry_deposit_amount.grid(row=12, column=1, padx=10, pady=5)

btn_deposit = tk.Button(root, text="Nạp tiền", command=deposit_money)
btn_deposit.grid(row=12, column=2, padx=10, pady=5)

root.mainloop()