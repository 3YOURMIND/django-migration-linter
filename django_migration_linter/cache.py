# Copyright 2018 3YOURMIND GmbH

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import hashlib
import os
import pickle

from django_migration_linter.utils import split_path, compose_migration_path


class Cache(dict):
    def __init__(self, django_folder, cache_path):
        self.django_folder = django_folder
        project_name = split_path(django_folder)[-2]
        self.filename = \
            os.path.join(cache_path, '{0}.pickle'.format(project_name))

        if not os.path.exists(os.path.dirname(self.filename)):
            os.makedirs(os.path.dirname(self.filename))

        super(Cache, self).__init__()

    def load(self):
        try:
            f = open(self.filename, 'rb')
            tmp_dict = pickle.load(f)
            self.update(tmp_dict)
            f.close()
        except IOError:
            pass

    def save(self):
        f = open(self.filename, 'wb')
        pickle.dump(self, f, 2)
        f.close()

    def md5(self, app_name, migration):
        path = compose_migration_path(self.django_folder, app_name, migration)
        hash_md5 = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
