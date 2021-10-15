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


def three_way_and(*, delay_ab, delay_ac, imax, start, pulse_a, pulse_b, pulse_c):
    a = Input("A", lambda t: 1 if start < t < start+pulse_a else 0)
    b = Input("B", lambda t: 1 if start+delay_ab < t < start+pulse_b+delay_ab else 0)
    c = Input("C", lambda t: 1 if start+delay_ac < t < start+pulse_c+delay_ac else 0)
    aeb = Gate("A & B", And.default(), Timer.default(), a, b)
    aebec = Gate("(A & B) & C", And.default(), Timer.default(), aeb, c)
    sc = Gate("=C", Same.default(), Timer.default(), c)
    aebesc = Gate("(A & B) & =C", And.default(), Timer.default(), aeb, sc)
    c = Circuit(a, b, c, aebec, aebesc)
    c.run(imax)
    return c

pulse = 3
start = 5
tmax = 20
imax = int(tmax / dt)
t = np.linspace(0, tmax, imax)

init_delay_ab = 0
init_delay_ac = 0

# Create the figure and the line that we will manipulate
fig, ax = plt.subplots()
lines = [plt.plot(t, g.output, lw=2)[0] for g in three_way_and(
    delay_ab=init_delay_ab,
    delay_ac=init_delay_ac,
    imax=imax,
    start=start,
    pulse_a=pulse,
    pulse_b=pulse,
    pulse_c=pulse).gates]
ax.set_xlabel('Time [s]')

axcolor = 'lightgoldenrodyellow'
ax.margins(x=0)

# adjust the main plot to make room for the sliders
plt.subplots_adjust(left=0.1, bottom=0.25)

draw_xmin = 0.1
draw_xsize = 0.8
delay_range = 4
draw_delaymin = draw_xmin + draw_xsize * (start - delay_range) / tmax
draw_delaymax = draw_xmin + draw_xsize * (start + delay_range) / tmax

# Make a horizontal slider to control the A/B delay
ax_ab = plt.axes([draw_delaymin, 0.15, draw_delaymax-draw_delaymin, 0.03], facecolor=axcolor)
ab_slider = Slider(
    ax=ax_ab,
    label='A/B delay [h]',
    valmin=-delay_range,
    valmax=delay_range,
    valinit=init_delay_ab,
)

# Make a horizontal slider to control the A/C delay
ax_ac = plt.axes([draw_delaymin, 0.1, draw_delaymax-draw_delaymin, 0.03], facecolor=axcolor)
ac_slider = Slider(
    ax=ax_ac,
    label="A/C delay [h]",
    valmin=-delay_range,
    valmax=delay_range,
    valinit=init_delay_ac,
    #orientation="vertical"
)

# Three vertical sliders for pulse duration for A,B,C
ax_pulse_c = plt.axes([0.75, 0.1, 0.03, 0.1], facecolor=axcolor)
pulse_c_slider = Slider(
    ax=ax_pulse_c,
    label="C",
    valmin=1,
    valmax=4,
    valinit=pulse,
    orientation="vertical"
)
ax_pulse_b = plt.axes([0.70, 0.1, 0.03, 0.1], facecolor=axcolor)
pulse_b_slider = Slider(
    ax=ax_pulse_b,
    label="B",
    valmin=1,
    valmax=4,
    valinit=pulse,
    orientation="vertical"
)
ax_pulse_a = plt.axes([0.65, 0.1, 0.03, 0.1], facecolor=axcolor)
pulse_a_slider = Slider(
    ax=ax_pulse_a,
    label="A",
    valmin=1,
    valmax=4,
    valinit=pulse,
    orientation="vertical"
)

# The function to be called anytime a slider's value changes
def update(val):
    c = three_way_and(
        delay_ab=ab_slider.val,
        delay_ac=ac_slider.val,
        imax=imax,
        start=start,
        pulse_a=pulse_a_slider.val,
        pulse_b=pulse_b_slider.val,
        pulse_c=pulse_c_slider.val)
    for (line, g) in zip(lines, c.gates):
        line.set_ydata(g.output)
    fig.canvas.draw_idle()


# register the update function with each slider
ab_slider.on_changed(update)
ac_slider.on_changed(update)
pulse_c_slider.on_changed(update)
pulse_b_slider.on_changed(update)
pulse_a_slider.on_changed(update)

plt.show()
