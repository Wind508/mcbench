import flask

import mcbench.highlighters
from mcbench.models import db

app = flask.Flask(__name__)
app.config.from_object('mcbench.settings')
app.jinja_env.filters['highlight_matlab'] = mcbench.highlighters.matlab
app.jinja_env.filters['highlight_xml'] = mcbench.highlighters.xml
db.init(app.config['DB_PATH'])

import mcbench.views
