from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import INT4RANGE
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("flask_blog_secretkey")
# Sqlite DB
# app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///cafes.db"
# PostgreSQL DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("cafe_database")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

Bootstrap5(app)

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Users, user_id)


def admin_only(func):
    @wraps(func)
    def any_func(*args, **kwargs):
        if current_user.id == 1:
            return func(*args, **kwargs)
        else:
            return abort(403)
    return any_func


class Cafes(db.Model):
    __tablename__ = "cafe"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250))
    map_url = db.Column(db.String)
    img_url = db.Column(db.String)
    location = db.Column(db.String(250))
    has_sockets = db.Column(db.Integer)
    has_toilet = db.Column(db.Integer)
    has_wifi = db.Column(db.Integer)
    can_take_calls = db.Column(db.Integer)
    seats = db.Column(INT4RANGE)
    coffee_price = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('Users', back_populates='cafes')


class Users(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250))
    email = db.Column(db.String(250), unique=True)
    password = db.Column(db.String(250))
    cafes = db.relationship('Cafes', back_populates='user')


@app.route("/")
def home():
    page = request.args.get("page", 1, type=int)
    cafes = Cafes.query.paginate(per_page=9, page=page)
    return render_template("index.html", cafes=cafes)


@app.route("/users/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        email = request.form.get("Email")
        user = db.session.query(Users).filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, request.form.get("Password")):
                login_user(user)
                return redirect(url_for("home"))
            else:
                flash("Wrong credentials - Try again.")
                return redirect(url_for("login"))
        else:
            flash("User not registered.")
            return redirect(url_for("login"))
    return render_template("login.html")


@app.route("/users/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        email = request.form.get("Email")
        password_hash = generate_password_hash(request.form.get("Password"))
        new_user = Users(
            name=request.form.get("Username"),
            email=email,
            password=password_hash
        )
        if db.session.query(Users).filter_by(email=email).first():
            flash("User already registered.")
            return redirect(url_for("register"))
        else:
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for("home"))
    return render_template("register.html")


@app.route("/users/logout", methods=["POST", "GET"])
@login_required
def logout():
    logout_user()
    flash("You've logged out.")
    return redirect(url_for("login"))


@app.route("/make-post", methods=["POST", "GET"])
@login_required
def make_post():
    if request.method == "POST":
        name = request.form.get("cafename")
        new_cafe = Cafes(
            name=name,
            map_url=request.form.get("mapurl"),
            img_url=request.form.get("imgurl"),
            location=request.form.get("location"),
            has_sockets=request.form.get("sockets"),
            has_toilet=request.form.get("toilets"),
            has_wifi=request.form.get("wifi"),
            can_take_calls=request.form.get("calls"),
            seats=request.form.get("seats"),
            coffee_price=request.form.get("price"),
            user_id=current_user.id
        )
        if db.session.query(Cafes).filter_by(name=name).first():
            flash("Cafe already registered.")
            return redirect(url_for("make_post"))
        else:
            db.session.add(new_cafe)
            db.session.commit()
            return redirect(url_for("home"))
    return render_template("make_post.html")


@app.route("/delete-post/<int:post_id>")
@login_required
@admin_only
def delete_post(post_id):
    post_to_delete = Cafes.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = Cafes.query.get(post_id)
    if post.user_id != current_user.id and current_user.id != 1:
        return abort(403, "Access denied. You can only edit your own posts.")
    if request.method == "POST":
        post.name = request.form.get("cafename")
        post.map_url = request.form.get("mapurl")
        post.img_url = request.form.get("imgurl")
        post.location = request.form.get("location"),
        post.has_sockets = request.form.get("sockets"),
        post.has_toilet = request.form.get("toilets"),
        post.has_wifi = request.form.get("wifi"),
        post.can_take_calls = request.form.get("calls"),
        post.seats = request.form.get("seats"),
        post.coffee_price = request.form.get("price")
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit_post.html", post=post)


if __name__ == "__main__":
    app.run()
