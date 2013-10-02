import flask

import mcbench.client

app = flask.Flask(__name__)
app.config.from_object('conf')

mcbench_client = mcbench.client.from_redis_url(app.config['REDIS_URL'])


@app.route('/', methods=['GET'])
def index():
    return flask.render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)
