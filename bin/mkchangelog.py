import datetime
import re
import sys
import git

URL = 'https://github.com/miguelgrinberg/flask-socketio'
merges = {}


def format_message(commit):
    if commit.message.startswith('Version '):
        return ''
    if '#nolog' in commit.message:
        return ''
    if commit.message.startswith('Merge pull request'):
        pr = commit.message.split('#')[1].split(' ')[0]
        message = ' '.join([line for line in [line.strip() for line in commit.message.split('\n')[1:]] if line])
        merges[message] = pr
        return ''
    if commit.message.startswith('Release '):
        return '\n**{message}** - {date}\n'.format(
            message=commit.message.strip(),
            date=datetime.datetime.fromtimestamp(commit.committed_date).strftime('%Y-%m-%d'))
    message = ' '.join([line for line in [line.strip() for line in commit.message.split('\n')] if line])
    if message in merges:
        message += ' #' + merges[message]
    message = re.sub('\\(.*(#[0-9]+)\\)', '\\1', message)
    message = re.sub('Fixes (#[0-9]+)', '\\1', message)
    message = re.sub('fixes (#[0-9]+)', '\\1', message)
    message = re.sub('#([0-9]+)', '[#\\1]({url}/issues/\\1)'.format(url=URL), message)
    message += ' ([commit]({url}/commit/{sha}))'.format(url=URL, sha=str(commit))
    if commit.author.name != 'Miguel Grinberg':
        message += ' (thanks **{name}**!)'.format(name=commit.author.name)
    return '- ' + message


def main(all=False):
    repo = git.Repo()

    for commit in repo.iter_commits():
        if not all and commit.message.startswith('Release '):
            break
        message = format_message(commit)
        if message:
            print(message)


if __name__ == '__main__':
    main(all=len(sys.argv) > 1 and sys.argv[1] == 'all')
