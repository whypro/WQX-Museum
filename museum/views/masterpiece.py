# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import datetime

from flask import Blueprint, render_template, redirect, url_for, abort, request
from flask import current_app, send_file
import pymongo
from bson.objectid import ObjectId

from ..extensions import mongo
from ..helpers import get_client_ip, get_user_agent


bp_masterpiece = Blueprint('masterpiece', __name__, url_prefix='/masterpiece')


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
        else:
            mongo.db.masterpieces.update_one({'_id': masterpiece['_id']}, {'$unset': {'author_oid', True}})
    if 'author' not in masterpiece:
        masterpiece['author'] = dict()
    return masterpiece


@bp_masterpiece.route('/')
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


@bp_masterpiece.route('/search/<key>/')
def search_masterpieces(key):
    find_condition = {'title': {'$regex': key}}
    sort = [('title', 1), ('_id', -1)]
    masterpieces = _load_masterpieces(find_condition, sort)
    return render_template('masterpieces.html', masterpieces=masterpieces)


@bp_masterpiece.route('/<oid>/update/')
def update_masterpieces_screenshots_and_files(oid):
    masterpiece = mongo.db.masterpieces.find_one({'_id': ObjectId(oid)})
    if not masterpiece:
        abort(404)

    screenshots = []
    files = []

    for filename in os.listdir(_get_masterpiece_dirname(masterpiece)):
        ext = os.path.splitext(filename)[-1].lower()
        if ext in ['.bmp', '.jpg', '.png', '.gif']:
            screenshots.append(filename)
        elif ext in ['.py', '.json', '.yml']:
            # 忽略
            continue
        else:
            files.append(filename)

    print screenshots
    print files

    mongo.db.masterpieces.update_one({'_id': ObjectId(oid)}, {'$set': {'screenshots': screenshots, 'files': files}})
    return redirect(url_for('masterpiece.show_masterpiece_detail', oid=oid))


@bp_masterpiece.route('/<oid>/')
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


@bp_masterpiece.route('/add/', methods=['GET', 'POST'])
def add_masterpiece():
    if request.method == 'POST':
        title = request.form.get('title')
        type_ = request.form.get('type')
        if not title or not type_ or type_ == 'None':
            return redirect(url_for('masterpiece.add_masterpiece'))
        data = dict(title=title, type=type_)
        subtitle = request.form.get('subtitle')
        if subtitle:
            data['subtitle'] = subtitle
        version = request.form.get('version')
        if version:
            data['version'] = version
        date = request.form.get('date')
        if date:
            data['date'] = date
        author_oid = request.form.get('author-oid')
        if author_oid and author_oid != 'None':
            data['author_oid'] = ObjectId(author_oid)
        studio_oid = request.form.get('studio-oid')
        if studio_oid and studio_oid != 'None':
            data['studio_oid'] = ObjectId(studio_oid)
        score = request.form.get('score')
        if score and score != 'None':
            if not score.isdigit():
                abort(400)
            data.setdefault('marking', dict())
            data['marking']['score'] = score
        static_cert = request.form.get('static-cert')
        if static_cert:
            data['static_cert'] = static_cert
        dynamic_cert = request.form.get('dynamic-cert')
        if dynamic_cert:
            data['dynamic_cert'] = dynamic_cert
        compatibility = request.form.getlist('compatibility')
        compatibility = filter(lambda x: x, compatibility)
        if compatibility:
            data['compatibility'] = compatibility
        tags = request.form.getlist('tags')
        if tags:
            data['tags'] = tags
        ref = request.form.get('ref')
        if ref:
            data['ref'] = ref
        print data

        result = mongo.db.masterpieces.insert_one(data)
        print result.inserted_id
        masterpiece = mongo.db.masterpieces.find_one({'_id': ObjectId(result.inserted_id)})
        os.makedirs(_get_masterpiece_dirname(masterpiece))

        return redirect(url_for('masterpiece.show_masterpiece_detail', oid=result.inserted_id))

    copy_oid = request.args.get('copy')
    if copy_oid:
        copy_masterpiece = mongo.db.masterpieces.find_one({'_id': ObjectId(copy_oid)})
        if not copy_masterpiece:
            abort(400)
    else:
        copy_masterpiece = dict()
    authors = mongo.db.authors.find().sort([('name', pymongo.ASCENDING)])
    studios = mongo.db.studios.find()
    tags = mongo.db.masterpieces.distinct('tags')
    types = mongo.db.masterpieces.distinct('type')
    return render_template('masterpiece_add.html', masterpiece=_new_masterpiece(copy_masterpiece), authors=authors, studios=studios, tags=tags, types=types)


