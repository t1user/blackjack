#!/usr/bin/python3

import os
import shutil

os.chdir('Cards')
print(os.getcwd())

files = os.listdir()

suits = {'spades': 's', 'hearts': 'h', 'diamonds': 'd', 'clubs': 'c'}
ranks = {'jack': 'j', 'queen': 'q', 'king': 'k', 'ace': 'a'}
for x in range(10):
	ranks[str(x+1)]=str(x+1)
suits1 = dict(suits)
for s in suits.keys():
	suits1[s+'2'] = suits[s]
#print(suits1)

count = 0
for f in files:
	text = f.split('.')
	item = text[0].split('_')
	element = [ranks[item[0]], suits1[item[2]]]
	filename = '_'.join(element)
	filename += '.png'
	shutil.move(f,filename)
	print(f, ' => ', filename)
	count += 1
print()
print(count, 'files renamed')
	#print(f)

