class Query(object):
    def __init__(self, id, xpath, name=None):
        self.id = id
        self.xpath = xpath
        self.name = name

    def __repr__(self):
        return '<Query: %s>' % (self.name or self.xpath)
