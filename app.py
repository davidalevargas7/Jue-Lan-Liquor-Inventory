from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
import datetime
from dotenv import load_dotenv

# Load .env values (for Supabase connection)
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define liquor model
class Liquor(db.Model):
    __tablename__ = 'liquor'
    id = db.Column(db.Integer, primary_key=True)
    liquor_name = db.Column(db.String(100), nullable=False)
    liquor_type = db.Column(db.String(50), nullable=False)
    bottle_size = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    last_updated = db.Column(db.String(100), nullable=False)

# TEMPORARY route to create tables
@app.route('/setup-db')
def setup_db():
    try:
        db.create_all()
        return "✅ Tables created in Supabase!"
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Home route
@app.route('/')
def index():
    liquors = Liquor.query.all()
    return render_template('index.html', liquors=liquors)

# Add liquor route
@app.route('/add', methods=['GET', 'POST'])
def add_liquor():
    if request.method == 'POST':
        liquor = Liquor(
            liquor_name=request.form['liquor_name'],
            liquor_type=request.form['liquor_type'],
            bottle_size=request.form['bottle_size'],
            quantity=int(request.form['quantity']),
            last_updated=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        db.session.add(liquor)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add.html')

# Run the app locally
if __name__ == '__main__':
    app.run(debug=True)