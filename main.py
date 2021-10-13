import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

dt = 0.01

# parametrized S-shaped response
class Cutoff:
    def __init__(self, *, ymax, ymin, k, n):
        self.ymax = ymax
        self.ymin = ymin
        self.k = k
        self.n = n

    def default():
        return Cutoff(ymax=1, ymin=0, k=0.3, n=4.7)

    def steady_state(self, x):
        return self.ymin + (self.ymax - self.ymin) / (1 + (x / self.k) ** self.n)


# non-instantaneous processes
class Timer:
    def __init__(self, *, emit, decay):
        self.tau_emit = emit
        self.tau_decay = decay

    def default():
        return Timer(emit=1, decay=1)

# a combinator is any logical gate
class Combinator:
    def __init__(self, cutoff):
        self.cutoff = cutoff

class Not(Combinator):
    def response(self, x):
        return self.cutoff.steady_state(x)

    def default():
        return Not(Cutoff.default())

class Same(Combinator):
    def response(self, x):
        return self.cutoff.steady_state(1 - x)

    def default():
        return Same(Cutoff.default())

class And(Combinator):
    def response(self, x, y):
        return self.cutoff.steady_state(1 - x * y)

    def default():
        return And(Cutoff.default())

class Or(Combinator):
    def response(self, x, y):
        return self.cutoff.steady_state((1-x) * (1-y))

    def default():
        return Or(Cutoff.default())

class Nor(Combinator):
    def response(self, x, y):
        return self.cutoff.steady_state(1 - (1-x) * (1-y))

    def default():
        return Nor(Cutoff.default())

class Nand(Combinator):
    def response(self, x, y):
        return self.cutoff.steady_state(x * y)

    def default():
        return Nand(Cutoff.default())

# instanciation of a logical gate takes
# - the gate description
# - time variation parameters
# - the 
class Gate:
    def __init__(self, name, combinator, timer, *inputs):
        self.name = name
        self.combinator = combinator
        self.timer = timer
        self.inputs = inputs
        self.output = [0]

    def plot_static(self, xrange, yrange):
        fig = plt.figure()
        ax = plt.axes(projection='3d')
        x = np.linspace(*xrange, 100)
        y = np.linspace(*yrange, 100)
        X, Y = np.meshgrid(x, y)
        Z = self.combinator.response(X, Y)
        ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap='viridis', edgecolor='none')
        plt.show()

    def out(self, t):
        while len(self.output) <= t:
            t2 = len(self.output)
            ins = [i.out(t2) for i in self.inputs]
            response = self.combinator.response(*ins)
            down = self.output[t2-1] * dt / self.timer.tau_decay
            up = response * dt / self.timer.tau_emit
            self.output.append(self.output[t2-1] + up - down)
        return self.output[t]

class Input:
    def __init__(self, name, ind):
        self.name = name
        self.ind = ind # should be a float -> [0,1] function that tells the value
        self.output = [ind(0)]

    def out(self, t):
        while len(self.output) <= t:
            self.output.append(self.ind(len(self.output) * dt))
        return self.output[t]


class Circuit:
    def __init__(self, *gates):
        self.gates = gates

    def run(self, tmax):
        imax = int(tmax / dt)
        for t in range(imax):
            for g in self.gates:
                g.out(t)
        for g in self.gates:
            plt.plot([i*dt for i in range(imax)], g.output, label=g.name)
        plt.legend()
        plt.show()


pulse = 3
start = 3
delay_ab = 0
delay_ac = 2
a = Input("A", lambda t: 1 if start < t < start+pulse else 0)
b = Input("B", lambda t: 1 if start+delay_ab < t < start+pulse+delay_ab else 0)
c = Input("C", lambda t: 1 if start+delay_ac < t < start+pulse+delay_ac else 0)
aeb = Gate("A & B", And(Cutoff()), Timer(), a, b)
aebec = Gate("(A & B) & C", And(Cutoff()), Timer(), aeb, c)
sc = Gate("=C", Same(Cutoff()), Timer(), c)
aebesc = Gate("(A & B) & =C", And(Cutoff()), Timer(), aeb, sc)
c = Circuit(a, b, c, aebec, aebesc)
c.run(15)

