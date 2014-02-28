from flask.ext.assets import Bundle, Environment

js = Bundle(
    'bower_components/jquery/dist/jquery.js',
    'bower_components/bootstrap/dist/js/bootstrap.min.js',
    'bower_components/bootbox/bootbox.js',
    filters='jsmin',
    output='gen/packed.js')

css = Bundle(
    'bower_components/bootstrap/dist/css/bootstrap.css',
    'css/highlight.css',
    filters='cssmin',
    output='gen/packed.css')

assets = Environment()
assets.register('js_all', js)
assets.register('css_all', css)
