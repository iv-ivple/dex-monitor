from flask import Flask, render_template
from api.routes import bp
from api.routes import bp, limiter

app = Flask(__name__)
limiter.init_app(app)
app.register_blueprint(bp)

@app.route("/")
def index():
    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run(debug=True, port=5001)
