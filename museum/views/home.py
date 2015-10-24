# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
from bson.objectid import ObjectId
import datetime

from flask import Blueprint, render_template, redirect, url_for, abort, request

from ..extensions import mongo
from ..helpers import get_client_ip, get_user_agent

home = Blueprint('home', __name__)


@home.route('/')
def index():
    return redirect(url_for('home.show_masterpieces'))


@home.route('/masterpiece/')
def show_masterpieces():
    find_condition = dict()
    all_tags = mongo.db.masterpieces.distinct('tags')
    # 标签过滤
    current_tags = []
    tags = request.args.get('tags')
    if tags:
        current_tags += tags.split(',')
        print current_tags
        # 验证合法性
        for tag in current_tags:
            print tag, all_tags
            if tag not in all_tags:
                abort(400)
        find_condition['tags'] = {'$all': current_tags}

    

    masterpieces = mongo.db.masterpieces.find(find_condition).sort([('_id', -1)])
    # print masterpieces.count()

    return render_template('masterpieces.html', masterpieces=masterpieces, all_tags=all_tags, current_tags=current_tags)


@home.route('/masterpiece/<oid>/')
def show_masterpiece_detail(oid):
    masterpiece = mongo.db.masterpieces.find_one({'_id': ObjectId(oid)})
    if not masterpiece:
        abort(404)
    # 统计
    ip = get_client_ip()
    user_agent = get_user_agent()
    mongo.db.clicks.update(
        {'masterpiece': ObjectId(oid), 'ip': ip, 'date': datetime.datetime.now().strftime('%Y-%m-%d')},
        {'$addToSet': {'user_agent': user_agent}, '$inc': {'count': 1}}, 
        upsert=True
    )
    return render_template('masterpiece_detail.html', masterpiece=masterpiece)


@home.route('/about-me/')
def show_about_me():
    return render_template('about_me.html')


@home.route('/recovery/')
def show_recovery():
    return render_template('recovery.html')


@home.route('/masterpiece/<oid>/download/<filename>')
def download(oid, filename):
    masterpiece = mongo.db.masterpieces.find_one({'_id': ObjectId(oid)})
    if not masterpiece:
        abort(404)
    return redirect(url_for('static', filename='masterpieces/'+masterpiece['type']+'/'+masterpiece['title']+'/'+filename))
