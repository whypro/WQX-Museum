# -*- coding: utf-8 -*-
import yaml
import os
import json
from collections import OrderedDict

from pymongo import MongoClient


def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    class OrderedLoader(Loader):
        pass
    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)

# usage example:
# ordered_load(stream, yaml.SafeLoader)

"""功能：将 yml 文件 转为 json 文件，将其更新（插入）至数据库。最后删除自己。"""

if __name__ == '__main__':

    files = []
    screenshots = []
    metadata = []

    for filename in os.listdir('.'):
        ext = os.path.splitext(filename)[-1].lower()
        fn = filename.decode('GB18030')
        if ext == '.yml':
            metadata.append(fn)
        elif ext in ['.bmp', '.jpg', '.png', '.gif']:
            screenshots.append(fn)
        elif ext in ['.py', '.json']:
            # 忽略
            continue
        else:
            files.append(fn)
    # print files
    # print screenshots
    # print metadata.encode('utf-8')

    for md in metadata:
        with open(md, 'r') as f:
            data = ordered_load(f.read().decode('utf-8'))
            # data = yaml.load(f.read().decode('utf-8'))
            data.setdefault('screenshots', screenshots)
            data.setdefault('files', files)
        # print data

        with open(os.path.splitext(md)[0]+'.json', 'w') as f:
            # print data
            json_str = json.dumps(data, ensure_ascii=False, encoding='utf-8', indent=2)
            f.write(json_str.encode('utf-8'))
            # json.dump(data, f, ensure_ascii=False, encoding='utf-8')

        client = MongoClient()
        db = client['wqx_museum']
        find_condition = dict(title=data['title'])
        if data.get('version'):
            find_condition['version'] = data['version']

        db['masterpieces'].update(find_condition, data, upsert=True)
        client.close()

    os.remove('automatic.py')
