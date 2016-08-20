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


@bp_device.route('/add/', methods=['GET', 'POST'])
def add_device():
    if request.method == 'POST':
        brand = request.form.get('brand')
        model = request.form.get('model')
        if not brand or not model:
            return redirect(url_for('device.add_device'))
        data = dict(brand=brand, model=model)
        alias = request.form.get('alias')
        if alias:
            data['alias'] = alias
        dimension = request.form.getlist('dimension')
        dimension = filter(lambda x: x, dimension)
        if dimension:
            data['dimension'] = map(lambda x: float(x), dimension)
        net_weight = request.form.get('net-weight')
        if net_weight:
            data.setdefault('weight', dict())
            data['weight']['net_weight'] = float(net_weight)
        with_battery_weight = request.form.get('with-battery-weight')
        if with_battery_weight:
            data.setdefault('weight', dict())
            data['weight']['with_battery_weight'] = float(with_battery_weight)
        screen = request.form.getlist('screen')
        screen = filter(lambda x: x, screen)
        if len(screen) == 2:
            data['screen'] = map(lambda x: int(x), screen)
        battery = request.form.get('battery')
        if battery:
            data['battery'] = battery
        print data

        result = mongo.db.devices.insert_one(data)
        print result.inserted_id
        device = mongo.db.devices.find_one({'_id': ObjectId(result.inserted_id)})
        os.makedirs(_get_device_dirname(device))

        return redirect(url_for('device.show_device_detail', oid=result.inserted_id))

    copy_oid = request.args.get('copy')
    if copy_oid:
        copy_device = mongo.db.devices.find_one({'_id': ObjectId(copy_oid)})
        if not copy_device:
            abort(400)
    else:
        copy_device = dict()

    return render_template('device_add.html', device=copy_device)


@bp_device.route('/<oid>/edit/', methods=['GET', 'POST'])
def edit_device(oid):
    device = mongo.db.devices.find_one({'_id': ObjectId(oid)})
    if not device:
        abort(404)

    if request.method == 'POST':
        brand = request.form.get('brand')
        model = request.form.get('model')
        if not brand or not model:
            return redirect(url_for('device.edit_device'))
        data = dict(brand=brand, model=model)
        alias = request.form.get('alias')
        if alias:
            data['alias'] = alias
        dimension = request.form.getlist('dimension')
        dimension = filter(lambda x: x, dimension)
        if len(dimension) == 3:
            data['dimension'] = map(lambda x: float(x), dimension)
        net_weight = request.form.get('net-weight')
        if net_weight:
            data.setdefault('weight', dict())
            data['weight']['net_weight'] = float(net_weight)
        with_battery_weight = request.form.get('with-battery-weight')
        if with_battery_weight:
            data.setdefault('weight', dict())
            data['weight']['with_battery_weight'] = float(with_battery_weight)
        screen = request.form.getlist('screen')
        screen = filter(lambda x: x, screen)
        if len(screen) == 2:
            data['screen'] = map(lambda x: int(x), screen)
        battery = request.form.get('battery')
        if battery:
            data['battery'] = battery
        print data

        mongo.db.devices.update_one({'_id': ObjectId(oid)}, {'$set': data})
        new_device = mongo.db.devices.find_one({'_id': ObjectId(oid)})

        old_dirname, new_dirname = _get_device_dirname(device), _get_device_dirname(new_device)
        if new_dirname != old_dirname:
            os.renames(old_dirname, new_dirname)

        return redirect(url_for('device.show_device_detail', oid=oid))

    return render_template('device_edit.html', device=device)


@bp_device.route('/<oid>/delete/')
def delete_device(oid):
    device = mongo.db.devices.find_one_and_delete({'_id': ObjectId(oid)})
    os.removedirs(_get_device_dirname(device))
    return redirect(url_for('device.show_devices'))
