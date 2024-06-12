from flask import Flask, request, render_template_string
from wallet_app.Wallet import Wallet  # Убедитесь, что путь импорта корректен

app = Flask(__name__)
wallet = Wallet()  # Инициализируйте ваш кошелек здесь

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        address = request.form['address']
        try:
            info = wallet.info(address)  # Метод info должен возвращать объект с атрибутом balance
            balance = info.balance / 10000000  # Предполагаем, что баланс нужно сконвертировать
            return render_template_string('''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Wallet Balance</title>
                </head>
                <body>
                    <h1>Balance for address {{ address }}: {{ balance }}</h1>
                    <a href="/">Check another address</a>
                </body>
                </html>
            ''', address=address, balance=balance)
        except Exception as e:
            return f"An error occurred: {str(e)}"
    return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Wallet Balance</title>
        </head>
        <body>
            <h1>Enter Wallet Address</h1>
            <form method="post">
                <input type="text" name="address" placeholder="Enter wallet address" required>
                <input type="submit" value="Get Balance">
            </form>
        </body>
        </html>
    '''

if __name__ == '__main__':
    app.run(debug=True)
