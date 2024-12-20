

class TestBaseClass:
    pass


class TestImplementation(TestBaseClass):
    def __init__(self, value=None):
        self.value = value


class SpecialImplementation(TestBaseClass):
    def __init__(self, special_value=None):
        self.special_value = special_value
