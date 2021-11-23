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


def date_parser_phi(d):
  '''Rules to convert the PHI date strings to a range.'''
  exemptions = {
      # GREEK WORLD
      'Archaic period': '-600 -479',
      'Classical period': '-479 -323',
      'early Classical period': '-480 -400',
      'high Classical period': '-450 -400',
      'late Classical period': '-400 -323',
      'Hellenistic period': '-323 -31',
      'early Hellenistic period': '-323 -250',
      'late Hellenistic period': '-250 -31',

      # HELLENISTIC EMPIRE
      'Seleucid period': '-311 -64',
      'Attalid period': '-330 -30',
      'Antigonid period': '-306 -168',
      'Ptolemaic period': '-332 -31',

      # ROME AND ITALY
      'aet. Rom.': '-200 600',
      'aet. imp.': '-27 284',

      'Roman period': '-200 600',
      'early Roman period': '-200 1',  # ?
      'late Roman period': '250 450',
      'Etruscan period': '-616 -509',
      'Roman Republic period': '-509 -27',
      'late Roman Republic period': '-146 -27',
      'Roman Imperial period': '-27 284',
      'Rom. Imp. period': '-27 284',
      'early Rom. Imp. period': '-27 150',
      'adv. Rom. Imp. period': '-27 150',
      'later Rom. Imp. period': '150 375',
      'late Rom. Imp. period': '150 375',
      'high Rom. Imp. period': '68 235',
      'Christian period': '27 325',
      'late Christian period': '313 476',
      'Byzantine period': '330 1453',
      'Late Antique period': '284 476',
      'late Antiquity': '284 476',

      # ROMAN IMPERIAL DYNASTIES
      'Julio-Claudian period': '-27 68',
      'Augustan period': '-27 14',
      'Tiberian period': '14 37',
      'Claudian period': '41 54',
      'Neronian period': '54 68',
      'Flavian period': '69 96',
      'Vespasianic period': '69 79',
      'Domitianic period': '81 96',
      'Antonine period': '96 192',  # (dynasty not emperor)
      'Trajanic period': '98 117',
      'Hadrianic period': '117 138',
      'Ant. Pius period': '138 161',  # (emperor not dynasty)
      'Severan period': '193 235',
      'Constantinian period': '307 364',
      'Valentinian period': '364 392',
      'Theodosian period': '392 456',
      'Thracian period': '457 476',

      # REIGN
      'reign of Augustus': '-27 14',
      'reign of Tiberius': '14 37',
      'reign of Gaius': '37 41',
      'reign of Claudius': '41 54',
      'reign of Nero': '54 68',
      'reign of Flavius': '69 96',
      'reign of Vespasian': '69 79',
      'reign of Domitian': '81 96',
      'reign of Nerva': '96 98',
      'reign of Trajan': '98 117',
      'reign of Hadrian': '117 138',
      'reign of Ant. Pius': '138 161',
      'reign of Severus': '193 235',
      'reign of Constantine': '307 364',
      'reign of Valentinian': '364 392',
      'reign of Theodosius': '392 456',

      # Other exemptions
      '1st c. BC/1st c. AD': '-100 199',
      '44 BC-267 AD': '-44 267'
  }

  # Remove parenthesis ()
  d = re.sub(r'\([^\)]*\)', r'', d)

  # Remove months
  d = re.sub(
      r'Jan\.|January|Feb\.|February|Mar\.|March|Apr\.|April|May|Jun\.|June|Jul\.|'
      r'July|Aug\.|August|Sept\.|September|Oct\.|October|Nov\.|November|'
      r'Dec\.|December', r'', d)

  # Parse 'circa' from 'ca' or '?'
  circa = False
  circa_words = ['?', 'probably', 'perhaps', 'perh.', 'prob.', 'or']
  if re.search(r'(?:^|\s+)ca(\W|$)', d):
    circa = True
  else:
    for w in circa_words:
      if w in d:
        circa = True
        break

  # Period matching, otherwise parse the date as a date
  if re.search(r'(' + '|'.join(exemptions.keys()) + ')', d, re.IGNORECASE):
    for period, period_date in exemptions.items():
      if re.search(period, d, re.IGNORECASE):
        return period_date, circa
    return None, None

  # Collapse spaces
  d = re.sub(r'\s+', ' ', d).strip()

  # Date matching BC AD
  m = re.search(r'(?:^|\s+)(BC|AD|a\.|p\.)(?:$|\s+|\?)', d, re.IGNORECASE)
  if m:
    # Treat a. as BC
    bc_ad = m.group(1).upper().replace('A.', 'BC')

    # Parse dates xxx(/xx)-xxx(/xx) BC
    m = re.search(
        r'\s?(\d{1,4})(\/\d{1,2})?\s?-\s?(\d{1,4})(\/(\d{1,2}))?\??\s+(BC|AD|a\.|p\.)',
        d, re.IGNORECASE)
    if m:
      min_date = int(m.group(1))
      max_date = int(m.group(3))

      # Pick the upper date margin in case xxx/x e.g. 409/408 BCE
      if m.group(5):
        max_date = int(m.group(3)[:-len(m.group(5))] + m.group(5))

      if bc_ad == 'BC' and min_date >= max_date:
        min_date, max_date = -min_date, -max_date
        return f'{min_date} {max_date}', circa
      elif bc_ad == 'AD' and min_date <= max_date:
        return f'{min_date} {max_date}', circa

    # Parse dates xxx(/xx) BC
    m = re.search(
        r'(\d{1,4})(\/(\d{1,4}))?\??\s+(BC|AD|a\.|p\.)', d, re.IGNORECASE)
    if m:
      min_date = int(m.group(1))
      if m.group(3):
        # Pick the upper date margin xxx/x
        max_date = int(m.group(1)[:-len(m.group(3))] + m.group(3))
      else:
        max_date = min_date

      if bc_ad == 'BC':
        min_date = -min_date
        max_date = -max_date

      # Swap dates if opposite
      if min_date > max_date:
        min_date, max_date = max_date, min_date

      return f'{min_date} {max_date}', circa

    # Parse precise dates e.g. AD 43
    m = re.search(r'^(BC|AD|a\.|p\.) (\d{1,4})\D', d, re.IGNORECASE)
    if m:
      min_date = int(m.group(2))
      if bc_ad == 'BC':
        min_date = -min_date

      if min_date <= max_date:
        return f'{min_date} {max_date}', circa
      else:
        return None, None

    # Parse century spans e.g. 7th/6th c. BC
    early_words = ['early', 'first half', '1st half', 'beginning', 'beg.']
    late_words = ['late', 'second half', '2nd half', 'end']
    mid_words = ['mid', 'mid.', 'mid-']

    regex_words = r'\s?|'.join(early_words + late_words + mid_words) + r'\s?'
    m = re.search(
        r'(((' + regex_words + r')?(\d{1,2})(st|nd|rd|th))'
        r'\s?(/|-|or)\s?)?(' + regex_words + r')?(\d{1,2})(st|nd|rd|th) '
        r'(:?c. )?(BC|AD|a\.)',
        d, re.IGNORECASE)
    if not m:
      return None, None
    else:

      max_date = int(m.group(8))
      if m.group(4):
        min_date = int(m.group(4))
      else:
        min_date = int(m.group(8))

      if bc_ad == 'BC':
        min_date = -(min_date * 100)
        max_date = -(max_date * 100 - 99)
      else:
        min_date = min_date * 100 - 99
        max_date = max_date * 100

      # if early add/remove/match 50 years from that century
      if m.group(3):
        if m.group(3).strip() in early_words:
          max_date -= 50
        elif m.group(3).strip() in late_words:
          min_date += 50

      # If late add/remove/match 50 years from that century
      if m.group(7):
        if m.group(7).strip() in early_words:
          max_date -= 50
        elif m.group(7).strip() in late_words:
          min_date += 50

      # Mid date
      if m.group(3):
        if m.group(3).strip() in mid_words:
          max_date -= 25
          min_date += 25

      if m.group(7):
        if m.group(7).strip() in mid_words:
          max_date -= 25
          min_date += 25

      if min_date <= max_date:
        return f'{min_date} {max_date}', circa
      else:
        return None, None
