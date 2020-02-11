from MarkAdmin import *
from MarkFlask import *

app = None


def main(p=80):
    port = os.getenv('FLASK_PORT', str(p))
    addr = os.getenv('FLASK_ADDR', '0.0.0.0')

    global app
    app = CreateWallApp()

    with app.app_context():
        db = CreateWallDatabase(app)
        CreateWallAdmin(app, db)
        app.run(host=addr, port=int(port), debug=False, threaded=True)


main(5002)
