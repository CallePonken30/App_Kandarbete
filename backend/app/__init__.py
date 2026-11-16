from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)

    CORS(app)

    from app.routes import transform_bp
    from app.review import review_bp

    app.register_blueprint(transform_bp, url_prefix="/transform")
    app.register_blueprint(review_bp, url_prefix="/file-analysis")

    return app

