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


def _load_masterpieces(find_condition, sort):
    masterpieces = mongo.db.masterpieces.find(find_condition, sort=sort)

    masterpieces_list = []
    for masterpiece in masterpieces:
        masterpieces_list.append(_new_masterpiece(masterpiece))

    return masterpieces_list


def _new_masterpiece(masterpiece):
    if 'author_oid' in masterpiece:
        author = mongo.db.authors.find_one({'_id': masterpiece['author_oid']})
        if author:
            masterpiece['author'] = author
    masterpiece['image'] = masterpiece['screenshots'][0] if 'screenshots' in masterpiece and len(masterpiece['screenshots']) else '../../../default.bmp'
    return masterpiece


@home.route('/masterpiece/')
def show_masterpieces():
    # 标签过滤
    find_condition = dict()
    current_tags = []
    all_tags = mongo.db.masterpieces.distinct('tags')
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

    masterpieces = _load_masterpieces(find_condition, [('_id', -1)])
    # print masterpieces.count()

    return render_template('masterpieces.html', masterpieces=masterpieces, all_tags=all_tags, current_tags=current_tags)


@home.route('/masterpiece/search/<key>/')
def search_masterpieces(key):
    find_condition = {'title': {'$regex': key}}
    sort = [('title', 1), ('_id', -1)]
    masterpieces = _load_masterpieces(find_condition, sort)
    return render_template('masterpieces.html', masterpieces=masterpieces)


@home.route('/masterpiece/<oid>/update/')
def update_masterpieces_screenshots_and_files(oid):
    masterpiece = mongo.db.masterpieces.find_one({'_id': ObjectId(oid)})
    if not masterpiece:
        abort(404)

    dirname = os.path.abspath(os.path.join('museum\\static', 'masterpieces', masterpiece['type'], masterpiece['title']))
    screenshots = []
    files = []

    for filename in os.listdir(dirname):
        ext = os.path.splitext(filename)[-1].lower()
        if ext in ['.bmp', '.jpg', '.png', '.gif']:
            screenshots.append(filename)
        elif ext in ['.py', '.json', '.yml']:
            # 忽略
            continue
        else:
            files.append(filename)
    print dirname
    print screenshots
    print files
    mongo.db.masterpieces.update_one({'_id': ObjectId(oid)}, {'$set': {'screenshots': screenshots, 'files': files}})
    return redirect(url_for('home.show_masterpiece_detail', oid=oid))


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
    return render_template('masterpiece_detail.html', masterpiece=_new_masterpiece(masterpiece))


@home.route('/masterpiece/add/', methods=['GET', 'POST'])
def add_masterpiece():
    if request.method == 'POST':
        print request.form.get('type')
        if not request.form.get('title') or not request.form.get('type') or request.form.get('type') == 'None':
            return redirect(url_for('home.add_masterpiece'))
        data = dict(
            title=request.form.get('title'),
            subtitle=request.form.get('subtitle'),
            version=request.form.get('version'),
            date=request.form.get('date'),
            author_oid=ObjectId(request.form.get('author-oid')) if request.form.get('author-oid') != 'None' else None,
            studio_oid=ObjectId(request.form.get('studio-oid')) if request.form.get('studio-oid') != 'None' else None,
            marking=dict(score=request.form.get('score')),
            type=request.form.get('type'),
            static_cert=request.form.get('static-cert'),
            dynamic_cert=request.form.get('dynamic-cert'),
            tags=request.form.getlist('tags'),
        )
        print data

        result = mongo.db.masterpieces.insert_one(data)
        return redirect(url_for('home.show_masterpiece_detail', oid=result.inserted_id))

    authors = mongo.db.authors.find()
    studios = mongo.db.studios.find()
    tags = mongo.db.masterpieces.distinct('tags')
    types = mongo.db.masterpieces.distinct('type')
    return render_template('masterpiece_add.html', authors=authors, studios=studios, tags=tags, types=types)


@home.route('/masterpiece/<oid>/edit/', methods=['GET', 'POST'])
def edit_masterpiece(oid):
    if request.method == 'POST':
        data = dict(
            # title=request.form.get('title'),
            subtitle=request.form.get('subtitle'),
            version=request.form.get('version'),
            date=request.form.get('date'),
            author_oid=ObjectId(request.form.get('author-oid')) if request.form.get('author-oid') != 'None' else None,
            studio_oid=ObjectId(request.form.get('studio-oid')) if request.form.get('studio-oid') != 'None' else None,
            marking=request.form.get('marking'),
            type_=request.form.get('type'),
            static_cert=request.form.get('static-cert'),
            dynamic_cert=request.form.get('dynamic-cert'),
            tags=request.form.getlist('tags'),
        )
        print data

        mongo.db.masterpieces.update_one({'_id': ObjectId(oid)}, {'$set': data})
        return redirect(url_for('home.show_masterpiece_detail', oid=oid))

    masterpiece = mongo.db.masterpieces.find_one({'_id': ObjectId(oid)})
    if not masterpiece:
        abort(404)
    authors = mongo.db.authors.find()
    studios = mongo.db.studios.find()
    tags = mongo.db.masterpieces.distinct('tags')
    types = mongo.db.masterpieces.distinct('type')
    return render_template('masterpiece_edit.html', masterpiece=_new_masterpiece(masterpiece), authors=authors, studios=studios, tags=tags, types=types)


@home.route('/masterpiece/<oid>/delete/')
def delete_masterpiece(oid):
    mongo.db.masterpieces.delete_one({'_id': ObjectId(oid)})
    return redirect(url_for('home.index'))


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
