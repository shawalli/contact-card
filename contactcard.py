# -*- coding: utf-8 -*-
from os import environ

from flask import Flask, redirect, render_template, request
from flask_sqlalchemy import SQLAlchemy


class Config:
    SQLALCHEMY_DATABASE_URI = environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False


app = Flask(__name__)
app.config.from_object(Config())


@app.before_request
def force_https():
    if request.url.startswith('http://'):
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)


db = SQLAlchemy()
db.init_app(app)


class ContactModel(db.Model):
    __tablename__ = 'contact'
    __table_args__ = {'schema': 'salesforce'}

    id = db.Column(primary_key=True)
    sfid = db.Column()

    firstname = db.Column()
    lastname = db.Column()
    title = db.Column()
    email = db.Column()
    phone = db.Column()


@app.route('/')
def index():
    contacts = ContactModel.query.all()
    return render_template('index.html', contacts=contacts)
