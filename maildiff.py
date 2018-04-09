import datetime
import email.header
import imaplib
import json
from typing import List

from imapclient import IMAPClient, SEEN
from slack import Slack

with open('config.json') as config:
    CONFIG = json.load(config)


def decode_header(text):
    decoded_header = email.header.decode_header(text)[0][0]
    return decoded_header if isinstance(decoded_header, str) else decoded_header.decode()


class Mail(object):
    def __init__(self, uid, raw):
        self.envelope = raw[b'ENVELOPE']
        self.internal_date = raw[b'INTERNALDATE']
        self.message_id = self.envelope.message_id.decode().strip().strip('<>')
        self.uid = uid

    @property
    def from_addresses(self):
        return [decode_header(str(f)) for f in self.envelope.from_]

    @property
    def subject(self):
        return decode_header(self.envelope.subject.decode())

    def __str__(self) -> str:
        return f'`{", ".join(self.from_addresses)}` `{self.subject}`'


class Mailbox(object):
    GMAIL = 'smtp.gmail.com'
    ICLOUD = 'imap.mail.me.com'

    def __init__(self, server: str, username: str, password: str, folders: List[str] = None):
        self._server = server
        self.imap = IMAPClient(server, use_uid=True)
        self.imap.login(username, password)
        self.folders = folders

    def __contains__(self, mail: Mail) -> bool:
        if self._server == Mailbox.GMAIL:
            for folder in self.folders:
                self.imap.select_folder(folder)
                if self.imap.gmail_search(f'rfc822msgid:{mail.message_id}'):
                    return True
        else:
            for folder in self.imap.list_folders():
                self.imap.select_folder(folder[2])
                if self.imap.search(['HEADER', 'MESSAGE-ID', mail.message_id]):
                    return True
        return False

    def unreads(self, folder='INBOX') -> List[Mail]:
        self.imap.select_folder(folder)
        all_mails = self.imap.fetch(self.imap.search('UNSEEN'), ['INTERNALDATE', 'ENVELOPE'])
        return [Mail(uid, all_mails[uid]) for uid in all_mails]

    def move(self, mail: Mail, destination: str) -> None:
        if self._server not in [Mailbox.ICLOUD]:
            try:
                self.imap.move(mail.uid, destination)
                return
            except imaplib.IMAP4.error as ex:
                print(f'Failed to move message [{ex}], trying copy-and-delete instead...')
        self.imap.copy(mail.uid, destination)
        self.imap.delete_messages(mail.uid)

    def read(self, mail: Mail):
        self.imap.add_flags(mail.uid, [SEEN])

    def logout(self):
        self.imap.logout()


def main(*args, **kwargs):  # pylint: disable=W0613
    slack = Slack(token=CONFIG['SLACK_TOKEN'], username='maildiff.py')

    for user in CONFIG['CREDENTIALS']:
        try:
            cred = CONFIG['CREDENTIALS'][user]
            icloud = Mailbox(server=Mailbox.ICLOUD, username=cred['icloud']['username'], password=cred['icloud']['password'])

            icloud_unreads = icloud.unreads()
            slack.debug(f'[{user}] Processing {len(icloud_unreads)} messages from iCloud...')

            if icloud_unreads:
                gmail = Mailbox(
                    server=Mailbox.GMAIL,
                    username=cred['gmail']['username'],
                    password=cred['gmail']['password'],
                    folders=cred['gmail']['folders']
                )

                try:
                    for mail in icloud_unreads:
                        if mail in gmail:
                            slack.debug(f'[{user}] Found email {mail} in Gmail.')
                            icloud.read(mail)
                            icloud.move(mail, cred['icloud']['archive'])
                        else:
                            if mail.internal_date + datetime.timedelta(minutes=CONFIG['TIMEOUT']) < datetime.datetime.now():
                                slack.warning(f'[{user}] Missing email {mail}.\nMoving it to *{cred["icloud"]["orphan"]}*.')
                                icloud.move(mail, cred['icloud']['orphan'])
                            else:
                                slack.debug(f'[{user}] Cannot find email {mail} in Gmail. Keep waiting...')
                finally:
                    gmail.logout()
        except Exception as ex:  # pylint: disable=W0703
            slack.critical(f'Critical error occurs: *{ex}*')
        finally:
            icloud.logout()


if __name__ == '__main__':
    main()
