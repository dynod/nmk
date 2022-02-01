from nmk.model.resolver import NmkConfigResolver


class FaillingResolver(NmkConfigResolver):
    pass


class BadTypeResolver:
    def __init__(self, some_stuff):
        pass
