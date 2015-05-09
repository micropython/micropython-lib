def attrgetter(attr):
    assert "." not in attr
    def _attrgetter(obj):
        return getattr(obj, attr)
    return _attrgetter
