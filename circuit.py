import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button

dt = 0.01
sigma = 0.003

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

    def response(self, *args):
        return self.cutoff.steady_state(self.activation(*args))

    @classmethod
    def default(cls):
        return cls(Cutoff.default())

class Not(Combinator):
    def activation(self, x):
        return x

class Same(Combinator):
    def activation(self, x):
        return 1 - x

class And(Combinator):
    def activation(self, x, y):
        return 1 - x * y

class Or(Combinator):
    def activation(self, x, y):
        return (1-x) * (1-y)

class Nor(Combinator):
    def activation(self, x, y):
        return 1 - (1-x) * (1-y)

class Nand(Combinator):
    def activation(self, x, y):
        return x * y

class Merge(Combinator):
    def response(self, x, y):
        return x + y

# instanciation of a logical gate takes
# - the gate description
# - time variation parameters
# - the 
class Gate:
    def __init__(self, name, color, combinator, timer, *inputs):
        self.name = name
        self.color = color
        self.combinator = combinator
        self.timer = timer
        self.inputs = list(inputs)
        self.output = [0]

    def push_input(self, i):
        self.inputs.append(i)

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
            ins = [i.out(t2 - 1) for i in self.inputs]
            response = self.combinator.response(*ins)
            down = self.output[t2-1] * dt / self.timer.tau_decay
            up = response * dt / self.timer.tau_emit
            noise = np.random.normal(0,sigma)
            self.output.append(max(0.,self.output[t2-1] + up - down + noise))
        return self.output[t]

class Input:
    def __init__(self, name, color, ind):
        self.name = name
        self.color = color
        # should be a float -> [0,1] function that tells the value
        self.ind = ind
        self.output = [ind(0, 0, dt)]

    def out(self, t):
        while len(self.output) <= t:
            self.output.append(
                self.ind(len(self.output) * dt, self.output[-1], dt))
        return self.output[t]


def heaviside_input(*, start, stop, delay):
    def f(t, last, dt):
        if start + delay < t < stop + delay:
            return 1
        else:
            return 0
    return f

def expstep_input(*, start, stop, tau_emit, tau_decay, delay):
    def f(t, last, dt):
        down = last * dt / tau_decay
        response = start + delay <= t <= stop + delay
        up = response * dt / tau_emit
        return last + up - down
    return f


class Circuit:
    def __init__(self, *gates):
        self.gates = gates

    def run(self, imax):
        for t in range(imax):
            for g in self.gates:
                g.out(t)

    def plot(self, tmax):
        imax = int(tmax / dt)
        self.run(imax)
        for g in self.gates:
            plt.plot([i*dt for i in range(imax)], g.output, label=g.name)
        plt.legend()
        plt.show()

