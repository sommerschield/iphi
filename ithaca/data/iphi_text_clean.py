"""
Copyright 2021 Thea Sommerschield, Jonathan Prag,
Marita Chatzipanagiotou, John Pavlopoulos, Ion Androutsopoulos,
University of Oxford, DeepMind Technologies Limited, Google LLC

Licensed under the Apache License, Version 2.0 (the 'License');
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an 'AS IS' BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import re
import unicodedata

from nltk import tokenize


def strip_accents(s):
  '''Strips all accents.'''
  return ''.join(c for c in unicodedata.normalize('NFD', s) if
                 unicodedata.category(c) != 'Mn')


def text_to_sentences(t, alphabet):
  '''Tokenizes sentences and removes the empty ones.'''
  sentences = []
  for s in tokenize.sent_tokenize(t):
    # remove all puntuation from sentence
    s = re.sub(r'[%s]+' % ''.join(alphabet.punctuation), ' ', s)

    # collapse spaces
    s = re.sub(r'\s+', ' ', s).strip()

    # append sentence
    if len(s) > 1:
      sentences.append(s)
  return sentences


def text_clean_phi(text_cleaned, alphabet):
  '''Converts an inscription text to a machine-actionable format.'''

  # Remove lines that start with
  text_cleaned = re.sub(r'^(IG|SEG|BCH|Agora|vacat) .*\n?',
                        '', text_cleaned, flags=re.MULTILINE)

  # Replace double brackets with single
  text_cleaned = text_cleaned.replace('〚', '[').replace('〛', ']')

  # Remove everything after vacat
  text_cleaned = re.sub(r'vacat .*\n?', '\n', text_cleaned, flags=re.MULTILINE)

  # Split on :
  text_cleaned = re.sub(r' [:∶]+ ', '. ', text_cleaned)

  # Join lines ending with -
  text_cleaned = re.sub(r'-\n', r'', text_cleaned)

  # Remove Greek numerals with ʹ
  text_cleaned = re.sub(r'[\w∙]+ʹ', r'', text_cleaned)

  # Remove Greek numerals
  word_boundary = r'([\s\.\⏑\—\-\-\,⏑․\[\]]|$|^)'
  greek_numerals = re.escape(
      '∶ΠT𐅈𐅃𐅉ϛ𐅀𐅁𐅂Ι𐅃ΔͰΗΧΜΤ𐅄𐅅𐅆𐅇𐅈𐅉𐅊𐅋𐅌𐅍𐅎𐅏𐅏𐅐𐅑��𐅓𐅔𐅕𐅖')
  text_cleaned = re.sub(rf'\[[{greek_numerals}]+\]', '', text_cleaned)
  text_cleaned = re.sub(
      rf'{word_boundary}([{greek_numerals}]+){word_boundary}',
      lambda m: '%s0%s' % (m.group(1), m.group(3)), text_cleaned)
  text_cleaned = re.sub(
      rf'{word_boundary}([{greek_numerals}]+){word_boundary}',
      lambda m: '%s0%s' % (m.group(1), m.group(3)), text_cleaned)

  # Remove extra punctuation
  text_cleaned = re.sub(r'(\s*)[\∶|\⋮|\·|\⁙|\;]+(\s*)', r' ', text_cleaned)

  # Remove all (?)
  text_cleaned = re.sub(r'\s*\(\?\)', r'', text_cleaned)

  # Remove anything between {}
  text_cleaned = re.sub(r'{[^}]*}', r'', text_cleaned)

  # Remove < >, but keep content
  text_cleaned = re.sub(r'<([^>]*)>', r'\1', text_cleaned)

  # Remove latin numbering within brackets [I]
  text_cleaned = re.sub(
      r'\[M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\]\s*$', r'',
      text_cleaned)

  # Lowercase
  text_cleaned = text_cleaned.lower()

  # filter alphabet to replace tonos and h
  text_cleaned = alphabet.filter(text_cleaned)

  # Remove vac, v v. vac vac. vac.? in (), etc
  text_cleaned = re.sub(r'(\d+\s)?\s*v[\w\.\?]*(\s\d+(\.\d+)?)?', '',
                        text_cleaned)

  # Remove parentheses surrounding greek characters
  text_cleaned = re.sub(r'\(([{}]+)\)'.format(''.join(alphabet.alphabet)),
                        r'\1', text_cleaned)

  # Remove any parentheses that has content that is not within the greek alphabet
  text_cleaned = re.sub(r'\([^\)]*\)', r'', text_cleaned)

  # Replace c with σ
  text_cleaned = text_cleaned.replace('ϲ', 'σ')

  # Remove lines with >10% Latin characters
  text_cleaned = '\n'.join([line for line in text_cleaned.splitlines() if len(
      line) and len(re.findall(r'[a-z]', line)) / len(line) < 0.1])

  # Convert short syllables to long ones
  text_cleaned = text_cleaned.replace('⏑', '—')
  text_cleaned = text_cleaned.replace('⏕', '—')
  text_cleaned = text_cleaned.replace('-', '—')

  # Collapse space between dashes (on purpuse double)
  text_cleaned = re.sub(r'—(?:[\s]+—)+',
                        lambda g: re.sub(r'[\s]+', '', g.group(0)),
                        text_cleaned, flags=re.MULTILINE)

  # Replace dots with dashes and c.#
  text_cleaned = re.sub(
      r"(?:\.|․|—)+\s?(?:c\.)?(\d+)(?:(\-|-|—)\d+)?\s?(?:\.|․|—)*",
      lambda g: alphabet.missing * int(g.group(1)),
      text_cleaned, flags=re.MULTILINE)

  # Replace with missing character
  text_cleaned = text_cleaned.replace(u'\u2013', alphabet.missing)
  text_cleaned = text_cleaned.replace(u'\u2014', alphabet.missing)
  text_cleaned = text_cleaned.replace('․', alphabet.missing)

  # PHI #⁷removed automatically because only gr chars

  # Join ][ and []
  text_cleaned = text_cleaned.replace('][', '').replace('[]', '')

  # Keep only alphabet characters
  chars = re.escape(''.join(
      alphabet.alphabet + alphabet.numerals + alphabet.punctuation + [
          alphabet.space, alphabet.missing, alphabet.sog, alphabet.eog]))
  text_cleaned = re.sub(rf'[^{chars}]', ' ', text_cleaned)

  # Replace any digit with 0
  text_cleaned = re.sub(r'\d+', '0', text_cleaned)

  # Merge multiple 0
  text_cleaned = re.sub(r'(\s+0)+', r' 0', text_cleaned)

  # Remove []
  text_cleaned = re.sub(r'\[\s*\]', '', text_cleaned)

  # Remove space before punctuation / merge double punctuation
  chars = re.escape(''.join(alphabet.punctuation + [alphabet.eog]))
  text_cleaned = re.sub(rf'\s+([{chars}])', r'\1', text_cleaned)

  # Remove leading space and punctuation
  text_cleaned = text_cleaned.lstrip(
      ''.join(alphabet.punctuation + [alphabet.space]))

  # Collapse duplicate dots
  punc = re.escape(''.join(alphabet.punctuation))
  text_cleaned = re.sub(rf'([{punc}])+', r'\1', text_cleaned)

  # Collapse spaces
  text_cleaned = re.sub(r'\s+', ' ', text_cleaned).strip()

  return text_cleaned
