class Mocker(object):

    def __init__(self):
        self.datas = []

    def add_mock(self, type, value, param_name=None):
        self.datas.append((type, value, param_name))

    def __iter__(self):
        return iter(self.datas)
