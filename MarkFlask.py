from flask import Flask, request, redirect, render_template, flash, url_for
from flask.templating import DispatchingJinjaLoader
from flask_babelex import Babel
from flask_caching import Cache
from flask_compress import Compress
from flask_cors import CORS
from flask_dropzone import Dropzone
from flask_login import login_required, logout_user, current_user, LoginManager, login_user
from flask_restful import Api, Resource
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class
from flask_wtf import FlaskForm
from sqlalchemy import func, or_
from wtforms import StringField, PasswordField, SubmitField

from MarkDatabase import *


class LoginForm(FlaskForm):
    username = StringField('Username')
    password = PasswordField('Password')
    submit = SubmitField('Submit')


class WallFileLoader(DispatchingJinjaLoader):
    def __init__(self, app):
        super(WallFileLoader, self).__init__(app)

    def get_source(self, environment, template):
        contents, filename, uptodate = super(WallFileLoader, self).get_source(environment, template)
        if template == 'base.html':
            contents = contents.replace(u'MyApp', u'Разметка Изображений')
            contents = contents.replace(u'2014', u'2020')
            contents = contents.replace(u'MyCorp', u'')
        return contents, filename, uptodate


class WallApp(Flask):
    def __init__(self, **kwargs):
        super(WallApp, self).__init__('Wall', **kwargs)

    def create_global_jinja_loader(self):
        return WallFileLoader(self)


class ConfigClass(object):
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'T#IS IS @N 666 sECRET')
    dbpath = os.getenv('DB_PATH', "db/")
    dbpath += 'db.sqlite'

    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///'+dbpath)

    CSRF_ENABLED = True
    USER_APP_NAME = "Wall"
    USER_ENABLE_FORGOT_PASSWORD = False
    USER_ENABLE_REGISTER = False
    USER_ENABLE_EMAIL = False
    USER_ALLOW_LOGIN_WITHOUT_CONFIRMED_EMAIL = True
    USER_EMAIL_SENDER_NAME = 'Yolo'
    USER_EMAIL_SENDER_EMAIL = 'info@example.com'

    DROPZONE_UPLOAD_MULTIPLE = True
    DROPZONE_ALLOWED_FILE_CUSTOM = True
    DROPZONE_ALLOWED_FILE_TYPE = 'image/*'
    DROPZONE_REDIRECT_VIEW = 'results'

    imgpath = os.getenv('IMG_PATH', os.getcwd() + '/uploads')
    UPLOADED_PHOTOS_DEST = imgpath

    TEMPLATES_AUTO_RELOAD = True
    DROPZONE_MAX_FILE_SIZE = 20
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT: 6000

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    COMPRESS_MIMETYPES = ['svg', 'xml', 'font', 'script', 'stylesheet', 'png', 'svg+xml', 'document',
                          'xhr', 'html', 'js', 'css']

    USER_LOGIN_TEMPLATE = 'login.html'
    USER_REGISTER_TEMPLATE = 'login.html'


def CreateWallApp():
    app = WallApp(static_folder='assets', static_url_path='/assets')
    app.config.from_object(__name__ + '.ConfigClass')

    try:
        app.config.from_object('local_settings')
    except:
        pass

    # Use for Frontend debug
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    Compress(app)
    Cache(app)
    babel = Babel(app)
    login = LoginManager(app)

    @login.unauthorized_handler
    def handle_needs_login():
        flash("You have to be logged in to access this page.")
        return redirect(url_for('login', next=request.endpoint))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            user = User.query.filter(or_(User.username == username, User.email == username)).first()
            if user is None or not user.check_password(password):
                flash("Sorry, but you could not log in.")
                redirect(url_for('home_page'))
            else:
                next = request.form['next']
                login_user(user, remember=True)
                return redirect(next)
        else:
            next = request.args.get('next')
            return render_template("login.html", next=next)

    login.login_view = 'login'

    @babel.localeselector
    def get_locale():
        return 'ru'

    app.dropzone = Dropzone(app)
    app.photos = UploadSet('photos', IMAGES)
    configure_uploads(app, app.photos)
    patch_request_class(app)

    @app.route('/')
    def home_page():
        users = db.session.query(func.count(User.id)).scalar()
        images = db.session.query(func.count(Image.id)).scalar()
        is_logedin = current_user.is_authenticated
        return render_template("index.html", files=str(images),
                               users=str(users), is_logedin=is_logedin)

    @app.route('/images_page')
    @login_required
    def images_page():
        return render_template('images_page.html')

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('home_page'))

    api = Api(app)

    class Images(Resource):
        def get(self, page):
            pglen = 10
            record_query = Image.query \
                .filter(Image.updated_at <= datetime.now()) \
                .paginate(int(page), pglen, False)

            files = record_query.items
            contents = []
            total = {'files': len(files), 'pglen': pglen}
            for file in files:
                filepath = app.photos.url(file.image)
                info = {}
                info['name'] = file.image
                info['width'] = file.width
                info['height'] = file.height
                info['url'] = filepath
                info['type'] = 'file'

                contents.append(info)
            return {'contents': contents, 'total': total}


    api.add_resource(Images, '/api/v1/FilesREST/<page>')

    return app
