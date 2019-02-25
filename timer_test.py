from threading import Timer

"""
def run(text):
    print(text)

times = [1.0, 2.0, 3.0]
a = ["paper", "scissors", "rock"]

t = [Timer(times[i], run, args=[a[i]]) for i in range(len(a))]

for t_i in t:
    t_i.start()
"""

t = Timer(times, run)

def run():
    print("paper")
    t = Timer(0.5, run)
    t.start()

run()
