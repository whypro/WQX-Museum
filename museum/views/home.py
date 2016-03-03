# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import Blueprint, render_template, redirect, url_for, abort, request


bp_home = Blueprint('home', __name__)


@bp_home.route('/')
def index():
    return redirect(url_for('masterpiece.show_masterpieces'))


@bp_home.route('/about-me/')
def show_about_me():
    return render_template('about_me.html')


@bp_home.route('/recovery/')
def show_recovery():
    return render_template('recovery.html')
