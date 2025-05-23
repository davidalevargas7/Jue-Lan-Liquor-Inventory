from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_
import os
import datetime
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "supersecret")

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ========================
# Models
# ========================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='viewer')  # 'viewer' or 'editor'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Liquor(db.Model):
    __tablename__ = 'liquor'
    id = db.Column(db.Integer, primary_key=True)
    liquor_name = db.Column(db.String(100), nullable=False)
    liquor_type = db.Column(db.String(50), nullable=False)
    bottle_size = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    last_updated = db.Column(db.String(100), nullable=False)
    edited_by = db.Column(db.String(150), nullable=True)

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150))
    action = db.Column(db.String(50))
    liquor_name = db.Column(db.String(100))
    timestamp = db.Column(db.String(100))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ========================
# Routes
# ========================

@app.route('/setup-db')
def setup_db():
    try:
        db.create_all()
        return "✅ Tables created!"
    except Exception as e:
        return f"❌ Error: {str(e)}"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    search_query = request.args.get('search', '').strip()
    sort_by = request.args.get('sort_by', 'name')
    order = request.args.get('order', 'asc')

    query = Liquor.query

    if search_query:
        query = query.filter(or_(
            Liquor.liquor_name.ilike(f"%{search_query}%"),
            Liquor.liquor_type.ilike(f"%{search_query}%"),
            Liquor.bottle_size.ilike(f"%{search_query}%"),
            Liquor.edited_by.ilike(f"%{search_query}%")
        ))

    if sort_by == 'quantity':
        query = query.order_by(Liquor.quantity.asc() if order == 'asc' else Liquor.quantity.desc())
    elif sort_by == 'type':
        query = query.order_by(Liquor.liquor_type.asc() if order == 'asc' else Liquor.liquor_type.desc())
    else:
        query = query.order_by(Liquor.liquor_name.asc() if order == 'asc' else Liquor.liquor_name.desc())

    liquors = query.all()
    return render_template('index.html', liquors=liquors, search_query=search_query, sort_by=sort_by, order=order)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_liquor():
    if current_user.role != 'editor':
        flash("Unauthorized access", "danger")
        return redirect(url_for('index'))

    if request.method == 'POST':
        liquor = Liquor(
            liquor_name=request.form['liquor_name'],
            liquor_type=request.form['liquor_type'],
            bottle_size=request.form['bottle_size'],
            quantity=int(request.form['quantity']),
            last_updated=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            edited_by=current_user.username
        )
        db.session.add(liquor)

        # Log this action
        log = ActivityLog(
            username=current_user.username,
            action='add',
            liquor_name=liquor.liquor_name,
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        db.session.add(log)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add.html')

@app.route('/edit/<int:liquor_id>', methods=['GET', 'POST'])
@login_required
def edit_liquor(liquor_id):
    if current_user.role != 'editor':
        flash("Unauthorized access", "danger")
        return redirect(url_for('index'))

    liquor = Liquor.query.get_or_404(liquor_id)
    if request.method == 'POST':
        liquor.liquor_name = request.form['liquor_name']
        liquor.liquor_type = request.form['liquor_type']
        liquor.bottle_size = request.form['bottle_size']
        liquor.quantity = int(request.form['quantity'])
        liquor.last_updated = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        liquor.edited_by = current_user.username

        # Log this action
        log = ActivityLog(
            username=current_user.username,
            action='edit',
            liquor_name=liquor.liquor_name,
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        db.session.add(log)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('edit.html', liquor=liquor)

@app.route('/delete/<int:liquor_id>', methods=['POST'])
@login_required
def delete_liquor(liquor_id):
    if current_user.role != 'editor':
        flash("Unauthorized access", "danger")
        return redirect(url_for('index'))

    liquor = Liquor.query.get_or_404(liquor_id)

    # Log before deleting
    log = ActivityLog(
        username=current_user.username,
        action='delete',
        liquor_name=liquor.liquor_name,
        timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    db.session.add(log)

    db.session.delete(liquor)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/logs')
@login_required
def view_logs():
    if current_user.role != 'editor':
        flash("Access denied: Only editors can view logs.", "danger")
        return redirect(url_for('index'))
    logs = ActivityLog.query.order_by(ActivityLog.id.desc()).all()
    return render_template('logs.html', logs=logs)

if __name__ == '__main__':
    app.run(debug=True)