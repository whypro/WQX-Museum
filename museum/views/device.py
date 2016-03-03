# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
from bson.objectid import ObjectId
import datetime

from flask import Blueprint, render_template, redirect, url_for, abort, request
from flask import current_app, send_from_directory, send_file
import pymongo

from ..extensions import mongo
from ..helpers import get_client_ip, get_user_agent


bp_device = Blueprint('device', __name__, url_prefix='/device')


@bp_device.route('/')
def show_devices():
    devices = mongo.db.devices.find()
    return render_template('devices.html', devices=devices)


@bp_device.route('/<oid>/')
def show_device_detail(oid):
    device = mongo.db.devices.find_one({'_id': ObjectId(oid)})
    if not device:
        abort(404)
    return render_template('device_detail.html', device=device)


@bp_device.route('/<oid>/preview/')
def get_device_preview(oid):
    device = mongo.db.devices.find_one({'_id': ObjectId(oid)})
    if not device:
        abort(404)

    if 'pictures' in device and device['pictures']:
        filename = device['pictures'][0]
        path = os.path.join('devices', device['brand'], device['model'], filename)
        return send_file(os.path.join(current_app.config['ASSETS_DIR'], path))
    else:
        path = os.path.join(current_app.static_folder, 'default.bmp')
        return send_file(path)


@bp_device.route('/<oid>/picture/<int:idx>/')
def get_device_picture(oid, idx):
    device = mongo.db.devices.find_one({'_id': ObjectId(oid)})
    if not device:
        abort(404)

    if 'pictures' in device and idx <= len(device['pictures']):
        filename = device['pictures'][idx]
    else:
        abort(404)

    path = os.path.join('devices', device['brand'], device['model'], filename)
    return send_file(os.path.join(current_app.config['ASSETS_DIR'], path))
    # return send_from_directory(current_app.config['ASSETS_DIR'], filename=path)


def _get_device_dirname(device):
    return os.path.abspath(os.path.join(current_app.config['ASSETS_DIR'], 'devices', device['brand'], device['model']))


@bp_device.route('/<oid>/update/')
def update_device_pictures(oid):
    device = mongo.db.devices.find_one({'_id': ObjectId(oid)})
    if not device:
        abort(404)

    pictures = []

    for filename in os.listdir(_get_device_dirname(device)):
        ext = os.path.splitext(filename)[-1].lower()
        if ext in ['.bmp', '.jpg', '.png', '.gif']:
            pictures.append(filename)
        else:
            continue

    print pictures

    mongo.db.devices.update_one({'_id': ObjectId(oid)}, {'$set': {'pictures': pictures}})
    return redirect(url_for('device.show_device_detail', oid=oid))