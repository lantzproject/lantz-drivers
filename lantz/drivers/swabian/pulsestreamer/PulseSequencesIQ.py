import numpy as np
import pandas as pd
from lantz.driver import Driver
from lantz.drivers.swabian.pulsestreamer.lib.pulse_streamer_grpc import PulseStreamer
from lantz import Q_
from spyre.widgets.rangespace import RangeDict
from lantz import Action, Feat, DictFeat, ureg


class Pulses(Driver):
    default_digi_dict = {"laser": "ch0", "offr_laser": "ch1", "EOM": "ch4", "CTR": "ch5", "switch": "ch6",
                         "gate": "ch7", "": None}
    default_digi_dict = {"laser": 0, "offr_laser": 1, "EOM": 4, "CTR": 5, "switch": 6, "gate": 7, "": None}
    rev_dict = {0: "laser", 1: "offr_laser", 4: "EOM", 5: "CTR", 6: "switch", 7: "gate", 8: "I", 9: "Q"}

    def __init__(self, channel_dict=default_digi_dict, laser_time=150 * Q_(1, "us"), readout_time=150 * Q_(1, "us"),
                 buf_after_init=450 * Q_(1, "us"), buf_after_readout=2 * Q_(1, "us"),
                 polarize_time=900 * Q_(1, "us"), settle=150 * Q_(1, "us"), reset=100 * Q_(1, "ns"), IQ=[0.5, 0],
                 ip="192.168.1.111"):
        """
        :param channel_dict: Dictionary of which channels correspond to which instr controls
        :param laser_time: Laser time in us
        :param CTR: When False CTR0 When True CTR1
        :param readout_time: Readout time in us
        :param buf_after_init: buf after laser turns off in us to allow the population to thermalize
        :param buf_after_readout: buf between the longest pulse and the readout in us to prevent laser to leak in
        :param IQ: IQ vector that rotates the spin
        """
        super().__init__()
        self.channel_dict = channel_dict
        self._reverse_dict = {0: "laser", 1: "offr_laser", 4: "EOM", 5: "CTR", 6: "switch", 7: "gate", 8: "I",
                              9: "Q"}  # rev_dict
        self.laser_time = int(round(laser_time.to("ns").magnitude))
        self.readout_time = int(round(readout_time.to("ns").magnitude))
        self.buf_after_init = int(round(buf_after_init.to("ns").magnitude))
        self.buf_after_readout = int(round(buf_after_readout.to("ns").magnitude))
        self.polarize_time = int(round(polarize_time.to("ns").magnitude))
        self.settle = int(round(settle.to("ns").magnitude))
        self.reset = int(round(reset.to("ns").magnitude))
        self._normalize_IQ(IQ)
        self.Pulser = PulseStreamer(ip)
        self.latest_streamed = pd.DataFrame({})

    @Feat()
    def has_sequence(self):
        """
        Has Sequence
        """
        return self.Pulser.hasSequence()

    def stream(self, seq):
        self.latest_streamed = self.convert_sequence(seq)
        self.Pulser.stream(seq)

    def _normalize_IQ(self, IQ):
        self.IQ = IQ / (2 * np.linalg.norm(IQ))

    def convert_sequence(self, seqs):
        # 0-7 are the 8 digital channels
        # 8-9 are the 2 analog channels
        data = {}
        time = -0.01
        for seq in seqs:
            col = np.zeros(10)
            col[seq[1]] = 1
            col[8] = seq[2]
            col[9] = seq[3]
            init_time = time + 0.01
            data[init_time] = col
            time = time + seq[0]
            # data[prev_time_stamp + 0.01] = col
            data[time] = col
            # prev_time_stamp = seq[0]
        dft = pd.DataFrame(data)
        df = dft.T
        sub_df = df[list(self._reverse_dict.keys())]
        fin = sub_df.rename(columns=self._reverse_dict)
        return fin

    def Transient_Measure(self):
        excitation = \
            [(self.laser_time, [self.channel_dict["laser"]], *self.IQ)]
        bg_decay = \
            [(self.buf_after_init, [], *self.IQ)]
        readout = \
            [(self.readout_time, [self.channel_dict["gate"]], *self.IQ)]
        buf = \
            [(self.buf_after_readout, [], *self.IQ)]
        return excitation + bg_decay + readout + buf

    def CODMR(self):
        excitation = \
            [(self.laser_time, [self.channel_dict["laser"], self.channel_dict["switch"]], *self.IQ)]
        bg_decay = \
            [(self.buf_after_init, [self.channel_dict["switch"]], *self.IQ)]
        readout = \
            [(self.readout_time, [self.channel_dict["switch"], self.channel_dict["gate"]], *self.IQ)]
        buf = \
            [(self.buf_after_readout, [self.channel_dict["switch"]], *self.IQ)]
        return excitation + bg_decay + readout + buf

    def EOM(self):
        excitation = \
            [(self.laser_time, [self.channel_dict["laser"], self.channel_dict["switch"], self.channel_dict["EOM"]],
              *self.IQ)]
        bg_decay = \
            [(self.buf_after_init, [self.channel_dict["switch"]], *self.IQ)]
        readout = \
            [(self.readout_time, [self.channel_dict["switch"], self.channel_dict["gate"]], *self.IQ)]
        buf = \
            [(self.buf_after_readout, [self.channel_dict["switch"]], *self.IQ)]
        return excitation + bg_decay + readout + buf

    def MW_L_EOM(self):
        excitation = \
            [(self.laser_time, [self.channel_dict["laser"], self.channel_dict["switch"], self.channel_dict["EOM"]],
              *self.IQ)]
        bg_decay = \
            [(self.buf_after_init, [self.channel_dict["switch"]], *[0, 0])]
        readout = \
            [(self.readout_time, [self.channel_dict["gate"]], *[0, 0])]
        buf = \
            [(self.buf_after_readout, [], *[0, 0])]
        L_excitation = \
            [(self.laser_time, [self.channel_dict["laser"], self.channel_dict["EOM"]], *[0, 0])]
        L_bg_decay = \
            [(self.buf_after_init, [self.channel_dict["switch"]], *self.IQ)]
        L_readout = \
            [(self.readout_time, [self.channel_dict["switch"], self.channel_dict["gate"], self.channel_dict["CTR"]],
              *self.IQ)]
        L_buf = \
            [(self.buf_after_readout, [self.channel_dict["switch"]], *self.IQ)]
        return excitation + bg_decay + readout + buf + L_excitation + L_bg_decay + L_readout + L_buf

    def L_CODMR(self, measure=0):
        s_excitation = \
            [(self.laser_time, [self.channel_dict["laser"], self.channel_dict["switch"]], *self.IQ)]
        s_bg_decay = \
            [(self.buf_after_init, [], *self.IQ)]
        s_readout = \
            [(self.readout_time, [self.channel_dict["gate"]], *self.IQ)]
        s_buf = \
            [(self.buf_after_readout, [], *self.IQ)]
        s = s_excitation + s_bg_decay + s_readout + s_buf
        m_excitation = \
            [(self.laser_time, [self.channel_dict["laser"]], *self.IQ)]
        m_bg_decay = \
            [(self.buf_after_init, [], *self.IQ)]
        m_readout = \
            [(self.readout_time, [self.channel_dict["gate"]], *self.IQ)]
        m_buf = \
            [(self.buf_after_readout, [], *self.IQ)]
        m = m_excitation + m_bg_decay + m_readout + m_buf
        b_excitation = \
            [(self.laser_time, [self.channel_dict["CTR"], self.channel_dict["laser"]], *self.IQ)]
        b_bg_decay = \
            [(self.buf_after_init, [self.channel_dict["CTR"]], *self.IQ)]
        b_readout = \
            [(self.readout_time, [self.channel_dict["CTR"], self.channel_dict["gate"]], *self.IQ)]
        b_buf = \
            [(self.buf_after_readout, [self.channel_dict["CTR"]], *self.IQ)]
        b = b_excitation + b_bg_decay + b_readout + b_buf
        return s + m * measure + b

    def Rabi(self, params):
        longest_time = int(round(params["stop"].to("ns").magnitude))

        def single_rabi(mw_on):
            wait = longest_time - mw_on + self.buf_after_readout
            excitation = \
                [(self.laser_time, [self.channel_dict["laser"]], *self.IQ)]
            bg_decay = \
                [(self.buf_after_init, [], *self.IQ)]
            readout = \
                [(self.readout_time, [self.channel_dict["gate"]], *self.IQ)]
            rabi = \
                [(mw_on, [self.channel_dict["switch"]], *self.IQ)]
            wait = \
                [(wait, [], *self.IQ)]
            return excitation + bg_decay + readout + rabi + wait

        seqs = [single_rabi(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
        return seqs

    def Resetting_Rabi(self, params):
        longest_time = int(round(params["stop"].to("ns").magnitude))

        def single_rabi(mw_on):
            # wait = self.reset + self.polarize_time + self.buf_after_init * 2 + self.settle + longest_time + self.laser_time + self.readout_time - mw_on
            wait = longest_time - mw_on + self.buf_after_readout
            reset = \
                [(self.reset, [self.channel_dict["offr_laser"]], *self.IQ)]
            polarize = \
                [(self.polarize_time, [self.channel_dict["laser"]], *self.IQ)]
            bg_decay = \
                [(self.buf_after_init, [], *self.IQ)]
            background = \
                [(self.settle, [self.channel_dict["gate"], self.channel_dict["CTR"]], *self.IQ)]
            rabi = \
                [(mw_on, [self.channel_dict["switch"]], *self.IQ)]
            probe = \
                [(self.laser_time, [self.channel_dict["laser"]], *self.IQ)]
            bg_decay = \
                [(self.buf_after_init, [], *self.IQ)]
            readout = \
                [(self.readout_time, [self.channel_dict["gate"]], *self.IQ)]
            wait = \
                [(wait, [], *self.IQ)]

            return reset + polarize + bg_decay + background + rabi + probe + bg_decay + readout + wait

        seqs = [single_rabi(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
        return seqs

    def Resetting_L_Rabi(self, params):
        longest_time = int(round(params["stop"].to("ns").magnitude))

        def single_rabi(mw_on):
            # wait = self.reset + self.polarize_time + self.buf_after_init * 2 + self.settle + longest_time + self.laser_time + self.readout_time - mw_on
            wait = longest_time - mw_on + self.buf_after_readout
            reset = \
                [(self.reset, [self.channel_dict["offr_laser"]], *self.IQ)]
            polarize = \
                [(self.polarize_time, [self.channel_dict["laser"]], *self.IQ)]
            # bg_decay = \
            #     [(self.buf_after_init, [], *self.IQ)]
            background = \
                [(self.settle, [], *self.IQ)]
            rabi = \
                [(mw_on, [self.channel_dict["switch"]], *self.IQ)]
            probe = \
                [(self.laser_time, [self.channel_dict["laser"]], *self.IQ)]
            bg_decay = \
                [(self.buf_after_init, [], *self.IQ)]
            readout = \
                [(self.readout_time, [self.channel_dict["gate"]], *self.IQ)]
            # Lockin Part
            L_rabi = \
                [(mw_on, [], *self.IQ)]
            L_readout = \
                [(self.readout_time, [self.channel_dict["gate"], self.channel_dict["CTR"]], *self.IQ)]
            wait = \
                [(wait, [], *self.IQ)]

            return reset + polarize + bg_decay + background + rabi + wait + probe + bg_decay + readout + \
                   reset + polarize + bg_decay + background + L_rabi + wait + probe + bg_decay + L_readout

        seqs = [single_rabi(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
        return seqs

    def T2(self, params, pi):
        longest_time = int(round(params["stop"].to("ns").magnitude))
        pi_ns = int(round(pi.to("ns").magnitude))

        def single_T2(tau):
            # wait = self.reset + self.polarize_time + self.buf_after_init * 2 + self.settle + longest_time + self.laser_time + self.readout_time - mw_on
            wait = longest_time - tau
            excitation = \
                [(self.laser_time, [self.channel_dict["laser"]], *self.IQ)]
            bg_decay = \
                [(self.buf_after_init, [], *self.IQ)]
            readout = \
                [(self.readout_time, [self.channel_dict["gate"]], *self.IQ)]
            first_pi2 = \
                [(pi_ns // 2, [self.channel_dict["switch"]], *self.IQ)]
            dephase = \
                [(tau // 2, [], *self.IQ)]
            flip = \
                [(pi_ns, [self.channel_dict["switch"]], *self.IQ)]
            rephase = \
                [(tau // 2, [], *self.IQ)]
            second_pi2 = \
                [(pi_ns // 2, [self.channel_dict["switch"]], *self.IQ)]
            wait = \
                [(wait, [], *self.IQ)]
            return excitation + bg_decay + readout + first_pi2 + dephase + flip + rephase + second_pi2 + wait

        seqs = [single_T2(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
        return seqs

    def Resetting_T2(self, params, pi):
        longest_time = int(round(params["stop"].to("ns").magnitude))
        pi_ns = int(round(pi.to("ns").magnitude))

        def single_T2(tau):
            # wait = self.reset + self.polarize_time + self.buf_after_init * 2 + self.settle + longest_time + self.laser_time + self.readout_time - mw_on
            wait = longest_time - tau + self.buf_after_readout
            reset = \
                [(self.reset, [self.channel_dict["offr_laser"]], *self.IQ)]
            polarize = \
                [(self.polarize_time, [self.channel_dict["laser"]], *self.IQ)]
            background = \
                [(self.settle, [self.channel_dict["gate"], self.channel_dict["CTR"]], *self.IQ)]
            first_pi2 = \
                [(pi_ns // 2, [self.channel_dict["switch"]], *self.IQ)]
            dephase = \
                [(tau // 2, [], *self.IQ)]
            flip = \
                [(pi_ns, [self.channel_dict["switch"]], *self.IQ)]
            rephase = \
                [(tau // 2, [], *self.IQ)]
            second_pi2 = \
                [(pi_ns // 2, [self.channel_dict["switch"]], *self.IQ)]
            probe = \
                [(self.laser_time, [self.channel_dict["laser"]], *self.IQ)]
            bg_decay = \
                [(self.buf_after_init, [], *self.IQ)]
            readout = \
                [(self.readout_time, [self.channel_dict["gate"]], *self.IQ)]
            wait = \
                [(wait, [], *self.IQ)]

            return reset + polarize + bg_decay + background + first_pi2 + dephase + flip + rephase + second_pi2 + probe + bg_decay + readout + wait

        seqs = [single_T2(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
        return seqs

    def Resetting_L_T2(self, params, pi, style=[[-1, 0], [1, 0], [1, 0]]):
        longest_time = int(round(params["stop"].to("ns").magnitude))
        pi_ns = int(round(pi.to("ns").magnitude))
        if style[0] == [0, 0]:
            f_pi2 = [0, 0]
            first_pi2gate = []
        else:
            f_pi2 = style[0] / (2 * np.linalg.norm(style[0]))
            first_pi2gate = [self.channel_dict["switch"]]
        if style[1] == [0, 0]:
            L_pi = [0, 0]
            pigate = []
        else:
            L_pi = style[1] / (2 * np.linalg.norm(style[1]))
            pigate = [self.channel_dict["switch"]]
        if style[2] == [0, 0]:
            s_pi2 = [0, 0]
            second_pi2gate = []
        else:
            s_pi2 = style[2] / (2 * np.linalg.norm(style[2]))
            second_pi2gate = [self.channel_dict["switch"]]

        def single_T2(tau):
            # wait = self.reset + self.polarize_time + self.buf_after_init * 2 + self.settle + longest_time + self.laser_time + self.readout_time - mw_on
            wait = longest_time - tau + self.buf_after_readout
            reset = \
                [(self.reset, [self.channel_dict["offr_laser"]], *self.IQ)]
            polarize = \
                [(self.polarize_time, [self.channel_dict["laser"]], *self.IQ)]
            background = \
                [(self.settle, [], *self.IQ)]
            first_pi2 = \
                [(pi_ns // 2, [self.channel_dict["switch"]], *self.IQ)]
            dephase = \
                [(tau // 2, [], *self.IQ)]
            flip = \
                [(pi_ns, [self.channel_dict["switch"]], *self.IQ)]
            rephase = \
                [(tau // 2, [], *self.IQ)]
            second_pi2 = \
                [(pi_ns // 2, [self.channel_dict["switch"]], *self.IQ)]
            probe = \
                [(self.laser_time, [self.channel_dict["laser"]], *self.IQ)]
            bg_decay = \
                [(self.buf_after_init, [], *self.IQ)]
            readout = \
                [(self.readout_time, [self.channel_dict["gate"]], *self.IQ)]
            # Lockin Part
            L_background = \
                [(self.settle, [], *f_pi2)]
            L_first_pi2 = \
                [(pi_ns // 2, first_pi2gate, *f_pi2)]
            L_dephase = \
                [(tau // 2, [], *L_pi)]
            L_flip = \
                [(pi_ns, pigate, *L_pi)]
            L_rephase = \
                [(tau // 2, [], *s_pi2)]
            L_second_pi2 = \
                [(pi_ns // 2, second_pi2gate, *s_pi2)]
            L_readout = \
                [(self.readout_time, [self.channel_dict["gate"], self.channel_dict["CTR"]], *self.IQ)]
            wait = \
                [(wait, [], *self.IQ)]

            return reset + polarize + background + first_pi2 + dephase + flip + rephase + second_pi2 + wait + probe + bg_decay + readout + \
                   reset + polarize + L_background + L_first_pi2 + L_dephase + L_flip + L_rephase + L_second_pi2 + wait + probe + bg_decay + L_readout

        seqs = [single_T2(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
        return seqs

    def Resetting_L_CPMG(self, params, pi, N):
        longest_time = int(round(params["stop"].to("ns").magnitude))
        pi_ns = int(round(pi.to("ns").magnitude))

        def CPMG_core(tau, N, IQ=[1, 0]):
            L_pi2_IQ = IQ / (2 * np.linalg.norm(IQ))
            L_pi2 = \
                [(pi_ns // 2, [self.channel_dict["switch"]], *L_pi2_IQ)]
            pi2 = \
                [(pi_ns // 2, [self.channel_dict["switch"]], *self.IQ)]
            wait_pi2 = \
                [(tau // (2 * N), [], *self.IQ)]
            pi = [(pi_ns, [self.channel_dict["switch"]], *self.IQ)]
            return L_pi2 + N * (wait_pi2 + pi + wait_pi2) + pi2

        def single_T2(tau):
            # wait = self.reset + self.polarize_time + self.buf_after_init * 2 + self.settle + longest_time + self.laser_time + self.readout_time - mw_on
            wait = longest_time - tau + self.buf_after_readout
            reset = \
                [(self.reset, [self.channel_dict["offr_laser"]], *self.IQ)]
            polarize = \
                [(self.polarize_time, [self.channel_dict["laser"]], *self.IQ)]
            background = \
                [(self.settle, [], *self.IQ)]
            CPMG_Core = CPMG_core(tau, N=N, IQ=[1, 0])
            probe = \
                [(self.laser_time, [self.channel_dict["laser"]], *self.IQ)]
            bg_decay = \
                [(self.buf_after_init, [], *self.IQ)]
            readout = \
                [(self.readout_time, [self.channel_dict["gate"]], *self.IQ)]
            # Lockin Part
            L_background = \
                [(self.settle, [], -0.5, 0)]
            L_CPMG_Core = CPMG_core(tau, N=N, IQ=[-1, 0])
            L_readout = \
                [(self.readout_time, [self.channel_dict["gate"], self.channel_dict["CTR"]], *self.IQ)]
            wait = \
                [(wait, [], *self.IQ)]

            return reset + polarize + background + CPMG_Core + wait + probe + bg_decay + readout + \
                   reset + polarize + L_background + L_CPMG_Core + wait + probe + bg_decay + L_readout

        seqs = [single_T2(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
        return seqs

    def Resetting_L_T1(self, params, pi):
        longest_time = int(round(params["stop"].to("ns").magnitude))
        pi_ns = int(round(pi.to("ns").magnitude))

        def single_T1(tau):
            # wait = self.reset + self.polarize_time + self.buf_after_init * 2 + self.settle + longest_time + self.laser_time + self.readout_time - mw_on
            wait = longest_time - tau + self.buf_after_readout
            reset = \
                [(self.reset, [self.channel_dict["offr_laser"]], *self.IQ)]
            polarize = \
                [(self.polarize_time, [self.channel_dict["laser"]], *self.IQ)]
            background = \
                [(self.settle, [], *self.IQ)]
            tau_wait = \
                [(tau, [], *self.IQ)]
            flip = \
                [(pi_ns, [self.channel_dict["switch"]], *self.IQ)]

            probe = \
                [(self.laser_time, [self.channel_dict["laser"]], *self.IQ)]
            bg_decay = \
                [(self.buf_after_init, [], *self.IQ)]
            readout = \
                [(self.readout_time, [self.channel_dict["gate"]], *self.IQ)]
            # Lockin Part
            L_flip = \
                [(pi_ns, [], 0, 0)]
            L_readout = \
                [(self.readout_time, [self.channel_dict["gate"], self.channel_dict["CTR"]], 0, 0)]
            wait = \
                [(wait, [], 0, 0)]
            return reset + polarize + background + flip + tau_wait + probe + bg_decay + readout + wait + \
                   reset + polarize + background + L_flip + tau_wait + probe + bg_decay + L_readout + wait

        seqs = [single_T1(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
        return seqs

    def Resetting_L_T1_Adaptive(self, params, pi):
        longest_time = int(round(params["stop"].to("ns").magnitude))
        pi_ns = int(round(pi.to("ns").magnitude))

        def single_T1(tau):
            # wait = self.reset + self.polarize_time + self.buf_after_init * 2 + self.settle + longest_time + self.laser_time + self.readout_time - mw_on
            wait = longest_time - tau + self.buf_after_readout
            reset = \
                [(self.reset, [self.channel_dict["offr_laser"]], *self.IQ)]
            polarize = \
                [(self.polarize_time, [self.channel_dict["laser"]], *self.IQ)]
            background = \
                [(self.settle, [], *self.IQ)]
            tau_wait = \
                [(tau, [], *self.IQ)]
            flip = \
                [(pi_ns, [self.channel_dict["switch"]], *self.IQ)]

            probe = \
                [(self.laser_time, [self.channel_dict["laser"]], *self.IQ)]
            bg_decay = \
                [(self.buf_after_init, [], *self.IQ)]
            readout = \
                [(self.readout_time, [self.channel_dict["gate"]], *self.IQ)]
            # Lockin Part
            L_flip = \
                [(pi_ns, [], 0, 0)]
            L_readout = \
                [(self.readout_time, [self.channel_dict["gate"], self.channel_dict["CTR"]], 0, 0)]
            wait = \
                [(wait, [], 0, 0)]
            return reset + polarize + background + flip + tau_wait + probe + bg_decay + readout + \
                   reset + polarize + background + L_flip + tau_wait + probe + bg_decay + L_readout

        seqs = [single_T1(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
        return seqs

    def Pulsed_ODMR(self, pi):
        excitation = \
            [(self.laser_time, [self.channel_dict["laser"]], *self.IQ)]
        bg_decay = \
            [(self.buf_after_init, [], *self.IQ)]
        readout = \
            [(self.readout_time, [self.channel_dict["gate"]], *self.IQ)]
        rabi = \
            [(pi, [self.channel_dict["switch"]], *self.IQ)]
        wait = \
            [(self.buf_after_readout, [], *self.IQ)]
        return excitation + bg_decay + readout + rabi + wait

    def Ramsey(self, params, pi):
        '''
        :param params: the iteration array
        :param pi: length of the pi pulse
        :return: an array of pulse sequences
        '''
        longest_time = int(round(params["stop"].to("ns").magnitude))
        pi_ns = int(pi.to("ns").magnitude)

        def single_ramsey(tau):
            wait = longest_time - tau + self.buf_after_readout
            excitation = \
                [(self.laser_time, [self.channel_dict["laser"]], *self.IQ)]
            bg_decay = \
                [(self.buf_after_init, [], *self.IQ)]
            readout = \
                [(self.readout_time, [self.channel_dict["gate"]], *self.IQ)]
            first_pi = \
                [(pi_ns // 2, [self.channel_dict["switch"]], *self.IQ)]
            dephase = \
                [(tau, [], *self.IQ)]
            second_pi = \
                [(pi_ns // 2, [self.channel_dict["switch"]], *self.IQ)]
            wait = \
                [(wait, [], *self.IQ)]
            return excitation + bg_decay + readout + first_pi + dephase + second_pi + wait

        seqs = [single_ramsey(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
        return seqs

    def Resetting_Ramsey(self, params, pi):
        '''
        :param params: the iteration array
        :param pi: length of the pi pulse
        :return: an array of pulse sequences
        '''
        longest_time = int(round(params["stop"].to("ns").magnitude))
        pi_ns = int(pi.to("ns").magnitude)

        def single_ramsey(tau):
            wait = longest_time - tau + self.buf_after_readout
            reset = \
                [(self.reset, [self.channel_dict["offr_laser"]], *self.IQ)]
            polarize = \
                [(self.polarize_time, [self.channel_dict["laser"]], *self.IQ)]
            background = \
                [(self.settle, [self.channel_dict["gate"], self.channel_dict["CTR"]], *self.IQ)]
            first_pi = \
                [(pi_ns // 2, [self.channel_dict["switch"]], *self.IQ)]
            dephase = \
                [(tau, [], *self.IQ)]
            second_pi = \
                [(pi_ns // 2, [self.channel_dict["switch"]], *self.IQ)]
            probe = \
                [(self.laser_time, [self.channel_dict["laser"]], *self.IQ)]
            bg_decay = \
                [(self.buf_after_init, [], *self.IQ)]
            readout = \
                [(self.readout_time, [self.channel_dict["gate"]], *self.IQ)]
            wait = \
                [(wait, [], *self.IQ)]
            return reset + polarize + background + first_pi + dephase + second_pi + probe + bg_decay + readout + wait

        seqs = [single_ramsey(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
        return seqs

    def Resetting_L_Ramsey(self, params, pi):
        '''
        :param params: the iteration array
        :param pi: length of the pi pulse
        :return: an array of pulse sequences
        '''
        longest_time = int(round(params["stop"].to("ns").magnitude))
        pi_ns = int(pi.to("ns").magnitude)

        def single_ramsey(tau):
            wait = longest_time - tau + self.buf_after_readout
            reset = \
                [(self.reset, [self.channel_dict["offr_laser"]], *self.IQ)]
            polarize = \
                [(self.polarize_time, [self.channel_dict["laser"]], *self.IQ)]
            background = \
                [(self.settle, [], *self.IQ)]
            first_pi = \
                [(pi_ns // 2, [self.channel_dict["switch"]], *self.IQ)]
            dephase = \
                [(tau, [], *self.IQ)]
            second_pi = \
                [(pi_ns // 2, [self.channel_dict["switch"]], *self.IQ)]
            probe = \
                [(self.laser_time, [self.channel_dict["laser"]], *self.IQ)]
            bg_decay = \
                [(self.buf_after_init, [], *self.IQ)]
            readout = \
                [(self.readout_time, [self.channel_dict["gate"]], *self.IQ)]
            # Lockin Part
            L_first_pi = \
                [(pi_ns // 2, [], *self.IQ)]
            L_dephase = \
                [(tau, [], *self.IQ)]
            L_second_pi = \
                [(pi_ns // 2, [], *self.IQ)]
            L_readout = \
                [(self.readout_time, [self.channel_dict["gate"], self.channel_dict["CTR"]], *self.IQ)]
            wait = \
                [(wait, [], *self.IQ)]
            return reset + polarize + background + first_pi + dephase + second_pi + wait + probe + bg_decay + readout + \
                   reset + polarize + background + L_first_pi + L_dephase + L_second_pi + wait + probe + bg_decay + L_readout

        seqs = [single_ramsey(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
        return seqs

    def T1(self, params, pi):
        longest_time = int(round(params["stop"].to("ns").magnitude))
        pi_ns = int(pi.to("ns").magnitude)

        def single_T1(tau):
            wait = longest_time - tau + self.buf_after_readout
            excitation = \
                [(self.laser_time, [self.channel_dict["laser"]], *self.IQ)]
            bg_decay = \
                [(self.buf_after_init, [], *self.IQ)]
            readout = \
                [(self.readout_time, [self.channel_dict["gate"]], *self.IQ)]
            pi = \
                [(pi_ns, [self.channel_dict["switch"]], *self.IQ)]
            flip = \
                [(tau, [], *self.IQ)]
            wait = \
                [(wait, [], *self.IQ)]
            return excitation + bg_decay + readout + pi + flip + wait

        seqs = [single_T1(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
        return seqs

    def res_Topt(self, params):
        longest_time = int(round(params["stop"].to("ns").magnitude))
        bin_time = int(round(params["step"].to("ns").magnitude))

        def single_T1(start):
            wait = longest_time - start + bin_time + self.buf_after_readout
            excitation = \
                [(self.laser_time, [self.channel_dict["laser"]], *self.IQ)]
            bg_decay = \
                [(self.buf_after_init, [], *self.IQ)]
            before_bin = \
                [(start, [], *self.IQ)]
            readout = \
                [(bin_time, [self.channel_dict["gate"]], *self.IQ)]
            wait = \
                [(wait, [], *self.IQ)]
            return excitation + bg_decay + before_bin + readout + wait

        seqs = [single_T1(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
        return seqs

    def res_Topt_MW(self, params):
        longest_time = int(round(params["stop"].to("ns").magnitude))
        bin_time = int(round(params["step"].to("ns").magnitude))

        def single_T1(start):
            wait = longest_time - start + bin_time + self.buf_after_readout
            excitation = \
                [(self.laser_time, [self.channel_dict["laser"], self.channel_dict["switch"]], *self.IQ)]
            bg_decay = \
                [(self.buf_after_init, [self.channel_dict["switch"]], *self.IQ)]
            before_bin = \
                [(start, [self.channel_dict["switch"]], *self.IQ)]
            readout = \
                [(bin_time, [self.channel_dict["gate"], self.channel_dict["switch"]], *self.IQ)]
            wait = \
                [(wait, [self.channel_dict["switch"]], *self.IQ)]
            return excitation + bg_decay + before_bin + readout + wait

        seqs = [single_T1(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
        return seqs

    def off_res_Topt(self, params):
        longest_time = int(round(params["stop"].to("ns").magnitude))
        bin_time = int(round(params["step"].to("ns").magnitude))

        def single_T1(start):
            wait = longest_time - start + bin_time + self.buf_after_readout
            excitation = \
                [(self.laser_time, [self.channel_dict["offr_laser"]], *self.IQ)]
            bg_decay = \
                [(self.buf_after_init, [], *self.IQ)]
            before_bin = \
                [(start, [], *self.IQ)]
            readout = \
                [(bin_time, [self.channel_dict["gate"]], *self.IQ)]
            wait = \
                [(wait, [], *self.IQ)]
            return excitation + bg_decay + before_bin + readout + wait

        seqs = [single_T1(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
        return seqs

    def red_Laser_Power(self, params):
        longest_time = int(round(params["stop"].to("ns").magnitude))

        def single_RLP(e_time):
            wait = longest_time - e_time + self.buf_after_readout
            # wait = self.buf_after_readout
            excitation = \
                [(e_time, [self.channel_dict["offr_laser"]], *self.IQ)]
            bg_decay = \
                [(self.buf_after_init, [], *self.IQ)]
            readout = \
                [(self.readout_time, [self.channel_dict["gate"]], *self.IQ)]
            wait = \
                [(wait, [], *self.IQ)]
            return excitation + bg_decay + readout + wait

        seqs = [single_RLP(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
        return seqs

    def Laser_Power(self, params):
        longest_time = int(round(params["stop"].to("ns").magnitude))

        def single_LP(e_time):
            wait = longest_time - e_time + self.buf_after_readout
            # wait = self.buf_after_readout
            excitation = \
                [(e_time, [self.channel_dict["laser"]], *self.IQ)]
            bg_decay = \
                [(self.buf_after_init, [], *self.IQ)]
            readout = \
                [(self.readout_time, [self.channel_dict["gate"]], *self.IQ)]
            wait = \
                [(wait, [], *self.IQ)]
            return excitation + bg_decay + readout + wait

        seqs = [single_LP(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
        return seqs

    def Laser_Power_MW(self, params):
        longest_time = int(round(params["stop"].to("ns").magnitude))

        def single_LP(e_time):
            wait = longest_time - e_time + self.buf_after_readout
            # wait = self.buf_after_readout
            excitation = \
                [(e_time, [self.channel_dict["laser"], self.channel_dict["switch"]], *self.IQ)]
            bg_decay = \
                [(self.buf_after_init, [self.channel_dict["switch"]], *self.IQ)]
            readout = \
                [(self.readout_time, [self.channel_dict["gate"], self.channel_dict["switch"]], *self.IQ)]
            wait = \
                [(wait, [self.channel_dict["switch"]], *self.IQ)]
            return excitation + bg_decay + readout + wait

        seqs = [single_LP(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
        return seqs

    def L_Inv_Optical_Rabi(self, params):
        longest_time = int(round(params["stop"].to("ns").magnitude))

        def single_OR(e_time):
            wait = longest_time - e_time + self.buf_after_readout
            # wait = self.buf_after_readout
            reset = \
                [(self.reset, [self.channel_dict["offr_laser"]], 0, 0)]
            background = \
                [(self.settle, [self.channel_dict["offr_laser"]], 0, 0)]
            excitation = \
                [(e_time, [self.channel_dict["laser"]], 0, 0)]
            bg_decay = \
                [(self.buf_after_init, [], 0, 0)]
            readout = \
                [(self.readout_time, [self.channel_dict["gate"]], 0, 0)]
            wait = \
                [(wait, [], 0, 0)]
            L_excitation = \
                [(e_time, [], 0, 0)]
            L_readout = \
                [(self.readout_time, [self.channel_dict["gate"], self.channel_dict["CTR"]], 0, 0)]
            return reset + background + excitation + bg_decay + readout + wait + \
                   reset + background + L_excitation + bg_decay + L_readout + wait

        seqs = [single_OR(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
        return seqs

    def Resetting_L_EOM(self):
        IQ = [0, 0]
        reset = \
            [(self.reset, [self.channel_dict["offr_laser"]], *IQ)]
        polarize = \
            [(self.polarize_time, [self.channel_dict["laser"]], *IQ)]
        background = \
            [(self.settle, [], *IQ)]
        probe = \
            [(self.laser_time, [self.channel_dict["laser"], self.channel_dict["EOM"]], *IQ)]
        bg_decay = \
            [(self.buf_after_init, [], *IQ)]
        readout = \
            [(self.readout_time, [self.channel_dict["gate"]], *IQ)]
        L_probe = \
            [(self.laser_time, [self.channel_dict["laser"]], *IQ)]
        L_readout = \
            [(self.readout_time, [self.channel_dict["gate"], self.channel_dict["CTR"]], *IQ)]
        return reset + polarize + background + probe + bg_decay + readout + \
               reset + polarize + background + L_probe + bg_decay + L_readout
