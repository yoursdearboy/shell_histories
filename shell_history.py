#!/usr/bin/env python
import argparse
import subprocess
from argparse import ArgumentParser
from tempfile import NamedTemporaryFile
from random import shuffle
from base64 import b64decode
from github import Github, GithubException

parser = ArgumentParser(description="Shell history TTS")
parser.add_argument('output')
parser.add_argument('--input-text', type=argparse.FileType('r'))
parser.add_argument('--output-text', type=argparse.FileType('w'))
parser.add_argument('--login')
parser.add_argument('--password')
parser.add_argument('--files', default=20)
parser.add_argument('--lines', default=500)
parser.add_argument('--tts', choices=['google', 'system'], default='google')
args = parser.parse_args()


def fetch_text(login, password, files, lines):
  if login is None or password is None:
    raise RuntimeError("No Github login or password provided")

  g = Github(login, password)

  query = 'filename:.bash_history'
  histories = list(g.search_code(query)[:files])
  shuffle(histories)

  text = ''
  for history in histories:
    try:
      content = b64decode(history.content).decode('utf-8')
      if content is not '':
        presents_text = "%s presents." % (history.repository.full_name)
        content = '\n'.join(content.split('\n')[:lines])
        text += "%s\n%s\n" % (presents_text, content)
    except GithubException:
      print("Failed to load single history file")

  return text

def filter_dups(text):
  new_text = ''
  prelines = []
  for line in text.split('\n'):
    if line in prelines:
      continue
    new_text += "%s\n" % line
    prelines.append(line)
    if len(prelines) > 5:
      prelines.pop(0)
  return new_text

def filter_num_lines(text, n):
  return '\n'.join(text.split('\n')[:n])

if args.input_text is not None:
  text = args.input_text.read()
else:
  text = fetch_text(args.login, args.password, args.files, round(args.lines/5))

text = filter_dups(text)
text = filter_num_lines(text, args.lines)

if args.output_text is not None:
  args.output_text.write(text)

if args.tts == 'system':
  text_file = NamedTemporaryFile(delete=False)
  text_file.write(text.encode('utf-8'))
  text_file.seek(0)
  subprocess.call(['say', '-o', args.output, '-f', text_file.name])
  text_file.close()
elif args.tts == 'google':
  from gtts import gTTS
  with open(args.output, 'wb') as f:
    tts = gTTS(text=text, lang='en')
    tts.write_to_fp(f)
