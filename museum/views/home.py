# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
from bson.objectid import ObjectId

from flask import Blueprint, render_template, redirect, url_for, abort

from ..extensions import mongo

home = Blueprint('home', __name__)


@home.route('/')
def index():
    return redirect(url_for('home.show_masterpieces'))


@home.route('/masterpiece/')
def show_masterpieces():
    masterpieces = mongo.db.masterpieces.find().sort([('_id', -1)])
    print masterpieces.count()
    return render_template('masterpieces.html', masterpieces=masterpieces)


@home.route('/masterpiece/<oid>/')
def show_masterpiece_detail(oid):
    masterpiece = mongo.db.masterpieces.find_one({'_id': ObjectId(oid)})
    if not masterpiece:
        abort(404)
    # 统计
    # mongo.db.update({'_id': ObjectId(oid)}, {'$push': {'statistic'}})
    return render_template('masterpiece_detail.html', masterpiece=masterpiece)


@home.route('/about-me/')
def show_about_me():
    return render_template('about_me.html')


@home.route('/recovery/')
def show_recovery():
    return render_template('recovery.html')