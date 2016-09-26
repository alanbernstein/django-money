#!/usr/local/bin/python
import sys
import json
import matplotlib.pyplot as plt
from dateparser import parse


with open(sys.argv[1]) as f:
    data = json.load(f)

x = [parse(z) for z in data['x']]
y1 = [float(z) for z in data['heb']]
y2 = [float(z) for z in data['whole foods']]

plt.plot(x, y1, 'r')
plt.plot(x, y2, 'b')
plt.show()
