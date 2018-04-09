# maildiff

Gets a notification when forwarded mail never arrive its destination.

## Story

I've been forwarding my email from iCloud to Gmail/Inbox for a while. But lately I've felt some email messages are lost in Gmail. I had the `Delete messages after forwarding` enabled so there's no way I can tell exactly which messages are missing.

I'm using this tool in AWS Lambda and triggered by CloudWatch.

## What It Does

1. Fetch all `unread` mail from iCloud Inbox
2. Search Gmail with [msg-id](https://tools.ietf.org/html/rfc822) from each mail
    1. Mark found mail as `read` and move to `Archive` folder in iCloud
    2. Move not-found mail to `Orphan` folder in iCloud
3. Send out Slack notification for the results

## Prerequisites

- Python 3.6+
- Slack App OAuth Access Token
- App Specific Passwords for iCloud & Gmail

## Usage

### Local

```bash
$ make run
```

### AWS Lambda

```bash
$ make lambda
```

Then upload generated zip file to AWS Lambda and set corresponding CloudWatch rule.
