#!/usr/bin/env python3
#coding: UTF-8

"""
Starts the seafile/seahub server and watches the controller process. It is
the entrypoint command of the docker container.
"""

import json
import os
from os.path import abspath, basename, exists, dirname, join, isdir
import shutil
import sys
import time

from utils import (
    call, get_conf, get_install_dir, get_script, get_command_output,
    wait_for_mysql, setup_logging
)
from upgrade import check_upgrade
from bootstrap import init_seafile_server


shared_seafiledir = '/shared/seafile'
ssl_dir = '/shared/ssl'
generated_dir = '/bootstrap/generated'
installdir = get_install_dir()
topdir = dirname(installdir)

def watch_controller():
    maxretry = 4
    retry = 0
    while retry < maxretry:
        controller_pid = get_command_output('ps aux | grep seafile-monitor.sh | grep -v grep || true').strip()
        garbage_collector_pid = get_command_output('ps aux | grep /scripts/gc.sh | grep -v grep || true').strip()
        if not controller_pid and not garbage_collector_pid:
            retry += 1
        else:
            retry = 0
        time.sleep(5)
    print('seafile monitor exited unexpectedly.')
    sys.exit(1)

def main():
    if not exists(shared_seafiledir):
        os.mkdir(shared_seafiledir)
    if not exists(generated_dir):
        os.makedirs(generated_dir)

    # --- proxy_cache_path injection (download token fix) ---
    # Seafile 13 下载 token 一次性消费，nginx proxy_cache 缓存首次成功响应 60s。
    # proxy_cache_path 必须在 http 块，不在持久化挂载里，所以每次启动注入。
    try:
        _ncf_path = '/etc/nginx/nginx.conf'
        if exists(_ncf_path):
            _ncf = open(_ncf_path).read()
            if 'dl_cache' not in _ncf:
                _cache_line = '    proxy_cache_path /tmp/seafhttp_cache levels=1:2 keys_zone=dl_cache:10m max_size=500m inactive=60s use_temp_path=off;\n'
                _marker = '    include /etc/nginx/sites-enabled/*;'
                if _marker in _ncf:
                    _ncf = _ncf.replace(_marker, _cache_line + _marker)
                    open(_ncf_path, 'w').write(_ncf)
                    print('[start.py] proxy_cache_path injected into nginx.conf')
    except Exception as _e:
        print('[start.py] proxy_cache_path injection failed:', _e)
    # --- end cache injection ---

    try:
        call('nginx -s reload')
    except Exception as e:
        print(e)

    wait_for_mysql()
    init_seafile_server()

    check_upgrade()
    os.chdir(installdir)

    admin_pw = {
        'email': get_conf('INIT_SEAFILE_ADMIN_EMAIL', 'me@example.com'),
        'password': get_conf('INIT_SEAFILE_ADMIN_PASSWORD', 'asecret'),
    }
    password_file = join(topdir, 'conf', 'admin.txt')
    with open(password_file, 'w') as fp:
        json.dump(admin_pw, fp)


    try:
        non_root = os.getenv('NON_ROOT', default='') == 'true'
        if non_root:
            call('su seafile -c "{} start"'.format(get_script('seafile.sh')))
            call('su seafile -c "{} start"'.format(get_script('seahub.sh')))
        else:
            call('{} start'.format(get_script('seafile.sh')))
            call('{} start'.format(get_script('seahub.sh')))
    finally:
        if exists(password_file):
            os.unlink(password_file)

    print('seafile server is running now.')

    # --- seaf-fuse auto-start (FUSE mount for raw file access) ---
    import subprocess
    subprocess.Popen(["/opt/seafile/conf/seaf-fuse-start.sh"],
                     stdout=open("/opt/seafile/logs/seaf-fuse-boot.log", "a"),
                     stderr=subprocess.STDOUT)
    # --- end seaf-fuse auto-start ---

    try:
        watch_controller()
    except KeyboardInterrupt:
        print('Stopping seafile server.')
        sys.exit(0)

if __name__ == '__main__':
    setup_logging()
    main()
