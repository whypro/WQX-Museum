# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app, send_from_directory

from ..extensions import mongo

home = Blueprint('home', __name__)


@home.route('/')
def index():
    masterpieces = mongo.db.masterpieces.find().sort([('_id', -1)])
    print masterpieces.count()
    return render_template('index.html', masterpieces=masterpieces)


@home.route('/masterpiece/<filename>')
def send_masterpiece(filename):
    return send_from_directory(current_app.config['MASTERPIECES_DIR'], filename)
