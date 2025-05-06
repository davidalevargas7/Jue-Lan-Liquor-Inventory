from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
import datetime
from dotenv import load_dotenv

# Load .env values (for Supabase connection)
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://neondb_owner:npg_mO6IdNFki3Qo@ep-shrill-cake-a43ro4b9-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require"
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

# Home route with search & sort
@app.route('/')
def index():
    search_query = request.args.get('search', '').strip()
    sort_by = request.args.get('sort_by', 'name')
    order = request.args.get('order', 'asc')

    query = Liquor.query

    if search_query:
        query = query.filter(Liquor.liquor_name.ilike(f"%{search_query}%"))

    if sort_by == 'quantity':
        query = query.order_by(Liquor.quantity.asc() if order == 'asc' else Liquor.quantity.desc())
    elif sort_by == 'type':
        query = query.order_by(Liquor.liquor_type.asc() if order == 'asc' else Liquor.liquor_type.desc())
    else:  # Default sort by name
        query = query.order_by(Liquor.liquor_name.asc() if order == 'asc' else Liquor.liquor_name.desc())

    liquors = query.all()

    return render_template('index.html', liquors=liquors, search_query=search_query, sort_by=sort_by, order=order)

# Add liquor
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

# Edit liquor
@app.route('/edit/<int:liquor_id>', methods=['GET', 'POST'])
def edit_liquor(liquor_id):
    liquor = Liquor.query.get_or_404(liquor_id)
    if request.method == 'POST':
        liquor.liquor_name = request.form['liquor_name']
        liquor.liquor_type = request.form['liquor_type']
        liquor.bottle_size = request.form['bottle_size']
        liquor.quantity = int(request.form['quantity'])
        liquor.last_updated = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('edit.html', liquor=liquor)

# Delete liquor
@app.route('/delete/<int:liquor_id>', methods=['POST'])
def delete_liquor(liquor_id):
    liquor = Liquor.query.get_or_404(liquor_id)
    db.session.delete(liquor)
    db.session.commit()
    return redirect(url_for('index'))

# Run locally
if __name__ == '__main__':
    app.run(debug=True)