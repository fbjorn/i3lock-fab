import re
import os
import random
import subprocess
import time
from tempfile import NamedTemporaryFile
from uuid import uuid4
from threading import Thread

import requests
import yaml

LINUX_CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.config')
APP_DIR = os.path.join(LINUX_CONFIG_DIR, '.{}'.format('i3lock-fab'))
ORIGINAL_IMG = os.path.join(APP_DIR, 'background.png')
OUTPUT_IMG = os.path.join(APP_DIR, 'out.png')
CONF_PATH = os.path.join(APP_DIR, 'conf.yaml')

DISPLAY_RE = r'(\d+)x(\d+)\+(\d+)\+(\d+)'
IMAGE_URL_RE = r'https?://[^ ]+?jpg'
DEFAULT_CONF = {
    'random_pic': True,
    'url': 'https://www.reddit.com/r/wallpaper/',
    'show_failed_attempts': True,
    'no_unlock_indicator': False,
    'proxies': {
        'http': '',
        'https': ''
    },
}


def run_in_shell(*cmd):
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = process.communicate()
    exit_code = process.returncode
    return exit_code, stdout.decode('utf8'), stderr.decode('utf8')


def prepare_stuff():
    for path in (LINUX_CONFIG_DIR, APP_DIR):
        if not os.path.exists(path):
            os.makedirs(path)
    if not os.path.exists(OUTPUT_IMG):
        make_black_image((1366, 768), OUTPUT_IMG)
    if not os.path.exists(CONF_PATH):
        with open(CONF_PATH, 'w') as conf_file:
            conf_file.write(yaml.dump(DEFAULT_CONF, default_flow_style=False))


def load_user_conf():
    conf = DEFAULT_CONF.copy()
    try:
        with open(CONF_PATH) as conf_file:
            conf.update(yaml.load(conf_file.read()))
    except Exception as exc:
        exception_handler(exc)
    if not conf['proxies']['http'] and not conf['proxies']['https']:
        del conf['proxies']
    return conf


def make_black_image(size, output):
    geometry = '{}x{}'.format(*size)
    run_in_shell('convert', '-size', geometry, 'xc:black', output)


def make_huge_image():
    output_img_width = 0
    output_img_height = 0
    args = []
    _, xrandr_output, _ = run_in_shell('xrandr')
    screen_sizes = re.findall(DISPLAY_RE, xrandr_output)
    for i, size in enumerate(screen_sizes):
        width, height, x, y = [int(x) for x in size]
        geometry = '{}X{}^'.format(width, height)
        crop = '{}X{}+0+0'.format(width, height)
        out_img = '/tmp/i3lock-fab-{}.png'.format(i)
        run_in_shell(
            'convert', ORIGINAL_IMG, '-resize', geometry, '-gravity', 'Center',
            '-crop', crop, '+repage', out_img
        )
        if output_img_width < width + x:
            output_img_width = width + x
        if output_img_height < height + y:
            output_img_height = height + y

        geometry = '+{}+{}'.format(x, y)
        args.extend([out_img, '-geometry', geometry, '-composite'])
    make_black_image((output_img_width, output_img_height), OUTPUT_IMG)
    cmd = ['convert', OUTPUT_IMG] + args + [OUTPUT_IMG]
    run_in_shell(*cmd)


def get_random_image_url(url, proxies=None):
    headers = {'User-Agent': str(uuid4())}
    response = requests.get(url, headers=headers, proxies=proxies)
    html = response.content.decode('utf8')
    urls = set([
        url for url in re.findall(IMAGE_URL_RE, html)
        if len(url) < 35 and 'out' not in url
    ])
    return random.choice(list(urls))


def download_image(url, output, proxies=None):
    headers = {'User-Agent': str(uuid4())}
    image = requests.get(url, headers=headers, proxies=proxies).content
    with open(output, 'wb') as out:
        out.write(image)


def lock_computer(conf, bkg_image):
    keys = []
    if conf['no_unlock_indicator']:
        keys.append('-u')
    if conf['show_failed_attempts']:
        keys.append('-f')
    cmd = ['i3lock', '-e'] + keys + ['-i', bkg_image]
    run_in_shell(*cmd)


def bkg_worker(conf):
    try:
        proxies = conf.get('proxies')
        url = get_random_image_url(conf['url'], proxies)
        download_image(url, ORIGINAL_IMG, proxies)
        make_huge_image()
    except Exception as exc:
        exception_handler(exc)


def exception_handler(exc):
    prefix = 'i3lock-fab-{}'.format(int(time.time()))
    with NamedTemporaryFile(prefix=prefix, delete=False, mode='w') as log:
        log.write(str(exc))


def main():
    try:
        prepare_stuff()
        conf = load_user_conf()
        image_path = ORIGINAL_IMG
        if conf['random_pic']:
            Thread(target=bkg_worker, args=(conf,)).start()
            image_path = OUTPUT_IMG
        lock_computer(conf, image_path)
    except Exception as exc:
        exception_handler(exc)


if __name__ == '__main__':
    main()
