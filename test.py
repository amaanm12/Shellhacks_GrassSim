from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return '<h1>Test successful! Flask is working.</h1>'

if __name__ == '__main__':
    app.run(debug=True)