@bp_masterpiece.route('/<oid>/edit/', methods=['GET', 'POST'])
def edit_masterpiece(oid):
    if request.method == 'POST':
        data = dict()
        subtitle = request.form.get('subtitle')
        if subtitle:
            data['subtitle'] = subtitle
        version = request.form.get('version')
        if version:
            data['version'] = version
        date = request.form.get('date')
        if date:
            data['date'] = date
        author_oid = request.form.get('author-oid')
        if author_oid and author_oid != 'None':
            data['author_oid'] = ObjectId(author_oid)
        studio_oid = request.form.get('studio-oid')
        if studio_oid and studio_oid != 'None':
            data['studio_oid'] = ObjectId(studio_oid)
        score = request.form.get('score')
        if score and score != 'None':
            if not score.isdigit():
                abort(400)
            data.setdefault('marking', dict())
            data['marking']['score'] = score
        static_cert = request.form.get('static-cert')
        if static_cert:
            data['static_cert'] = static_cert
        dynamic_cert = request.form.get('dynamic-cert')
        if dynamic_cert:
            data['dynamic_cert'] = dynamic_cert
        compatibility = request.form.getlist('compatibility')
        compatibility = filter(lambda x: x, compatibility)
        if compatibility:
            data['compatibility'] = compatibility
        tags = request.form.getlist('tags')
        if tags:
            data['tags'] = tags
        ref = request.form.get('ref')
        if ref:
            data['ref'] = ref
        print data

        mongo.db.masterpieces.update_one({'_id': ObjectId(oid)}, {'$set': data})
        return redirect(url_for('masterpiece.show_masterpiece_detail', oid=oid))

    masterpiece = mongo.db.masterpieces.find_one({'_id': ObjectId(oid)})
    if not masterpiece:
        abort(404)
    authors = mongo.db.authors.find().sort([('name', pymongo.ASCENDING)])
    studios = mongo.db.studios.find()
    tags = mongo.db.masterpieces.distinct('tags')
    types = mongo.db.masterpieces.distinct('type')
    return render_template('masterpiece_edit.html', masterpiece=_new_masterpiece(masterpiece), authors=authors, studios=studios, tags=tags, types=types)


def _get_masterpiece_dirname(masterpiece):
    return os.path.abspath(os.path.join(current_app.config['ASSETS_DIR'], 'masterpieces', masterpiece['type'], masterpiece['title']))


@bp_masterpiece.route('/<oid>/delete/')
def delete_masterpiece(oid):
    masterpiece = mongo.db.masterpieces.find_one_and_delete({'_id': ObjectId(oid)})
    os.removedirs(_get_masterpiece_dirname(masterpiece))
    return redirect(url_for('masterpiece.index'))


@bp_masterpiece.route('/<oid>/download/<filename>')
def get_masterpiece_file(oid, filename):
    masterpiece = mongo.db.masterpieces.find_one({'_id': ObjectId(oid)})
    if not masterpiece:
        abort(404)

    path = os.path.join(_get_masterpiece_dirname(masterpiece), filename)
    return send_file(path)
    # return send_from_directory(current_app.config['ASSETS_DIR'], filename=path, as_attachment=True)


@bp_masterpiece.route('/<oid>/screenshot/<int:idx>/')
def get_masterpiece_screenshot(oid, idx):
    masterpiece = mongo.db.masterpieces.find_one({'_id': ObjectId(oid)})
    if not masterpiece:
        abort(404)

    if 'screenshots' in masterpiece and idx <= len(masterpiece['screenshots']):
        filename = masterpiece['screenshots'][idx]
    else:
        abort(404)

    path = os.path.join(_get_masterpiece_dirname(masterpiece), filename)
    return send_file(path)
    # return send_from_directory(current_app.config['ASSETS_DIR'], filename=path)


@bp_masterpiece.route('/<oid>/preview/')
def get_masterpiece_preview(oid):
    masterpiece = mongo.db.masterpieces.find_one({'_id': ObjectId(oid)})
    if not masterpiece:
        abort(404)

    if 'screenshots' in masterpiece and masterpiece['screenshots']:
        filename = masterpiece['screenshots'][0]
        path = os.path.join(_get_masterpiece_dirname(masterpiece), filename)
        return send_file(path)
    else:
        path = os.path.join(current_app.static_folder, 'default.bmp')
        return send_file(path)
