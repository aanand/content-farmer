from __future__ import unicode_literals

import tweepy

import os
import sys
import subprocess
import tempfile

import logging
log = logging.getLogger(__name__)


temp_dir = './tmp'


def main():
    query = sys.argv[1]

    auth = tweepy.OAuthHandler(os.environ['TWITTER_CONSUMER_KEY'], os.environ['TWITTER_CONSUMER_SECRET'])
    auth.set_access_token(os.environ['TWITTER_ACCESS_TOKEN'], os.environ['TWITTER_ACCESS_TOKEN_SECRET'])

    api = tweepy.API(auth)
    tweets = api.search(query, count=100)
    log.info("Got {} tweets".format(len(tweets)))

    urls = list(get_frame_urls(tweets))
    log.info("Using {} tweets".format(len(urls)))

    frames = list(get_frames(urls))
    log.info("Made {} frames".format(len(frames)))

    if len(frames) == 0:
        return

    gif_filename = make_gif(frames)
    log.info("Wrote {}".format(gif_filename))


def make_gif(frames):
    _, gif_filename = tempfile.mkstemp('.gif', dir=temp_dir)

    cmd = ['convert', '-loop', '0', '-delay', '8', '-layers', 'Optimize']
    cmd += frames
    cmd.append(gif_filename)
    check_call(cmd)

    return gif_filename


def get_frames(urls):
    for url in urls:
        _, filename = tempfile.mkstemp('.png', dir=temp_dir)
        cmd = [
            'wkhtmltoimage',
            '--user-style-sheet', 'user.css',
            '--width', '670',
            url,
            filename,
        ]
        check_call(cmd)
        yield filename


def get_frame_urls(tweets):
    for t in tweets:
        if '@' in t.text:
            log.info("Skipping: {}".format(t.text))
            continue

        media = t.entities.get('media', [])
        photos = [m for m in media if m.get('type') == 'photo']
        if len(photos) > 0:
            yield tweet_url(t)


def tweet_url(tweet):
    return "http://twitter.com/" + tweet.author.screen_name + "/status/" + str(tweet.id)


def check_call(cmd, *args, **kwargs):
    log.info("$ %s" % " ".join(cmd))
    output = ""

    try:
        output = subprocess.check_output(cmd, *args, **kwargs)
    except subprocess.CalledProcessError:
        log.error(output)
        raise


def start_logging():
    stderr = logging.StreamHandler()
    stderr.setLevel(logging.DEBUG)
    stderr.setFormatter(logging.Formatter(fmt='%(levelname)8s: %(message)s'))

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(stderr)


if __name__ == '__main__':
    start_logging()
    main()

