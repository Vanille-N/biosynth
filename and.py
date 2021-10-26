from circuit import *

sigma = 0.

def three_way_and(*, delay_ab, delay_ac, imax, start, pulse_a, pulse_b, pulse_c, use_expstep=False):
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
    b = Input("B", 'darkgrey', f(pulse_b, delay_ab))
    c = Input("C", 'lightgray', f(pulse_c, delay_ac))
    a_b_and = Gate("A & B", '', And.default(), Timer.default(), a, b)
    b_c_and = Gate("A & C", '', And.default(), Timer.default(), b, c)
    a_c_and = Gate("A & C", '', And.default(), Timer.default(), a, c)
    a_b_and_c_and = Gate("(A & B) & C", 'red', And.default(), Timer.default(), a_b_and, c)
    a_b_c_and_and = Gate("A & (B & C)", 'orange', And.default(), Timer.default(), a, b_c_and)
    a_c_and_b_and = Gate("B & (A & C)", 'yellow', And.default(), Timer.default(), b, a_c_and)
    a_eq = Gate("=A", '', Same.default(), Timer.default(), a)
    b_eq = Gate("=B", '', Same.default(), Timer.default(), b)
    c_eq = Gate("=C", '', Same.default(), Timer.default(), c)
    a_b_and_c_eq_and = Gate("(A & B) & =C", 'blue', And.default(), Timer.default(), a_b_and, c_eq)
    a_eq_b_c_and_and = Gate("=A & (B & C)", 'green', And.default(), Timer.default(), a_eq, b_c_and)
    a_c_and_b_eq_and = Gate("=B & (A & C)", 'cyan', And.default(), Timer.default(), b_eq, a_c_and)
    c = Circuit(
        a, b, c,
        a_b_and_c_and,
        #a_b_c_and_and,
        #a_c_and_b_and,
        a_b_and_c_eq_and,
        #a_eq_b_c_and_and,
        #a_c_and_b_eq_and,
    )
    global sigma
    c.run(imax,sigma)
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
lines = [plt.plot(t, g.output, lw=2, label=g.name, color=g.color)[0] for g in three_way_and(
    delay_ab=init_delay_ab,
    delay_ac=init_delay_ac,
    imax=imax,
    start=start,
    pulse_a=pulse,
    pulse_b=pulse,
    pulse_c=pulse
).gates]
plt.legend()
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

ab_slider = delay_slider(y=0.2, label='A/B delay [h]', valinit=init_delay_ab)
ac_slider = delay_slider(y=0.15, label='A/C delay [h]', valinit=init_delay_ac)


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

pulse_c_slider = pulse_slider(x=0.75, label="C")
pulse_b_slider = pulse_slider(x=0.70, label="B")
pulse_a_slider = pulse_slider(x=0.65, label="A")

ax = plt.axes([0.8, 0.075, 0.03, 0.2], facecolor=axcolor)
noise_slider = Slider(
        ax=ax,
        label='Noise',
        valmin=0,
        valmax=0.0099,
        valinit=0,
        orientation='vertical',
    )



use_expstep = False
ax_heaviside = plt.axes([0.05, 0.05, 0.2, 0.05])
heaviside_button = Button(ax_heaviside, "Heaviside")
ax_expstep = plt.axes([0.3, 0.05, 0.2, 0.05])
expstep_button = Button(ax_expstep, "ExpStep")

# The function to be called anytime a slider's value changes
def update(val):
    global sigma
    sigma = noise_slider.val
    print(noise_slider.val)
    c = three_way_and(
        delay_ab=ab_slider.val,
        delay_ac=ac_slider.val,
        imax=imax,
        start=start,
        pulse_a=pulse_a_slider.val,
        pulse_b=pulse_b_slider.val,
        pulse_c=pulse_c_slider.val,
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
for slider in [ab_slider, ac_slider, pulse_c_slider, pulse_b_slider, pulse_a_slider,noise_slider]:
    slider.on_changed(update)
heaviside_button.on_clicked(switch_input_type(False))
expstep_button.on_clicked(switch_input_type(True))

plt.show()
