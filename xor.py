from circuit import *

def xor(*, delay, imax, start, pulse_a, pulse_b, use_expstep=False):
    if use_expstep:
        f = lambda pulse, delay: expstep_input(
            start=start,
            stop=start + pulse,
            tau_emit=0.5,
            tau_decay=0.5,
            delay=delay,
        )
    else:
        f = lambda pulse, delay: heaviside_input(
            start=start,
            stop=start + pulse,
            delay=delay,
        )
    a = Input("A", 'grey', f(pulse_a, 0))
    b = Input("B", 'darkgrey', f(pulse_b, delay))
    a_eq = Gate("=A", 'green', Same.default(), Timer.default(), a)
    b_eq = Gate("=B", 'green', Same.default(), Timer.default(), b)
    a_b_nor = Gate("A !| B", 'orange', Nor.default(), Timer.default(), a, b)
    a_b_nor_b_nor = Gate("(A !| B) !| B", '', Nor.default(), Timer.default(), a_b_nor, b)
    a_b_nor_a_nor = Gate("(A !| B) !| A", '', Nor.default(), Timer.default(), a_b_nor, a)
    a_b_nor_b_eq_nor = Gate("(A !| B) !| =B", '', Nor.default(), Timer.default(), a_b_nor, b_eq)
    a_b_nor_a_eq_nor = Gate("(A !| B) !| =A", '', Nor.default(), Timer.default(), a_b_nor, a_eq)
    a_b_xor = Gate("A ^ B", 'red', Merge.default(), Timer.default(), a_b_nor_a_nor, a_b_nor_b_nor)
    a_b_eqxor = Gate("A =^ B", 'blue', Merge.default(), Timer.default(), a_b_nor_a_eq_nor, a_b_nor_b_eq_nor)
    c = Circuit(
        a, b,
        a_b_xor,
        a_b_eqxor,
    )
    c.run(imax)
    return c


pulse = 3
start = 10
tmax = 30
imax = int(tmax / dt)
t = np.linspace(0, tmax, imax)

init_delay = 0

# Create the figure and the line that we will manipulate
fig, ax = plt.subplots()
lines = [plt.plot(t, g.output, lw=2, label=g.name, color=g.color)[0] for g in xor(
    delay=init_delay,
    imax=imax,
    start=start,
    pulse_a=pulse,
    pulse_b=pulse,
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

delay_slider = delay_slider(y=0.2, label='A/B delay [h]', valinit=init_delay)


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

pulse_b_slider = pulse_slider(x=0.85, label="B")
pulse_a_slider = pulse_slider(x=0.80, label="A")

use_expstep = False
ax_heaviside = plt.axes([0.05, 0.05, 0.2, 0.05])
heaviside_button = Button(ax_heaviside, "Heaviside")
ax_expstep = plt.axes([0.3, 0.05, 0.2, 0.05])
expstep_button = Button(ax_expstep, "ExpStep")

# The function to be called anytime a slider's value changes
def update(val):
    c = xor(
        delay=delay_slider.val,
        imax=imax,
        start=start,
        pulse_a=pulse_a_slider.val,
        pulse_b=pulse_b_slider.val,
        use_expstep=use_expstep,
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
for slider in [delay_slider, pulse_b_slider, pulse_a_slider]:
    slider.on_changed(update)
heaviside_button.on_clicked(switch_input_type(False))
expstep_button.on_clicked(switch_input_type(True))

plt.show()
