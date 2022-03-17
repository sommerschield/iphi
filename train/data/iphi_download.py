# Copyright 2021 Thea Sommerschield, Jonathan Prag,
# Marita Chatzipanagiotou, John Pavlopoulos, Ion Androutsopoulos,
# University of Oxford, DeepMind Technologies Limited, Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
from collections import Counter
import concurrent.futures
import glob
import json
import os
import random
import re
import requests

from bs4 import BeautifulSoup
import cloudscraper
from tqdm import tqdm

from ithaca.util.alphabet import GreekAlphabet
from train.data.iphi_dates import date_parser_phi
from train.data.iphi_text_clean import strip_accents
from train.data.iphi_text_clean import text_clean_phi
from train.data.iphi_text_clean import text_to_sentences


p = argparse.ArgumentParser(prog='I.PHI', description='I.PHI JSON downloader.')
p.add_argument('--connections', default=1, type=int, metavar='N',
               help='number of connections')
p.add_argument('--timeout', default=5, type=int, metavar='N',
               help='seconds to timeout')
p.add_argument('--output_dir',
               default='train/data/iphi-json/', type=str,
               help='output path')
p.add_argument('--output_json',
               default='train/data/iphi.json', type=str,
               help='output json dataset')
p.add_argument('--output_word_list',
               default='train/data/iphi-wordlist.txt',
               type=str, help='output wordlist')
p.add_argument('--output_region_main_list',
               default='train/data/iphi-region-main.txt',
               type=str, help='output region main list')
p.add_argument('--output_region_sub_list',
               default='train/data/iphi-region-sub.txt',
               type=str, help='output region sub list')
p.add_argument('--min_text_len', default=10, type=int, metavar='N',
               help='maximum text length')
p.add_argument('--max_phi_id', default=400000, type=int, metavar='N',
               help='maximum PHI inscription id')
p.add_argument('--max_retries_per_inscription', default=10,
               type=int, metavar='N', help='maximum retries per inscription')
p.add_argument('--limit_phi_id', default=0, type=int, metavar='N',
               help='get a limited sample')
p.add_argument('--local', action='store_true', default=False)
FLAGS = p.parse_args()


def load_phi_id(phi_id, timeout, output, client, headers, alphabet):
  '''Fetches the given PHI id.'''
  file_path = os.path.join(output, '{}.html'.format(phi_id))

  # Check if a file already exists
  path_exists = FLAGS.local or os.path.exists(file_path)
  if path_exists:
    with open(file_path, 'r') as f:
      req_text = f.read().strip()
  else:
    req_text = None
    retries = 0
    while retries <= FLAGS.max_retries_per_inscription and (
            req_text is None or '520: Web server is returning an unknown error' in req_text):

      req = client.get(
          'https://epigraphy.packhum.org/text/{}'.format(phi_id),
          timeout=timeout, headers=headers)
      req_text = req.text

  if 'Invalid PHI Inscription Number' not in req_text:
    try:
      soup = BeautifulSoup(req_text, 'lxml')

      # Grab the text
      lines = []
      table = soup.find('table', attrs={'class': 'grk'})
      for row in table.find_all('tr'):
        tds = row.find_all('td')
        for td_i, td in enumerate(tds):
          if 'class' in td.attrs and td.attrs['class'][0] == 'id':
            continue
          lines.append(td.get_text().strip())
      text = '\n'.join(lines)

      # Clean text
      text = text_clean_phi(text, alphabet)
      sentences = text_to_sentences(text, alphabet)
      text = ' '.join([s + '.' for s in sentences])

      # Strip accents
      text = strip_accents(text)

      # Grab main and sub region
      region_main, region_sub = '', ''
      region_main_id, region_sub_id = -1, -1
      hdr1 = soup.find('div', attrs={'class': 'hdr1'})
      if hdr1:
        hdr1_a = hdr1.find_all('a')
        if hdr1_a and len(hdr1_a) == 3:
          region_main_id = hdr1_a[1]['href'].replace('/regions/', '')
          region_main = hdr1_a[1].get_text()
          region_sub_id = hdr1_a[2]['href'].replace('/regions/', '')
          region_sub = hdr1_a[2].get_text()
        elif hdr1_a and len(hdr1_a) == 2:
          region_main_id = hdr1_a[1]['href'].replace('/regions/', '')
          region_main = hdr1_a[1].get_text()

      # Grab the metadata
      metadata = soup.find('span', attrs={'class': 'ti'})
      if metadata:
        metadata = metadata.get_text()
      else:
        metadata = ''

      # Time
      date_str = ''
      date_min = None
      date_max = None
      date_circa = None
      for tok in metadata.split('—'):
        if re.search(
                r'\W(BC|AD|period|reign|a\.|p\.(?!\s+\d)|aet\.)(\W|$)', tok):
          date_str = tok
          date_range, circa = date_parser_phi(tok)
          if date_range:
            date_min, date_max = date_range.split(' ')
            date_circa = circa

      # Output dictionary
      output = {
          'id': phi_id,
          'text': text,
          'metadata': metadata,
          'region_main_id': region_main_id,
          'region_main': region_main,
          'region_sub_id': region_sub_id,
          'region_sub': region_sub,
          'date_str': date_str,
          'date_min': date_min,
          'date_max': date_max,
          'date_circa': date_circa,
      }

      # Write intermediate output file
      if not path_exists:
        with open(file_path, 'w') as f:
          f.write(req_text)

      if len(output['text'].replace(alphabet.missing, '')) >= FLAGS.min_text_len:
        return output
      return
    except:
      print(req_text)
      return


