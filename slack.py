# -*- coding: utf-8 -*-
from slacker import Slacker


class Slack(object):
    def __init__(self, token, username=None, icon_url=None, channels=None):
        self.slack = Slacker(token)
        self.username = username
        self.icon_url = icon_url
        self.channels = channels if channels else ['sandbox', 'debug', 'info', 'warning', 'error', 'critical']

    def send_message(self, message, target='#heartbeat'):
        self.slack.chat.post_message(
            target,
            message,
            username=self.username,
            icon_url=self.icon_url)

    def __getattr__(self, item):
        if item in self.channels:
            return lambda x: self.send_message(x, target=f'#{item}')
        raise AttributeError
