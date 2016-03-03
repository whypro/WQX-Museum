# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from flask import Flask

from . import views
from .extensions import mongo


def create_app(config=None):
    app = Flask(__name__)

    # config
    app.config.from_object(config)

    # database
    mongo.init_app(app)

    # blueprint
    app.register_blueprint(views.bp_home)
    app.register_blueprint(views.bp_masterpiece)
    app.register_blueprint(views.bp_author)
    app.register_blueprint(views.bp_device)

    return app
