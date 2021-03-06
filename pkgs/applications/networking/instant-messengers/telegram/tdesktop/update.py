#! /usr/bin/env nix-shell
#! nix-shell -i python3 -p python3 nix

import fileinput
import json
import os
import re
import subprocess

from datetime import datetime
from urllib.request import urlopen, Request


DIR = os.path.dirname(os.path.abspath(__file__))
HEADERS = {'Accept': 'application/vnd.github.v3+json'}


def github_api_request(endpoint):
    base_url = 'https://api.github.com/'
    request = Request(base_url + endpoint, headers=HEADERS)
    with urlopen(request) as http_response:
        return json.loads(http_response.read().decode('utf-8'))


def get_commit_date(repo, sha):
    url = f'https://api.github.com/repos/{repo}/commits/{sha}'
    request = Request(url, headers=HEADERS)
    with urlopen(request) as http_response:
        commit = json.loads(http_response.read().decode())
        date = commit['commit']['committer']['date'].rstrip('Z')
        date = datetime.fromisoformat(date).date().isoformat()
        return 'unstable-' + date


def nix_prefetch_url(url, unpack=False):
    """Prefetches the content of the given URL."""
    print(f'nix-prefetch-url {url}')
    options = ['--type', 'sha256']
    if unpack:
        options += ['--unpack']
    out = subprocess.check_output(['nix-prefetch-url'] + options + [url])
    return out.decode('utf-8').rstrip()


def update_file(relpath, version, sha256, rev=None):
    file_path = os.path.join(DIR, relpath)
    with fileinput.FileInput(file_path, inplace=True) as f:
        for line in f:
            result = line
            result = re.sub(r'^  version = ".+";', f'  version = "{version}";', result)
            result = re.sub(r'^    sha256 = ".+";', f'    sha256 = "{sha256}";', result)
            if rev:
                result = re.sub(r'^    rev = ".*";', f'    rev = "{rev}";', result)
            print(result, end='')


if __name__ == "__main__":
    tdesktop_tag = github_api_request('repos/telegramdesktop/tdesktop/releases/latest')['tag_name']
    tdesktop_version = tdesktop_tag.lstrip('v')
    tdesktop_hash = nix_prefetch_url(f'https://github.com/telegramdesktop/tdesktop/releases/download/{tdesktop_tag}/tdesktop-{tdesktop_version}-full.tar.gz')
    update_file('default.nix', tdesktop_version, tdesktop_hash)
    tg_owt_ref = github_api_request('repos/desktop-app/tg_owt/commits/master')['sha']
    tg_owt_version = get_commit_date('desktop-app/tg_owt', tg_owt_ref)
    tg_owt_hash = 'TODO'
    update_file('tg_owt.nix', tg_owt_version, tg_owt_hash, tg_owt_ref)
    tg_owt_ref = github_api_request('repos/desktop-app/tg_owt/commits/master')['sha']
    libtgvoip_ref = github_api_request(f'repos/telegramdesktop/tdesktop/contents/Telegram/ThirdParty/libtgvoip?ref={tdesktop_tag}')['sha']
    libtgvoip_version = get_commit_date('telegramdesktop/libtgvoip', libtgvoip_ref)
    libtgvoip_hash = nix_prefetch_url(f'https://github.com/telegramdesktop/libtgvoip/archive/{libtgvoip_ref}.tar.gz', unpack=True)
    update_file('../../../../../development/libraries/libtgvoip/default.nix', libtgvoip_version, libtgvoip_hash, libtgvoip_ref)
