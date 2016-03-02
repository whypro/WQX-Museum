# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
from bson.objectid import ObjectId
import datetime

from flask import Blueprint, render_template, redirect, url_for, abort, request
import pymongo

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
        else:
            mongo.db.masterpieces.update_one({'_id': masterpiece['_id']}, {'$unset': {'author_oid', True}})
    if 'author' not in masterpiece:
        masterpiece['author'] = dict()
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
        title = request.form.get('title')
        type_ = request.form.get('type')
        if not title or not type_ or type_ == 'None':
            return redirect(url_for('home.add_masterpiece'))
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
        if compatibility:
            data['compatibility'] = filter(lambda x: x, compatibility)
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

        return redirect(url_for('home.show_masterpiece_detail', oid=result.inserted_id))

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


@home.route('/masterpiece/<oid>/edit/', methods=['GET', 'POST'])
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
        if compatibility:
            data['compatibility'] = filter(lambda x: x, compatibility)
        tags = request.form.getlist('tags')
        if tags:
            data['tags'] = tags
        ref = request.form.get('ref')
        if ref:
            data['ref'] = ref
        print data

        mongo.db.masterpieces.update_one({'_id': ObjectId(oid)}, {'$set': data})
        return redirect(url_for('home.show_masterpiece_detail', oid=oid))

    masterpiece = mongo.db.masterpieces.find_one({'_id': ObjectId(oid)})
    if not masterpiece:
        abort(404)
    authors = mongo.db.authors.find().sort([('name', pymongo.ASCENDING)])
    studios = mongo.db.studios.find()
    tags = mongo.db.masterpieces.distinct('tags')
    types = mongo.db.masterpieces.distinct('type')
    return render_template('masterpiece_edit.html', masterpiece=_new_masterpiece(masterpiece), authors=authors, studios=studios, tags=tags, types=types)


def _get_masterpiece_dirname(masterpiece):
    return os.path.abspath(os.path.join('museum\\static', 'masterpieces', masterpiece['type'], masterpiece['title']))


@home.route('/masterpiece/<oid>/delete/')
def delete_masterpiece(oid):
    masterpiece = mongo.db.masterpieces.find_one_and_delete({'_id': ObjectId(oid)})
    os.removedirs(_get_masterpiece_dirname(masterpiece))
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


@home.route('/author/')
def show_authors():
    authors = mongo.db.authors.find().sort([('name', pymongo.ASCENDING)])
    return render_template('authors.html', authors=authors)


@home.route('/author/add/', methods=['GET', 'POST'])
def add_author():
    if request.method == 'POST':
        data = dict()
        name = request.form.get('name')
        if name:
            data['name'] = name
        other_names = request.form.getlist('other-names')
        if other_names:
            data['other_names'] = filter(lambda x: x, other_names)
        email = request.form.get('email')
        if email:
            data['email'] = email
        qq = request.form.get('qq')
        if qq:
            data['qq'] = qq
        realname = request.form.get('realname')
        if realname:
            data['realname'] = realname
        site = request.form.get('site')
        if site:
            data['site'] = site
        address = request.form.get('address')
        if address:
            data['address'] = address
        zip_ = request.form.get('zip')
        if zip_:
            data['zip'] = zip_
        print data

        mongo.db.authors.insert_one(data)
        return redirect(url_for('home.show_authors'))

    offset = request.args.get('offset')
    if offset:
        if not offset.isdigit():
            abort(400)
        offset = int(offset)
        authors = mongo.db.masterpieces.distinct('author')
        old_author = authors[offset]
    else:
        old_author = dict()

    return render_template('author_add.html', old_author=old_author)


@home.route('/author/<oid>/edit/', methods=['GET', 'POST'])
def edit_author(oid):
    author = mongo.db.authors.find_one({'_id': ObjectId(oid)})
    if not author:
        abort(404)

    if request.method == 'POST':
        data = dict()
        name = request.form.get('name')
        if name:
            data['name'] = name
        other_names = request.form.getlist('other_names')
        if other_names:
            data['other_names'] = other_names
        email = request.form.get('email')
        if email:
            data['email'] = email
        qq = request.form.get('qq')
        if qq:
            data['qq'] = qq
        realname = request.form.get('realname')
        if realname:
            data['realname'] = realname
        site = request.form.get('site')
        if site:
            data['site'] = site
        address = request.form.get('address')
        if address:
            data['address'] = address
        zip_ = request.form.get('zip')
        if zip_:
            data['zip'] = zip_

        mongo.db.authors.update_one({'_id': ObjectId(oid)}, {'$set': data})
        return redirect(url_for('home.show_authors'))

    offset = request.args.get('offset')
    if offset:
        if not offset.isdigit():
            abort(400)
        offset = int(offset)
        authors = mongo.db.masterpieces.distinct('author')
        old_author = authors[offset]
    else:
        old_author = dict()

    return render_template('author_edit.html', author=author, old_author=old_author)