def counter_to_file(cnt, filepath):
  with open(filepath, 'w') as f:
    output = '\n'.join(
        ['{};{}'.format(c, c_count) for c, c_count in
         cnt.most_common()])
    f.write(output)


def main():
  # Create structure
  os.makedirs(FLAGS.output_dir, exist_ok=True)

  # Dataset list
  dataset = []

  # Greek alphabet
  alphabet = GreekAlphabet()

  # Inscriptions list
  if FLAGS.limit_phi_id > 0:
    random.seed(123)
    range_ids = [random.randint(1, FLAGS.max_phi_id) for _ in
                 range(FLAGS.limit_phi_id)]
  else:
    if FLAGS.local:
      def get_filename_noext(x): return os.path.splitext(os.path.basename(x))[0]
      range_ids = list(
          map(get_filename_noext, glob.glob(
              f'{FLAGS.output_dir}/*.html')))
      range_ids = list(map(int, range_ids))
    else:
      range_ids = list(range(1, FLAGS.max_phi_id))

  # Download inscriptions
  if FLAGS.connections == 1:
    client = requests
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
    }
    for text_i in tqdm(range_ids):
      result = load_phi_id(text_i, FLAGS.timeout, FLAGS.output_dir, client,
                           headers, alphabet)
      if result:
        dataset.append(result)
  else:
    client = cloudscraper.create_scraper()
    headers = {}
    with concurrent.futures.ThreadPoolExecutor(
            max_workers=FLAGS.connections) as executor:
      future_to_phi = (
          executor.submit(load_phi_id, text_i, FLAGS.timeout, FLAGS.output_dir,
                          client, headers, alphabet) for text_i in range_ids)
      for future in tqdm(concurrent.futures.as_completed(future_to_phi),
                         total=len(range_ids)):
        try:
          output = future.result()
          if output:
            dataset.append(output)
        except:
          pass

  # Write the dataset as a JSON file.
  with open(FLAGS.output_json, 'w') as f:
    json.dump(dataset, f)

  print('Dataset size:', len(dataset))

  # Generate word list and region list.
  cnt_word = Counter()
  cnt_region_main = Counter()
  cnt_region_sub = Counter()
  for d in dataset:
    for word in re.findall(r'\w+', d['text']):
      cnt_word[word] += 1

    region_main_k = '{}_{}'.format(d['region_main'], d['region_main_id'])
    cnt_region_main[region_main_k] += 1

    region_sub_k = '{}_{}'.format(d['region_sub'], d['region_sub_id'])
    cnt_region_sub[region_sub_k] += 1

  # Write counters.
  counter_to_file(cnt_word, FLAGS.output_word_list)
  print('Word list size:', len(cnt_word))

  counter_to_file(cnt_region_main, FLAGS.output_region_main_list)
  print('Region main size:', len(cnt_region_main))

  counter_to_file(cnt_region_sub, FLAGS.output_region_sub_list)
  print('Region sub size:', len(cnt_region_sub))


if __name__ == '__main__':
  main()
