# Copyright 2019 3YOURMIND GmbH

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import pickle


class Cache(dict):
    def __init__(self, django_folder, database, cache_path):
        self.filename = os.path.join(
            cache_path,
            "{0}_{1}.pickle".format(django_folder.replace(os.sep, "_"), database),
        )

        if not os.path.exists(os.path.dirname(self.filename)):
            os.makedirs(os.path.dirname(self.filename))

        super(Cache, self).__init__()

    def load(self):
        try:
            with open(self.filename, "rb") as f:
                tmp_dict = pickle.load(f)
                self.update(tmp_dict)
        except IOError:
            pass

    def save(self):
        with open(self.filename, "wb") as f:
            pickle.dump(self, f, protocol=2)
