#########################################################################
# Title  : Application main
# Author : Kevin Ryan Noronha
# Editor : Disha Khurana – 1 June 2025 – Integrated all three features:
#          Continuing Students, Pathway Overview, and GPA Prediction
##########################################################################

from flask import Flask, redirect, url_for
import os

# Importing Blueprints
from continuing_students import continuing_bp
from pathway_overview import pathway_bp
from Predicting_gpa import ml_bp 

def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')

    # File upload configuration
    upload_dir = os.path.join(app.root_path, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_dir
    app.config['SECRET_KEY'] = 'change_this_to_something_secret'

    # Register feature Blueprints
    app.register_blueprint(continuing_bp, url_prefix='/continuing')
    app.register_blueprint(pathway_bp,    url_prefix='/pathway')
    app.register_blueprint(ml_bp,         url_prefix='/ml')

    # Home redirects to continuing students
    @app.route('/')
    def index():
        return redirect(url_for('continuing.home'))

    return app


# Entry point for running the app
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
