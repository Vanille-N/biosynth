import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button

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
        # should be a float -> [0,1] function that tells the value
        self.ind = ind
        self.output = [ind(0, 0, dt)]

    def out(self, t):
        while len(self.output) <= t:
            self.output.append(
                self.ind(len(self.output) * dt, self.output[-1], dt))
        return self.output[t]


def heaviside_input(start, stop, delay):
    return lambda t, last, dt: 1 if start+delay < t < stop+delay else 0


def expstep_input(start, stop, tau_emit, tau_decay, delay):
    def f(t, last, dt):
        down = last * dt / tau_decay
        response = start+delay <= t <= stop+delay
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


def three_way_and(*, delay_ab, delay_ac, imax, start, pulse_a, pulse_b, pulse_c, use_expstep=False):
    if use_expstep:
        a = Input("A", expstep_input(start, start+pulse_a, 0.5, 0.5, 0))
        b = Input("B", expstep_input(start, start+pulse_b, 0.5, 0.5, delay_ab))
        c = Input("C", expstep_input(start, start+pulse_c, 0.5, 0.5, delay_ac))
    else:
        a = Input("A", heaviside_input(start, start+pulse_a, 0))
        b = Input("B", heaviside_input(start, start+pulse_b, delay_ab))
        c = Input("C", heaviside_input(start, start+pulse_c, delay_ac))
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
plt.subplots_adjust(left=0.1, bottom=0.35)

draw_xmin = 0.15
draw_xsize = 0.8
delay_range = 4
draw_delaymin = draw_xmin + draw_xsize * (start - delay_range) / tmax
draw_delaymax = draw_xmin + draw_xsize * (start + delay_range) / tmax

# Make a horizontal slider to control the A/B delay
ax_ab = plt.axes([draw_delaymin, 0.2, draw_delaymax -
                 draw_delaymin, 0.03], facecolor=axcolor)
ab_slider = Slider(
    ax=ax_ab,
    label='A/B delay [h]',
    valmin=-delay_range,
    valmax=delay_range,
    valinit=init_delay_ab,
)

# Make a horizontal slider to control the A/C delay
ax_ac = plt.axes([draw_delaymin, 0.15, draw_delaymax -
                 draw_delaymin, 0.03], facecolor=axcolor)
ac_slider = Slider(
    ax=ax_ac,
    label="A/C delay [h]",
    valmin=-delay_range,
    valmax=delay_range,
    valinit=init_delay_ac,
    #orientation="vertical"
)

# Three vertical sliders for pulse duration for A,B,C
ax_pulse_c = plt.axes([0.75, 0.15, 0.03, 0.1], facecolor=axcolor)
pulse_c_slider = Slider(
    ax=ax_pulse_c,
    label="C",
    valmin=1,
    valmax=4,
    valinit=pulse,
    orientation="vertical"
)
ax_pulse_b = plt.axes([0.70, 0.15, 0.03, 0.1], facecolor=axcolor)
pulse_b_slider = Slider(
    ax=ax_pulse_b,
    label="B",
    valmin=1,
    valmax=4,
    valinit=pulse,
    orientation="vertical"
)
ax_pulse_a = plt.axes([0.65, 0.15, 0.03, 0.1], facecolor=axcolor)
pulse_a_slider = Slider(
    ax=ax_pulse_a,
    label="A",
    valmin=1,
    valmax=4,
    valinit=pulse,
    orientation="vertical"
)

use_expstep = False
ax_heaviside = plt.axes([0.05, 0.05, 0.2, 0.05])
heaviside_button = Button(ax_heaviside, "Heaviside")
ax_expstep = plt.axes([0.3, 0.05, 0.2, 0.05])
expstep_button = Button(ax_expstep, "ExpStep")

# The function to be called anytime a slider's value changes
def update(val):
    c = three_way_and(
        delay_ab=ab_slider.val,
        delay_ac=ac_slider.val,
        imax=imax,
        start=start,
        pulse_a=pulse_a_slider.val,
        pulse_b=pulse_b_slider.val,
        pulse_c=pulse_c_slider.val,
        use_expstep=use_expstep)
    for (line, g) in zip(lines, c.gates):
        line.set_ydata(g.output)
    fig.canvas.draw_idle()


def switch_input_type(new_type):
    def f(_):
        global use_expstep
        use_expstep = new_type
        update(True)
    return f

# register the update function with each slider
ab_slider.on_changed(update)
ac_slider.on_changed(update)
pulse_c_slider.on_changed(update)
pulse_b_slider.on_changed(update)
pulse_a_slider.on_changed(update)
heaviside_button.on_clicked(switch_input_type(False))
expstep_button.on_clicked(switch_input_type(True))

plt.show()
