"""
wanderai/routes/pages.py
HTML page routes — serve Jinja2 templates.
Migrated from the original app.py page routes, now as a Blueprint.
"""
from flask import Blueprint, render_template, redirect, url_for

pages_bp = Blueprint("pages", __name__)


@pages_bp.get("/")
def index():
    return render_template("index.html")


@pages_bp.get("/chat")
def chat():
    return render_template("chat.html")


@pages_bp.get("/dashboard")
def dashboard():
    return render_template("dashboard.html", trip_data={})


@pages_bp.get("/itinerary")
def itinerary():
    return render_template("itinerary.html")


@pages_bp.get("/budget")
def budget():
    return render_template("budget.html")


@pages_bp.get("/profile")
def profile():
    return render_template("profile.html")


@pages_bp.get("/login")
def login():
    return render_template("auth/login.html")


@pages_bp.get("/register")
def register():
    return render_template("auth/register.html")


@pages_bp.get("/trips")
def trips():
    return render_template("trips/list.html")
