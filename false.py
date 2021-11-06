from circuit import *

def false(*, imax, start, pulse, sigma, use_expstep=False):
    if use_expstep:
        f = lambda pulse: expstep_input(
            start=start,
            stop=start + pulse,
            tau_emit=0.5,
            tau_decay=0.5,
            delay=0,
        )
    else:
        f = lambda pulse: heaviside_input(
            start=start,
            stop=start + pulse,
            delay=0,
        )
    a = Input("A", 'grey', f(pulse))
    a_eq = Gate("=A", 'green', Same.default(), Timer.default(), a)
    a_not = Gate("!A", 'orange', Not.default(), Timer.default(), a)
    false = Gate("A & !A", 'red', And.default(), Timer.default(), a, a_not)
    true = Gate("A | !A", 'red', Or.default(), Timer.default(), a, a_not)
    false_eq = Gate("=A & !A", 'blue', And.default(), Timer.default(), a_eq, a_not)
    true_eq = Gate("=A | !A", 'blue', Or.default(), Timer.default(), a_eq, a_not)
    c = Circuit(
        a,
        false, false_eq,
        true, true_eq,
    )
    c.run(imax, sigma)
    return c


pulse = 3
start = 10
tmax = 30
imax = int(tmax / dt)
t = np.linspace(0, tmax, imax)

init_delay = 0
init_sigma = 0

# Create the figure and the line that we will manipulate
fig, ax = plt.subplots()
lines = [plt.plot(t, g.output, lw=2, label=g.name, color=g.color)[0] for g in false(
    imax=imax,
    start=start,
    pulse=pulse,
    sigma=init_sigma,
).gates]
plt.legend()
ax.set_xlabel('Time [h]')

axcolor = 'lightgoldenrodyellow'
ax.margins(x=0)

# adjust the main plot to make room for the sliders
plt.subplots_adjust(left=0.1, bottom=0.35)

draw_xmin = 0.15
draw_xsize = 0.8
delay_range = 8
draw_delaymin = draw_xmin + draw_xsize * (start - delay_range) / tmax
draw_delaymax = draw_xmin + draw_xsize * (start + delay_range) / tmax

def delay_slider(*, y, label, valinit):
    ax = plt.axes(
        [draw_delaymin, y, draw_delaymax - draw_delaymin, 0.03],
        facecolor=axcolor,
    )
    return Slider(
        ax=ax,
        label=label,
        valmin=-delay_range,
        valmax=delay_range,
        valinit=valinit,
    )

def pulse_slider(*, x, label):
    ax = plt.axes([x, 0.075, 0.03, 0.2], facecolor=axcolor)
    return Slider(
        ax=ax,
        label=label,
        valmin=1,
        valmax=8,
        valinit=pulse,
        orientation='vertical',
    )

pulse_slider = pulse_slider(x=0.80, label="pulse")

ax = plt.axes([0.9, 0.075, 0.03, 0.2], facecolor=axcolor)
noise_slider = Slider(
        ax=ax,
        label='Noise',
        valmin=0,
        valmax=0.0099,
        valinit=init_sigma,
        orientation='vertical',
    )

use_expstep = False
ax_heaviside = plt.axes([0.05, 0.05, 0.2, 0.05])
heaviside_button = Button(ax_heaviside, "Heaviside")
ax_expstep = plt.axes([0.3, 0.05, 0.2, 0.05])
expstep_button = Button(ax_expstep, "ExpStep")

# The function to be called anytime a slider's value changes
def update(val):
    c = false(
        imax=imax,
        start=start,
        pulse=pulse_slider.val,
        use_expstep=use_expstep,
        sigma=noise_slider.val,
    )
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
pulse_slider.on_changed(update)
noise_slider.on_changed(update)
heaviside_button.on_clicked(switch_input_type(False))
expstep_button.on_clicked(switch_input_type(True))

plt.show()
