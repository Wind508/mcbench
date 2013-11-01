class Query(object):
    def __init__(self, xpath, name=None):
        self.xpath = xpath
        self.name = name

    def __repr__(self):
        return '<Query: %s>' % (self.name or self.xpath)
