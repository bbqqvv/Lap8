# server/server.py
# import os
# import sys
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
import sqlite3
import requests

from database import *

app = Flask(__name__)

# Kết nối và khởi tạo CSDL
conn = connect_db('database_A.db')  # Thay đổi tên CSDL tương ứng cho mỗi server
initialize_db(conn, 'schema.sql')

# Danh sách các server khác để đồng bộ
OTHER_SERVERS = ['http://localhost:5001', 'http://localhost:5002']  # Thêm URL của các server khác


@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')

    if not username:
        return jsonify({"status": "error", "message": "Tên tài khoản không được để trống."}), 400

    try:
        # Gọi hàm create_account để thêm tài khoản vào cơ sở dữ liệu
        account_id = create_account(conn, username)

        return jsonify({"status": "success", "message": f"Tài khoản {username} đã được tạo thành công. ID của bạn là {account_id}"}), 200

    except Exception as e:
        # Xử lý lỗi nếu có vấn đề khi thêm tài khoản
        return jsonify({"status": "error", "message": "Có lỗi xảy ra khi tạo tài khoản."}), 500

# API đăng nhập
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    account_name = data['account_name']

    account = get_account(conn, account_name)
    if not account:
        return jsonify({"status": "error", "message": "Tài khoản không tồn tại."}), 404

    account_id, _, balance, is_logged_in = account
    if is_logged_in:
        return jsonify({"status": "error", "message": "Tài khoản đã được đăng nhập từ máy khác."}), 403

    # Cập nhật trạng thái đăng nhập
    update_account_login_status(conn, account_id, True)

    # Đồng bộ trạng thái đăng nhập lên các server khác
    sync_login_status(account_id, True)

    return jsonify({"status": "success", "message": "Đăng nhập thành công!"}), 200


# API đăng xuất
@app.route('/logout', methods=['POST'])
def logout():
    data = request.json
    account_name = data['account_name']

    account = get_account(conn, account_name)
    if not account:
        return jsonify({"status": "error", "message": "Tài khoản không tồn tại."}), 404

    account_id, _, balance, is_logged_in = account
    if not is_logged_in:
        return jsonify({"status": "error", "message": "Tài khoản chưa được đăng nhập."}), 400

    # Cập nhật trạng thái đăng xuất
    update_account_login_status(conn, account_id, False)

    # Đồng bộ trạng thái đăng xuất lên các server khác
    sync_login_status(account_id, False)

    return jsonify({"status": "success", "message": "Đăng xuất thành công!"}), 200


# API rút tiền
@app.route('/withdraw', methods=['POST'])
def withdraw():
    data = request.json
    account_name = data['account_name']
    amount = data['amount']

    account = get_account(conn, account_name)
    if not account:
        return jsonify({"status": "error", "message": "Tài khoản không tồn tại."}), 404

    account_id, _, balance, is_logged_in = account
    if balance < amount:
        return jsonify({"status": "error", "message": "Số dư không đủ."}), 400

    new_balance = balance - amount
    update_balance(conn, account_id, new_balance)
    add_transaction(conn, account_id, 'withdraw', amount)

    # Đồng bộ giao dịch rút tiền lên các server khác
    sync_transaction(account_id, new_balance, 'withdraw', amount)

    return jsonify({"status": "success", "message": f"Rút {amount} thành công!", "new_balance": new_balance}), 200


# API chuyển tiền
@app.route('/transfer', methods=['POST'])
def transfer():
    data = request.json
    from_account_name = data['from_account']
    to_account_name = data['to_account']
    amount = data['amount']

    from_account = get_account(conn, from_account_name)
    to_account = get_account(conn, to_account_name)

    if not from_account:
        return jsonify({"status": "error", "message": "Tài khoản gửi không tồn tại."}), 404
    if not to_account:
        return jsonify({"status": "error", "message": "Tài khoản nhận không tồn tại."}), 404

    from_account_id, _, from_balance, is_logged_in = from_account
    to_account_id, _, to_balance, is_logged_in_to = to_account

    if from_balance < amount:
        return jsonify({"status": "error", "message": "Số dư tài khoản gửi không đủ."}), 400

    # Cập nhật số dư
    new_from_balance = from_balance - amount
    new_to_balance = to_balance + amount
    update_balance(conn, from_account_id, new_from_balance)
    update_balance(conn, to_account_id, new_to_balance)

    # Ghi vào bảng giao dịch
    add_transaction(conn, from_account_id, 'transfer_out', amount)
    add_transaction(conn, to_account_id, 'transfer_in', amount)

    # Đồng bộ giao dịch chuyển tiền lên các server khác
    sync_transfer(from_account_id, to_account_id, amount)

    return jsonify(
        {"status": "success", "message": f"Chuyển {amount} từ {from_account_name} sang {to_account_name} thành công!",
         "from_new_balance": new_from_balance, "to_new_balance": new_to_balance}), 200


# API cập nhật số dư từ các server khác
@app.route('/update_balance', methods=['POST'])
def update_balance_api():
    data = request.json
    account_id = data['account_id']
    new_balance = data['new_balance']

    cursor = conn.cursor()
    cursor.execute("UPDATE accounts SET balance = ? WHERE account_id = ?", (new_balance, account_id))
    conn.commit()

    return jsonify({"status": "success"}), 200


