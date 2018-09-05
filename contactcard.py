# -*- coding: utf-8 -*-
"""One-file Flask app that displays Salesforce Contact sObject records.

Additionally, the records may be edited and have the record changes
automatically synced back to Salesforce. This app requires a PostGreSQL
database that is connected to Salesforce via Heroku Connect.
"""
from base64 import b64encode
from functools import wraps
from os import environ, urandom
from re import search
from typing import Callable, Optional, Union

from flask import flash, Flask, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from sqlalchemy.sql import text
from wtforms import StringField
from wtforms.validators import DataRequired, Email


class Config:
    """This class stores configuration variables for the Flask application.

    Attributes
    ----------
    SECRET_KEY : str
        Secret used to generate security-based data, such as CSRF tokens
        (default: random 64-character string)
    SQLALCHEMY_DATABASE_URI : str
        URI of the database this app uses. This variable is provided by the
        Heroku PostGreSQL add-on.
    SQLALCHEMY_TRACK_MODIFICATIONS : bool
        This variable is used by SQLAlchemy. SQLAlchemy recommends setting it
        to False if it is not explicitly needed, as the feature has a side
        effect of slowing down transactions.
    HEROKU_CONNECT_INITED : bool
        Whether or not Heroku Connect has been initialized. The app will update
        this value as necessary.
    """

    SECRET_KEY: str = environ.get(
        'SECRET_KEY',
        b64encode(urandom(48)).decode('utf-8')
    )
    SQLALCHEMY_DATABASE_URI: str = environ['DATABASE_URL']
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    HEROKU_CONNECT_INITED = False


# Flask application, configured
app = Flask(__name__)
app.config.from_object(Config())


# Database, configured
db = SQLAlchemy()
db.init_app(app)


class ContactModel(db.Model):  # type: ignore
    """Model used to interface with Heroku Connect Contact table. Column types
    are left blank so as to blindly assume the characteristics placed on them
    by the Heroku Connect mapping.

    Attributes
    ----------
    __tablename__ : str
        Table name, as set by Heroku Connect
    __table_args__ : dict
        Table arguments. The only argument the app must pass is the schema
        namespace, which directs SQLAlchemy to the Heroku Connect schema when
        connecting the model to the database table.
    id : int
        PostGreSQL record id
    sfid : str
        Salesforce 18-character record ID
    firstname : str
        First name
    lastname : str
        Last name
    title : str, optional
        Company title
    email : str
        Valid email address (enforced by app and Salesforce)
    phone : str
        Valid phone number (enforced by Salesforce)
    """

    __tablename__ = 'contact'
    __table_args__ = {'schema': 'salesforce'}

    id = db.Column(primary_key=True)
    sfid = db.Column()

    firstname = db.Column()
    lastname = db.Column()
    title = db.Column()
    email = db.Column()
    phone = db.Column()


class ContactForm(FlaskForm):
    """Form used to render and edit contact information.

    Attributes
    ----------
    firstname : :obj:`StringField`
        First-name form-field
    lastname : :obj:`StringField`
        Last-name form-field
    title : :obj:`StringField`, optional
        Company-title form-field
    email : :obj:`StringField`
        Email form-field
    phone : :obj:`StringField`
        Phone form-field
    """

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


def salesforce_connection_exists() -> bool:
    """Tests whether Heroku Connect has been configured.
    """

    if not app.config['HEROKU_CONNECT_INITED']:
        with db.engine.connect() as conn:
            # Search for the 'salesforce' schema
            statement = text(
                "SELECT COUNT(*) "
                "FROM information_schema.schemata "
                "WHERE schema_name = 'salesforce';"
            )

            # Unpack the proxy and extract single result (count)
            results_proxy = conn.execute(statement)
            results = [result for result in results_proxy]
            result = results.pop()
            schema_exists = bool(result['count'])

            if schema_exists:
                app.config['HEROKU_CONNECT_INITED'] = True

    return app.config['HEROKU_CONNECT_INITED']


def heroku_connect_required(func: Callable) -> Callable:
    """View decorator that checks whether Heroku Connect has been configured
    and redirects the user to the welcome page if the connection has not been
    set up.
    """

    @wraps(func)
    def decorated_view(*args, **kwargs) -> Callable:
        """Returns original view method if Heroku Connect is setup.

        If not set up, redirects to the welcome page.
        """

        if salesforce_connection_exists():
            return func(*args, **kwargs)
        else:
            return redirect(url_for('welcome'))

    return decorated_view


@app.before_request
def force_https() -> redirect:
    """Redirects all HTTP requests to HTTPS."""

    if request.url.startswith('http://'):
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)


@app.route('/welcome')
def welcome() -> Union[redirect, render_template]:
    """Renders the welcome page to the app.

    Only available if Heroku Connect has not yet been set up.
    """

    if salesforce_connection_exists():
        return redirect(url_for('index'))

    app_name_match = search(
        '^https?://([\w-]*).herokuapp.com.*',
        request.url_root
    )

    app_name = app_name_match.group(1)

    heroku_resource_url = (
        f"https://dashboard.heroku.com/apps/{app_name}/resources"
    )

    return render_template(
        'welcome.html',
        heroku_resource_url=heroku_resource_url
    )


@app.route('/')
@heroku_connect_required
def index() -> render_template:
    """Renders page for URL root (index)."""

    # Get all Contact sObject records and pass to the renderer
    contacts = ContactModel.query.all()

    return render_template('index.html', contacts=contacts)


@app.route('/contact/<string:sfid>', methods=['GET', 'POST'])
@heroku_connect_required
def contact(sfid: str) -> Union[redirect, render_template]:
    """Renders or edits a contact based on the Salesforce record.

    sfid : str
        Salesforce 18-character record ID
    """

    # Get Contact sObject record with matching Salesforce ID
    contact: Optional[ContactModel] = ContactModel.query.filter_by(
        sfid=sfid
    ).first()

    if contact is None:
        flash(
            'No contact with matching Salesforce ID exists.',
            category='danger'
        )
        # Since the record does not exist, redirect to the index page.
        return redirect(url_for('index'))

    form = ContactForm()
    # First, check if this is a submission (POST).
    if form.is_submitted():
        # Next, validate form data.
        if form.validate():
            # Populate changes onto Contact sObject record and commit the
            # changes to the PostGreSQL database. Heroku Connect will sync
            # those changes back to Salesforce in the background.
            form.populate_obj(contact)

            db.session.add(contact)
            db.session.commit()

            flash('Contact successfully updated.', category='success')
        else:
            # Form validation failed; flash error messages
            for errors in form.errors.values():
                for error in errors:
                    flash(error, category='danger')
    else:
        # Else, not a submission (GET); Populate the form with the contents
        # of the Contact sObject record.
        form.process(formdata=None, obj=contact)

    # Render the contact page.
    return render_template('contact.html', sfid=sfid, form=form)
