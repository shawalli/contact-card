# -*- coding: utf-8 -*-
from os import environ, urandom

from flask import flash, Flask, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Email


class Config:
    SECRET_KEY = urandom(64)

    SQLALCHEMY_DATABASE_URI = environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False


app = Flask(__name__)
app.config.from_object(Config())


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


@app.before_request
def force_https():
    if request.url.startswith('http://'):
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)


@app.route('/')
def index():
    contacts = ContactModel.query.all()
    return render_template('index.html', contacts=contacts)


class ContactForm(FlaskForm):
    firstname = StringField(
        label="First name",
        validators=[DataRequired()]
    )
    lastname = StringField(
        label="Last name",
        validators=[DataRequired()]
    )
    title = StringField(label="Title")
    email = StringField(
        label="Email Address",
        validators=[DataRequired(), Email()]
    )
    phone = StringField(
        label="Phone Number",
        validators=[DataRequired()]
    )


@app.route('/contact/<string:sfid>', methods=['GET', 'POST'])
def contact(sfid):
    contact = ContactModel.query.filter_by(sfid=sfid).first()

    form = ContactForm()
    if form.is_submitted():
        v = form.validate()
        if v:  # form.validate():
            form.populate_obj(contact)

            db.session.add(contact)
            db.session.commit()

            flash('Contact successfully updated.', category='success')
        else:
            for errors in form.errors.values():
                for error in errors:
                    flash(error, category='danger')
    else:
        form.process(formdata=None, obj=contact)

    return render_template('contact.html', sfid=sfid, form=form)
