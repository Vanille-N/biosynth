from circuit import *

# DNA-binding proteins
class RealNor(Gate):
    def __init__(self, name, color, *inputs):
        super().__init__(name, color, Nor(Cutoff.default()), Timer(emit=36/60,decay=35/60), *inputs)

# CRISPRi
class RealNorCRISPRi(Gate):
    def __init__(self, name, color, *inputs):
        super().__init__(name, color, Nor(Cutoff.default()), Timer(emit=35/60,decay=47/60), *inputs)


def real_nor(*, delay_ab, imax, start, pulse_a, pulse_b, mecanism='protein'):
    f = lambda pulse, delay: heaviside_input(
            start=start,
            stop=start + pulse,
            delay=delay,
        )
    a = Input("A", 'grey', f(pulse_a, 0))
    b = Input("B", 'darkgrey', f(pulse_b, delay_ab))
    if mecanism == 'protein':
        a_b_nor = RealNor("A NOR B", 'red',a,b)
    if mecanism == 'crispri':
        a_b_nor = RealNorCRISPRi("A NOR B", 'red',a,b)
    c = Circuit(
        a, b,
        a_b_nor
    )
    c.run(imax)
    return c

if __name__ == "__main__":
    pulse = 3
    start = 5
    tmax = 20
    imax = int(tmax / dt)
    t = np.linspace(0, tmax, imax)

    init_delay_ab = 0

    # Create the figure and the line that we will manipulate
    fig, ax = plt.subplots()
    lines = [plt.plot(t, g.output, lw=2, label=g.name, color=g.color)[0] for g in real_nor(
        delay_ab=init_delay_ab,
        imax=imax,
        start=start,
        pulse_a=pulse,
        pulse_b=pulse,
        mecanism='protein'
    ).gates]
    plt.legend()
    ax.set_xlabel('Time [h]')

    axcolor = 'lightgoldenrodyellow'
    ax.margins(x=0)
    plt.show()
