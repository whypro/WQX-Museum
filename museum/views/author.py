# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import Blueprint, render_template, redirect, url_for, abort, request
import pymongo
from bson.objectid import ObjectId

from ..extensions import mongo


bp_author = Blueprint('author', __name__, url_prefix='/author')


@bp_author.route('/')
def show_authors():
    authors = mongo.db.authors.find().sort([('name', pymongo.ASCENDING)])
    return render_template('authors.html', authors=authors)


@bp_author.route('/add/', methods=['GET', 'POST'])
def add_author():
    if request.method == 'POST':
        data = dict()
        name = request.form.get('name')
        if name:
            data['name'] = name
        other_names = request.form.getlist('other-names')
        other_names = filter(lambda x: x, other_names)
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
        print data

        mongo.db.authors.insert_one(data)
        return redirect(url_for('author.show_authors'))

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


@bp_author.route('/<oid>/edit/', methods=['GET', 'POST'])
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
        return redirect(url_for('author.show_authors'))

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


@bp_author.route('/<oid>/')
def show_author_detail(oid):
    author = mongo.db.authors.find_one({'_id': ObjectId(oid)})
    if not author:
        abort(404)

    masterpieces = mongo.db.masterpieces.find({'author_oid': ObjectId(oid)})
    author['masterpieces'] = masterpieces
    # print author['masterpieces']
    return render_template('author_detail.html', author=author)