# API cập nhật giao dịch từ các server khác
@app.route('/update_transaction', methods=['POST'])
def update_transaction():
    data = request.json
    account_id = data['account_id']
    transaction_type = data['transaction_type']
    amount = data['amount']

    cursor = conn.cursor()
    cursor.execute("INSERT INTO transactions (account_id, transaction_type, amount) VALUES (?, ?, ?)",
                   (account_id, transaction_type, amount))

    # Cập nhật số dư nếu cần
    if transaction_type == 'withdraw':
        cursor.execute("UPDATE accounts SET balance = balance - ? WHERE account_id = ?", (amount, account_id))
    elif transaction_type == 'deposit':
        cursor.execute("UPDATE accounts SET balance = balance + ? WHERE account_id = ?", (amount, account_id))
    elif transaction_type == 'transfer_in':
        cursor.execute("UPDATE accounts SET balance = balance + ? WHERE account_id = ?", (amount, account_id))
    elif transaction_type == 'transfer_out':
        cursor.execute("UPDATE accounts SET balance = balance - ? WHERE account_id = ?", (amount, account_id))

    conn.commit()

    return jsonify({"status": "success"}), 200


# API cập nhật trạng thái đăng nhập
@app.route('/update_login_status', methods=['POST'])
def update_login_status_api():
    data = request.json
    account_id = data['account_id']
    status = data['is_logged_in']

    update_account_login_status(conn, account_id, status)

    return jsonify({"status": "success"}), 200


# Hàm đồng bộ trạng thái đăng nhập
def sync_login_status(account_id, status):
    data = {
        'account_id': account_id,
        'is_logged_in': status
    }
    for server in OTHER_SERVERS:
        try:
            requests.post(f"{server}/update_login_status", json=data)
        except Exception as e:
            print(f"Lỗi đồng bộ trạng thái đăng nhập tới {server}: {e}")


# Hàm đồng bộ giao dịch rút tiền
def sync_transaction(account_id, new_balance, transaction_type, amount):
    data = {
        'account_id': account_id,
        'new_balance': new_balance,
        'transaction_type': transaction_type,
        'amount': amount
    }
    for server in OTHER_SERVERS:
        try:
            requests.post(f"{server}/update_transaction", json=data)
            requests.post(f"{server}/update_balance", json={'account_id': account_id, 'new_balance': new_balance})
        except Exception as e:
            print(f"Lỗi đồng bộ giao dịch tới {server}: {e}")


# Hàm đồng bộ giao dịch chuyển tiền
def sync_transfer(from_account_id, to_account_id, amount):
    data_out = {
        'account_id': from_account_id,
        'transaction_type': 'transfer_out',
        'amount': amount
    }
    data_in = {
        'account_id': to_account_id,
        'transaction_type': 'transfer_in',
        'amount': amount
    }

    for server in OTHER_SERVERS:
        try:
            requests.post(f"{server}/update_transaction", json=data_out)
            requests.post(f"{server}/update_transaction", json=data_in)
            # Cập nhật số dư cho cả hai tài khoản
            cursor = conn.cursor()
            cursor.execute("SELECT balance FROM accounts WHERE account_id = ?", (from_account_id,))
            from_balance = cursor.fetchone()[0]
            cursor.execute("SELECT balance FROM accounts WHERE account_id = ?", (to_account_id,))
            to_balance = cursor.fetchone()[0]
            requests.post(f"{server}/update_balance", json={'account_id': from_account_id, 'new_balance': from_balance})
            requests.post(f"{server}/update_balance", json={'account_id': to_account_id, 'new_balance': to_balance})
        except Exception as e:
            print(f"Lỗi đồng bộ chuyển tiền tới {server}: {e}")


# Hàm đồng bộ giao dịch nạp tiền
def sync_deposit(account_id, new_balance, amount):
    data = {
        'account_id': account_id,
        'transaction_type': 'deposit',  # Xác định loại giao dịch là 'nạp tiền'
        'amount': amount,
        'new_balance': new_balance
    }

    for server in OTHER_SERVERS:
        try:
            # Gửi yêu cầu đồng bộ giao dịch nạp tiền
            requests.post(f"{server}/update_transaction", json=data)

            # Gửi yêu cầu cập nhật số dư sau khi nạp tiền
            requests.post(f"{server}/update_balance", json={'account_id': account_id, 'new_balance': new_balance})
        except Exception as e:
            print(f"Lỗi đồng bộ nạp tiền tới {server}: {e}")


# API nạp tiền
@app.route('/deposit', methods=['POST'])
def deposit():
    data = request.json
    account_name = data['account_name']
    amount = data['amount']

    # Kiểm tra tài khoản tồn tại
    account = get_account(conn, account_name)
    if not account:
        return jsonify({"status": "error", "message": "Tài khoản không tồn tại."}), 404

    account_id, _, balance, _ = account
    new_balance = balance + amount

    # Cập nhật số dư và thêm giao dịch nạp tiền
    update_balance(conn, account_id, new_balance)
    add_transaction(conn, account_id, 'deposit', amount)

    # Đồng bộ giao dịch nạp tiền lên các server khác
    sync_transaction(account_id, new_balance, 'deposit', amount)

    return jsonify({"status": "success", "message": f"Nạp {amount} thành công!", "new_balance": new_balance}), 200



if __name__ == '__main__':
    app.run(port=5000)  # Server A chạy trên port 5000
