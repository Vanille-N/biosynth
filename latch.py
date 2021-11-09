from circuit import *

def latch(*, delay_a, delay_b, imax, start, pulse_a, pulse_b, sigma, use_expstep=False, signals="AB"):
    if use_expstep:
        f = lambda pulse, delay: Input.expstep(
            start=start,
            stop=start + pulse,
            tau_emit=0.5,
            tau_decay=0.5,
            delay=delay,
        )
    else:
        f = lambda pulse, delay: Input.heaviside(
            start=start,
            stop=start + pulse,
            delay=delay,
        )
    fn_a = f(pulse_a, delay_a) if "A" in signals else lambda *_: 0
    fn_b = f(pulse_b, delay_b) if "B" in signals else lambda *_: 0
    a = Input("A", 'grey', fn_a)
    b = Input("B", 'darkgrey', fn_b)
    p = Gate("P: A !| Q", 'cyan', Nor.default(), Timer.default(), a, initial=1)
    q = Gate("Q: B !| P", 'blue', Nor.default(), Timer.default(), b, initial=0)
    p.push_input(q)
    q.push_input(p)
    c = Circuit(
        a, b,
        p, q,
    )
    c.run(imax, sigma)
    return c

pulse = 3
start = 8
tmax = 20
imax = int(tmax / dt)
t = np.linspace(0, tmax, imax)

init_delay_a = 0
init_delay_b = 0
init_sigma = 0

# Create the figure and the line that we will manipulate
fig, ax = plt.subplots()
lines = [plt.plot(t, g.output, lw=3, label=g.name, color=g.color)[0] for g in latch(
    delay_a=init_delay_a,
    delay_b=init_delay_b,
    imax=imax,
    start=start,
    pulse_a=pulse,
    pulse_b=pulse,
    sigma=init_sigma,
).gates]
plt.legend()
ax.set_xlabel('Time [h]')

axcolor = 'lightgoldenrodyellow'
ax.margins(x=0)

# adjust the main plot to make room for the sliders
plt.subplots_adjust(left=0.1, bottom=0.35)

draw_xmin = 0.05
draw_xsize = 0.8
delay_range = 7
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

a_slider = delay_slider(y=0.2, label='A delay [h]', valinit=init_delay_a)
b_slider = delay_slider(y=0.15, label='B delay [h]', valinit=init_delay_b)

def pulse_slider(*, x, label):
    ax = plt.axes([x, 0.085, 0.03, 0.15], facecolor=axcolor)
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

ax = plt.axes([0.9, 0.075, 0.015, 0.15], facecolor=axcolor)
noise_slider = Slider(
        ax=ax,
        label='Noise',
        valmin=0,
        valmax=0.0099,
        valinit=init_sigma,
        orientation='vertical',
    )

use_expstep = False
signals = "AB"
ax_heaviside = plt.axes([0.1, 0.05, 0.1, 0.05])
heaviside_button = Button(ax_heaviside, "Heaviside")
ax_expstep = plt.axes([0.25, 0.05, 0.1, 0.05])
expstep_button = Button(ax_expstep, "ExpStep")
ax_signals = plt.axes([0.40, 0.05, 0.1, 0.05])
signals_button = Button(ax_signals, "Signals")

# The function to be called anytime a slider's value changes
def update(*_):
    sigma = noise_slider.val
    c = latch(
        delay_a=a_slider.val,
        delay_b=b_slider.val,
        imax=imax,
        start=start,
        pulse_a=pulse_a_slider.val,
        pulse_b=pulse_b_slider.val,
        use_expstep=use_expstep,
        signals=signals,
        sigma=sigma,
    )
    for (line, g) in zip(lines, c.gates):
        line.set_ydata(g.output)
    fig.canvas.draw_idle()


def switch_input_type(new_type):
    def f(_):
        global use_expstep
        use_expstep = new_type
        update()
    return f

def toggle_signals(_):
    global signals
    signals = {
        "A":"B",
        "B":"AB",
        "AB":"A",
    }[signals]
    update()

# register the update function with each slider
for slider in [a_slider, b_slider, pulse_b_slider, pulse_a_slider, noise_slider]:
    slider.on_changed(update)
heaviside_button.on_clicked(switch_input_type(False))
expstep_button.on_clicked(switch_input_type(True))
signals_button.on_clicked(toggle_signals)

plt.show()
