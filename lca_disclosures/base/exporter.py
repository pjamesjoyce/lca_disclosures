import json
import os

class BaseExporter(object):

    def write(self):
        
        if isinstance(self.folder_path, str):

            if not os.path.isdir(self.folder_path):
                os.mkdir(self.folder_path)

            full_efn = os.path.join(self.folder_path, self.efn)

        else:
            full_efn = self.efn

        with open(full_efn, 'w') as f:
            json.dump(self.data, f)

        return full_efn
