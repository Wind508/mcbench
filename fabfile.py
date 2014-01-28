from fabric.api import sudo, cd, env, run, local

env.hosts = ['ibadaw@sableamd2.cs.mcgill.ca']

DEPLOY_DIR = '/var/www/mcbench/mcbench'


def deploy():
    with cd(DEPLOY_DIR):
        run('git pull origin master')
    restart()


def restart():
    sudo('service httpd restart')


def test():
    local('nosetests')


def coverage():
    nose_flags = [
        '--with-coverage',
        '--cover-html',
        '--cover-package=app,manage,mcbench'
    ]
    local('nosetests ' + ' '.join(nose_flags))
