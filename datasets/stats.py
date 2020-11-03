import csv
import json
from collections import Counter
from pathlib import Path

if __name__ == '__main__':
    # 291,137 lines in big.tsv
    counter_per_lang = dict()
    print('1gram.sample.tsv')
    with Path('1gram.sample.tsv').open('rt', encoding='utf8', newline='') as f:
        c = csv.reader(f, delimiter='\t')
        for i, row in enumerate(c):
            if (i + 1) % 1000000 == 0:
                print(i + 1)
            assert len(row) == 4, row
            counter_per_lang.setdefault(row[1], Counter())[int(row[3])] += 1
    with Path('1gram.sample.json').open('wt', encoding='utf8') as f:
        json.dump(counter_per_lang, f, indent=4)

    # 847,269 lines in big.tsv
    counter_per_lang = dict()
    print('2gram.sample.tsv')
    with Path('2gram.sample.tsv').open('rt', encoding='utf8', newline='') as f:
        c = csv.reader(f, delimiter='\t')
        for i, row in enumerate(c):
            if (i + 1) % 1000000 == 0:
                print(i + 1)
            assert len(row) == 4, row
            counter_per_lang.setdefault(row[1], Counter())[int(row[3])] += 1
    with Path('2gram.sample.json').open('wt', encoding='utf8') as f:
        json.dump(counter_per_lang, f, indent=4)

    # 1,431,347 lines in big.tsv
    counter_per_lang = dict()
    print('chargram.sample.tsv')
    with Path('chargram.sample.tsv').open('rt', encoding='utf8', newline='') as f:
        c = csv.reader(f, delimiter='\t', quotechar=None)
        for i, row in enumerate(c):
            if (i + 1) % 1000000 == 0:
                print(i + 1)
            assert len(row) == 5, row
            counter_per_lang.setdefault(row[1], Counter())[int(row[4])] += 1
    with Path('chargram.sample.json').open('wt', encoding='utf8') as f:
        json.dump(counter_per_lang, f, indent=4)

    # 124,514,722 lines in big.csv
    counter_per_lang = dict()
    print('MASTER.LINGUISTIC.1GRAM.sample.csv')
    with Path('MASTER.LINGUISTIC.1GRAM.sample.csv').open('rt', encoding='utf8', newline='') as f:
        c = csv.reader(f)
        for i, row in enumerate(c):
            if (i + 1) % 1000000 == 0:
                print(i + 1)
            assert len(row) == 3, row
            counter_per_lang.setdefault(row[0], Counter())[int(row[2])] += 1
    with Path('MASTER.LINGUISTIC.1GRAM.sample.json').open('wt', encoding='utf8') as f:
        json.dump(counter_per_lang, f, indent=4)

    # 687,413,157 lines in big.csv
    counter_per_lang = dict()
    print('MASTER.LINGUISTIC.2GRAM.sample.csv')
    with Path('MASTER.LINGUISTIC.2GRAM.sample.csv').open('rt', encoding='utf8', newline='') as f:
        c = csv.reader(f)
        for i, row in enumerate(c):
            if (i + 1) % 1000000 == 0:
                print(i + 1)
            assert len(row) == 3, row
            counter_per_lang.setdefault(row[0], Counter())[int(row[2])] += 1
    with Path('MASTER.LINGUISTIC.2GRAM.sample.json').open('wt', encoding='utf8') as f:
        json.dump(counter_per_lang, f, indent=4)
