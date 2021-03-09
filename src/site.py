from flask import Blueprint, flash, redirect, render_template, request, url_for, session, current_app
from .models import *

from google.oauth2 import id_token
from google.auth.transport import requests

site = Blueprint("site", __name__)

@site.route('/', methods=["GET", "POST"])
def index():
    return render_template('Index/index.html')

@site.route('/about', methods=["GET", "POST"])
def about():
    return render_template('About/about.html')

@site.before_app_request
def force_https():
    if request.endpoint in current_app.view_functions and request.headers.get('X-Forwarded-Proto', None) == 'http':
        return redirect(request.url.replace('http://', 'https://'))

@site.route('/google-signin', methods=["GET", "POST"])
def google_signin():
    if session.get("logged_in"):
        return redirect(url_for('site.index'))
    
    return render_template('Google-Sign-In/google.html')

@site.route("/google-auth", methods=["GET", "POST"])
def google_auth():
    if request.method == "GET":
        return redirect(url_for("site.login"))
    token = request.form.get("idtoken")
    print(token)
    try:
        idinfo = id_token.verify_oauth2_token(token, requests.Request(
        ), "337745045052-c19u56smhk30nck0dat09vigoe7fcolf.apps.googleusercontent.com")
        print("Email", idinfo["email"])
        result = d_gauth(idinfo["email"])
        if result:
            flash(f"You have successfully logged back in as {idinfo['email']}!", category='success')
        else:
            flash(f"Your account has successfully been created and you are now logged in as {idinfo['email']}!", category='success')
        session["logged_in"] = True
        session["g_auth"] = True
        session["email"] = idinfo["email"]
        return "Success!"
    except ValueError:
        flash("Your login was invalid! Make sure you have provided permissions to access your email address", category='error')
        return "Error!"


@site.route('/login', methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("site.index"))
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        result = d_login(email, password)
        if result:
            session["logged_in"] = True
            session["username"] = result["Username"]
            session["email"] = result["Email"]
            flash(f"You are now logged in as {session['username']}!", category='success')
            return redirect(url_for("site.index"))
        else:
            flash("Invalid Username or Password!", category='error')
            return redirect(url_for("site.login"))
    return render_template('Login/login.html')


@site.route('/register', methods=["GET", "POST"])
def register():
    if session.get("logged_in"):
        return redirect(url_for("site.index"))
    if request.method == "POST":
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")
        if len(email) < 4:
            flash('Your email must be greater than 3 characters!', category='error')
        elif len(username) <= 5:
            flash('Your username must be greater than 5 characters!',
                  category='error')
        elif len(password) < 8:
            flash('Your password should be 8 characters or more!', category='error')
        else:
            if d_signup(username, email, password=password):
                session["logged_in"] = True
                session["username"] = username
                session["email"] = email
                flash(
                    f"Successfully Registered as {username}!", category='success')
                flash(
                    f"You are now logged in as  {username}!", category='success')
                return redirect(url_for("site.index"))
            else:
                flash(
                    "Someone is already registered with this username or password!", category='error')
    return render_template('Register/register.html')


@site.route('/logout')
def logout():
    if not session.get("logged_in"):
        flash("You are already logged out!", category='error')
        return redirect(url_for('site.login'))
    else:
        session.clear()
        flash("You have been successfully logged out!", category='success')
        return redirect(url_for("site.login"))

@site.route('/change-password', methods=["GET", "POST"])
def change_password():
    if request.method == "POST":
        old_pass = request.form.get('current-password')
        new_pass = request.form.get('new-password') 
        result = d_change_pwd(session.get("username"), old_pass, new_pass)
        if result:
            flash("Password has been changed!", category='success')
            return redirect(url_for('site.index'))
        flash("Password change has failed", category='error')
        return redirect(url_for('site.index'))
    return render_template('Change/change.html')

@site.route('/delete-account', methods=["GET", "POST"])
def delete_account():
    if request.method == "POST":
        password = request.form.get('password')
        confirm_password = request.form.get('confirm-password')

        if d_delete(session.get("username"), session.get("email"), password):
            session.clear()
            flash("Account deleted!", category="success")
            return redirect(url_for('site.register'))
        else:
            flash("Account deletion unsuccessful!", category="error")
            return redirect(url_for("site.delete_account"))
    return render_template('Delete/delete.html')

themes = {
    "Cool Breeze": "",
    "Sunrise": "",
    "Dark Mountains": ""
}

types = {
    "Simple Text": "",
    "Cards": ""
}

boilerplate = [
    "",
    "",
    ""
]

@site.route('/projects', methods=["GET", "POST"])
def projects():
    if not session.get('logged_in'):
        flash('You must be logged in to view your projects!', category='error')
        return redirect(url_for('site.login'))
    return render_template('Profile/profile.html', sites=d_get_sites(session.get("username"), session.get("email")))


@site.route('/create', methods=["GET", "POST"])
def create():
    if not session.get('logged_in'):
        flash("You must login to create a website!", category='error')
        return redirect(url_for("site.login"))
    else:
        styles = [{'style': 'Cool Breeze'}, {
            'style': 'Sun Rise'}, {'style': 'Dark Mountains'}]
        types = [{'type': 'Test One'}, {
            'type': 'Test Two'}, {'type': 'Test Three'}]

        if request.method == "POST":
            web_name = request.form.get("web-name")
            web_style = request.form.get("web-style")
            web_type = request.form.get("web-type")
            flash(f"You chose {web_name} {web_style} {web_type}!", category='success')
            return redirect(url_for("site.projects"))
        else:
            return render_template('Create/create.html', styles=styles, types=types)


@site.route('/edit/<sitename>', methods=["GET", "POST"])
def edit(sitename=None):
    if not session.get('logged_in'):
        flash("You must be logged in to edit your projects!", category='error')
        return redirect(url_for('site.login')) 
    if not sitename:
        flash("An Internal Error Occured! This has been reported and will be resolved soon. Thanks for the patience!", category="error")
    if request.method == "POST":
        new_code = request.form.get("code")
        d_edit(session.get("username"), session.get("email"), sitename, new_code)
        return ""
    site = d_get_site(session.get("username"), session.get("email"), sitename)
    return render_template('Edit/edit.html', name=site[0], code=site[1]["HTML"])