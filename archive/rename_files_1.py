#!/usr/bin/python3

import os
import shutil

os.chdir('Cards')
print(os.getcwd())

files = os.listdir()

count = 0
for f in files:
	filename = f + '.png'
	shutil.move(f,filename)
	print(f, ' => ', filename)
	count += 1
print()
print(count, 'files renamed')
	#print(f)

