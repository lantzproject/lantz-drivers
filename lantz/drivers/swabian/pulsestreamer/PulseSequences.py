import numpy as np
from lantz.driver import Driver
from lantz.drivers.swabian.pulsestreamer.lib.pulse_streamer_grpc import PulseStreamer
from lantz import Q_
from spyre.widgets.rangespace import RangeDict
from lantz import Action, Feat, DictFeat, ureg



class Pulses(Driver):

    default_digi_dict = {"laser": "ch0", "offr_laser": "ch1", "CTR": "ch5", "switch": "ch6", "gate": "ch7", "": None}
    default_anal_dict = {"ai0": "I", "ai1": "Q"}

    def __init__(self, channel_dict = default_digi_dict, laser_time = 150*Q_(1,"us"), readout_time = 150*Q_(1,"us"),
                 buffer_after_init = 450*Q_(1,"us"), buffer_after_readout = 2*Q_(1, "us"),
                 polarize_time = 900*Q_(1,"us"), settle = 150*Q_(1,"us") , reset=100*Q_(1,"ns"), IQ = [0.5,0], ip="192.168.1.111"):
        """
        :param channel_dict: Dictionary of which channels correspond to which instr controls
        :param laser_time: Laser time in us
        :param CTR: When False CTR0 When True CTR1
        :param readout_time: Readout time in us
        :param buffer_after_init: Buffer after laser turns off in us to allow the population to thermalize
        :param buffer_after_readout: Buffer between the longest pulse and the readout in us to prevent laser to leak in
        :param IQ: IQ vector that rotates the spin
        """
        super().__init__()
        self.channel_dict = channel_dict
        self.laser_time = int(round(laser_time.to("ns").magnitude))
        self.readout_time = int(round(readout_time.to("ns").magnitude))
        self.buffer_after_init = int(round(buffer_after_init.to("ns").magnitude))
        self.buffer_after_readout = int(round(buffer_after_readout.to("ns").magnitude))
        self.polarize_time = int(round(polarize_time.to("ns").magnitude))
        self.settle = int(round(settle.to("ns").magnitude))
        self.reset = int(round(reset.to("ns").magnitude))
        self._normalize_IQ(IQ)
        self.Pulser = PulseStreamer(ip)

    @Feat()
    def has_sequence(self):
        """
        Has Sequence
        """
        return self.Pulser.hasSequence()

    def stream(self,seq):
        initial = (0, [], 0, 0)
        final = (0, [], 0, 0)
        underflow = (0, [], 0, 0)
        self.Pulser.stream(seq, -1, initial, final, underflow, "IMMEDIATE")

    def _normalize_IQ(self, IQ):
        norm_iq = IQ/(2*np.linalg.norm(IQ))
        self.I = norm_iq[0]
        self.Q = norm_iq[1]

    def Transient_Measure(self):
        excitation = \
            [(self.laser_time, [self.channel_dict["laser"]], 0, 0)]
        bg_decay = \
            [(self.buffer_after_init, [], 0, 0)]
        readout = \
            [(self.readout_time, [self.channel_dict["gate"]], 0, 0)]
        buffer = \
            [(self.buffer_after_readout, [], 0, 0)]
        return excitation + bg_decay + readout + buffer


    def CODMR(self):
        excitation = \
            [(self.laser_time, [self.channel_dict["laser"], self.channel_dict["switch"]], 0, 0)]
        bg_decay = \
            [(self.buffer_after_init, [self.channel_dict["switch"]], 0, 0)]
        readout = \
            [(self.readout_time, [self.channel_dict["switch"], self.channel_dict["gate"]], 0, 0)]
        buffer = \
            [(self.buffer_after_readout, [self.channel_dict["switch"]], 0, 0)]
        return excitation + bg_decay + readout + buffer

    def L_CODMR(self, measure = 0):
        s_excitation = \
            [(self.laser_time, [self.channel_dict["laser"], self.channel_dict["switch"]], 0, 0)]
        s_bg_decay = \
            [(self.buffer_after_init, [], 0, 0)]
        s_readout = \
            [(self.readout_time, [self.channel_dict["gate"]], 0, 0)]
        s_buffer = \
            [(self.buffer_after_readout, [], 0, 0)]
        s = s_excitation + s_bg_decay + s_readout + s_buffer
        m_excitation = \
            [(self.laser_time, [self.channel_dict["laser"]], 0, 0)]
        m_bg_decay = \
            [(self.buffer_after_init, [], 0, 0)]
        m_readout = \
            [(self.readout_time, [self.channel_dict["gate"]], 0, 0)]
        m_buffer = \
            [(self.buffer_after_readout, [], 0, 0)]
        m = m_excitation + m_bg_decay + m_readout + m_buffer
        b_excitation = \
            [(self.laser_time, [self.channel_dict["CTR"], self.channel_dict["laser"]], 0, 0)]
        b_bg_decay = \
            [(self.buffer_after_init, [self.channel_dict["CTR"]], 0, 0)]
        b_readout = \
            [(self.readout_time, [self.channel_dict["CTR"], self.channel_dict["gate"]], 0, 0)]
        b_buffer = \
            [(self.buffer_after_readout, [self.channel_dict["CTR"]], 0, 0)]
        b = b_excitation + b_bg_decay + b_readout + b_buffer
        return s + m*measure + b


    def Rabi(self, params):
        longest_time = int(round(params["stop"].to("ns").magnitude))
        def single_rabi(mw_on):
            wait = longest_time-mw_on+self.buffer_after_readout
            excitation = \
                [(self.laser_time, [self.channel_dict["laser"]], 0, 0)]
            bg_decay = \
                [(self.buffer_after_init, [], 0, 0)]
            readout = \
                [(self.readout_time, [self.channel_dict["gate"]], 0, 0)]
            rabi = \
                [(mw_on, [self.channel_dict["switch"]], 0, 0)]
            wait = \
                [(wait, [], 0, 0)]
            return excitation + bg_decay + readout + rabi + wait
        seqs = [single_rabi(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
        return seqs

    def Resetting_Rabi(self, params):
        longest_time = int(round(params["stop"].to("ns").magnitude))
        def single_rabi(mw_on):
            #wait = self.reset + self.polarize_time + self.buffer_after_init * 2 + self.settle + longest_time + self.laser_time + self.readout_time - mw_on
            wait = longest_time - mw_on + self.buffer_after_readout
            reset = \
                [(self.reset, [self.channel_dict["offr_laser"]], 0, 0)]
            polarize = \
                [(self.polarize_time, [self.channel_dict["laser"]], 0, 0)]
            bg_decay = \
                [(self.buffer_after_init, [], 0, 0)]
            background = \
                [(self.settle, [self.channel_dict["gate"], self.channel_dict["CTR"]], 0, 0)]
            rabi = \
                [(mw_on, [self.channel_dict["switch"]], 0, 0)]
            probe = \
                [(self.laser_time, [self.channel_dict["laser"]], 0, 0)]
            bg_decay = \
                [(self.buffer_after_init, [], 0, 0)]
            readout = \
                [(self.readout_time, [self.channel_dict["gate"]], 0, 0)]
            wait = \
                [(wait, [], 0, 0)]

            return reset + polarize + bg_decay + background + rabi + probe + bg_decay + readout + wait
        seqs = [single_rabi(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
        return seqs

    def Resetting_L_Rabi(self, params):
        longest_time = int(round(params["stop"].to("ns").magnitude))

        def single_rabi(mw_on):
            #wait = self.reset + self.polarize_time + self.buffer_after_init * 2 + self.settle + longest_time + self.laser_time + self.readout_time - mw_on
            wait = longest_time - mw_on + self.buffer_after_readout
            reset = \
                [(self.reset, [self.channel_dict["offr_laser"]], 0, 0)]
            polarize = \
                [(self.polarize_time, [self.channel_dict["laser"]], 0, 0)]
            # bg_decay = \
            #     [(self.buffer_after_init, [], 0, 0)]
            background = \
                [(self.settle, [], 0, 0)]
            rabi = \
                [(mw_on, [self.channel_dict["switch"]], 0, 0)]
            probe = \
                [(self.laser_time, [self.channel_dict["laser"]], 0, 0)]
            bg_decay = \
                [(self.buffer_after_init, [], 0, 0)]
            readout = \
                [(self.readout_time, [self.channel_dict["gate"]], 0, 0)]
            #Lockin Part
            L_rabi = \
                [(mw_on, [], 0, 0)]
            L_readout = \
                [(self.readout_time, [self.channel_dict["gate"], self.channel_dict["CTR"]], 0, 0)]
            wait = \
                [(wait, [], 0, 0)]

            return reset + polarize + bg_decay + background + rabi + probe + bg_decay + readout + wait + \
                   reset + polarize + bg_decay + background + L_rabi + probe + bg_decay + L_readout + wait

        seqs = [single_rabi(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
        return seqs

    def T2(self, params, pi):
        longest_time = int(round(params["stop"].to("ns").magnitude))
        pi_ns = int(round(pi.to("ns").magnitude))
        def single_T2(tau):
            #wait = self.reset + self.polarize_time + self.buffer_after_init * 2 + self.settle + longest_time + self.laser_time + self.readout_time - mw_on
            wait = longest_time-tau
            excitation = \
                [(self.laser_time, [self.channel_dict["laser"]], 0, 0)]
            bg_decay = \
                [(self.buffer_after_init, [], 0, 0)]
            readout = \
                [(self.readout_time, [self.channel_dict["gate"]], 0, 0)]
            first_pi2 = \
                [(pi_ns // 2, [self.channel_dict["switch"]], 0, 0)]
            dephase = \
                [(tau // 2, [], 0, 0)]
            flip = \
                [(pi_ns, [self.channel_dict["switch"]], 0, 0)]
            rephase = \
                [(tau // 2, [], 0, 0)]
            second_pi2 = \
                [(pi_ns // 2, [self.channel_dict["switch"]], 0, 0)]
            wait = \
                [(wait, [], 0, 0)]
            return excitation + bg_decay + readout + first_pi2 + dephase + flip + rephase + second_pi2 + wait
        seqs = [single_T2(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
        return seqs

    def Resetting_T2(self, params, pi):
        longest_time = int(round(params["stop"].to("ns").magnitude))
        pi_ns = int(round(pi.to("ns").magnitude))
        def single_T2(tau):
            #wait = self.reset + self.polarize_time + self.buffer_after_init * 2 + self.settle + longest_time + self.laser_time + self.readout_time - mw_on
            wait = longest_time-tau  + self.buffer_after_readout
            reset = \
                [(self.reset, [self.channel_dict["offr_laser"]], 0, 0)]
            polarize = \
                [(self.polarize_time, [self.channel_dict["laser"]], 0, 0)]
            background = \
                [(self.settle, [self.channel_dict["gate"], self.channel_dict["CTR"]], 0, 0)]
            first_pi2 = \
                [(pi_ns // 2, [self.channel_dict["switch"]], 0, 0)]
            dephase = \
                [(tau // 2, [], 0, 0)]
            flip = \
                [(pi_ns, [self.channel_dict["switch"]], 0, 0)]
            rephase = \
                [(tau // 2, [], 0, 0)]
            second_pi2 = \
                [(pi_ns // 2, [self.channel_dict["switch"]], 0, 0)]
            probe = \
                [(self.laser_time, [self.channel_dict["laser"]], 0, 0)]
            bg_decay = \
                [(self.buffer_after_init, [], 0, 0)]
            readout = \
                [(self.readout_time, [self.channel_dict["gate"]], 0, 0)]
            wait = \
                [(wait, [], 0, 0)]

            return reset + polarize + bg_decay + background + first_pi2 + dephase + flip + rephase + second_pi2 + probe + bg_decay + readout + wait
        seqs = [single_T2(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
        return seqs

    def Resetting_L_T2(self, params, pi):
        longest_time = int(round(params["stop"].to("ns").magnitude))
        pi_ns = int(round(pi.to("ns").magnitude))
        def single_T2(tau):
            #wait = self.reset + self.polarize_time + self.buffer_after_init * 2 + self.settle + longest_time + self.laser_time + self.readout_time - mw_on
            wait = longest_time - tau  + self.buffer_after_readout
            reset = \
                [(self.reset, [self.channel_dict["offr_laser"]], 0, 0)]
            polarize = \
                [(self.polarize_time, [self.channel_dict["laser"]], 0, 0)]
            background = \
                [(self.settle, [], 0, 0)]
            first_pi2 = \
                [(pi_ns // 2, [self.channel_dict["switch"]], 0, 0)]
            dephase = \
                [(tau // 2, [], 0, 0)]
            flip = \
                [(pi_ns, [self.channel_dict["switch"]], 0, 0)]
            rephase = \
                [(tau // 2, [], 0, 0)]
            second_pi2 = \
                [(pi_ns // 2, [self.channel_dict["switch"]], 0, 0)]
            probe = \
                [(self.laser_time, [self.channel_dict["laser"]], 0, 0)]
            bg_decay = \
                [(self.buffer_after_init, [], 0, 0)]
            readout = \
                [(self.readout_time, [self.channel_dict["gate"]], 0, 0)]
            # Lockin Part
            L_first_pi2 = \
                [(pi_ns // 2, [], 0, 0)]
            L_dephase = \
                [(tau // 2, [], 0, 0)]
            L_flip = \
                [(pi_ns, [], 0, 0)]
            L_rephase = \
                [(tau // 2, [], 0, 0)]
            L_second_pi2 = \
                [(pi_ns // 2, [], 0, 0)]
            L_readout = \
                [(self.readout_time, [self.channel_dict["gate"], self.channel_dict["CTR"]], 0, 0)]
            wait = \
                [(wait, [], 0, 0)]

            return reset + polarize + bg_decay + background + first_pi2 + dephase + flip + rephase + second_pi2 + wait + probe + bg_decay + readout + \
                   reset + polarize + bg_decay + background + L_first_pi2 + L_dephase + L_flip + L_rephase + L_second_pi2 + wait + probe + bg_decay + L_readout

        seqs = [single_T2(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
        return seqs

    # def Experimental_Rabi(self, params):
    #     longest_time = int(round(params["stop"].to("ns").magnitude))
    #     def single_rabi(mw_on):
    #         wait = longest_time-mw_on
    #         polarization = [(self.polarize_time, [self.channel_dict["laser"]], 0, 0)]
    #         settle = [(self.settle, [], 0, 0)]
    #         rabi = \
    #             [(mw_on, [self.channel_dict["switch"]], 0, 0)]
    #         wait = \
    #             [(wait, [], 0, 0)]
    #         probe = [(self.laser_time, [self.channel_dict["laser"]], 0, 0)]
    #         bg_decay = \
    #             [(self.buffer_after_init, [], 0, 0)]
    #         readout = \
    #             [(self.readout_time, [self.channel_dict["gate"]], 0, 0)]
    #         return polarization + settle + rabi + wait + probe + bg_decay + readout
    #     seqs = [single_rabi(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
    #     return seqs
    #
    # def L_Experimental_Rabi(self, params, cycle=0):
    #     longest_time = int(round(params["stop"].to("ns").magnitude))
    #     def single_rabi(mw_on):
    #         wait = longest_time-mw_on
    #         polarization = [(self.polarize_time, [self.channel_dict["laser"]], 0, 0)]
    #         settle = [(self.readout_time, [self.channel_dict["gate"], self.channel_dict["CTR"]], 0, 0)]
    #         rabi = \
    #             [(mw_on, [self.channel_dict["switch"]], 0, 0)]
    #         wait = \
    #             [(wait, [], 0, 0)]
    #         probe = [(self.laser_time, [self.channel_dict["laser"]], 0, 0)]
    #         bg_decay = \
    #             [(self.buffer_after_init, [], 0, 0)]
    #         readout = \
    #             [(self.readout_time, [self.channel_dict["gate"]], 0, 0)]
    #         return polarization + bg_decay + settle + rabi + wait + probe + bg_decay + readout
    #     seqs = [single_rabi(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
    #     return seqs

    # def Traditional_Rabi(self, params, cycle=1):
    #     longest_time = int(round(params["stop"].to("ns").magnitude))
    #     def single_rabi(mw_on):
    #         wait = longest_time-mw_on
    #         polarization = [(self.polarize_time, [self.channel_dict["laser"], self.channel_dict["gate"], self.channel_dict["CTR"]], 0, 0)]
    #         bg_decay = \
    #             [(self.buffer_after_init, [], 0, 0)]
    #         rabi = \
    #             [(mw_on, [self.channel_dict["switch"]], 0, 0)]
    #         wait = \
    #             [(wait, [], 0, 0)]
    #         probe = [(self.polarize_time, [self.channel_dict["laser"], self.channel_dict["gate"],], 0, 0)]
    #         b_bg_decay = \
    #             [(self.buffer_after_init, [], 0, 0)]
    #         b_rabi = \
    #             [(mw_on, [], 0, 0)]
    #         # b_wait = \
    #         #     [(wait, [], 0, 0)]
    #         return (polarization + bg_decay + rabi + wait)* cycle + (probe + b_bg_decay + b_rabi + wait)*cycle
    #     seqs = [single_rabi(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
    #     return seqs


    def Pulsed_ODMR(self, pi):
        excitation = \
            [(self.laser_time, [self.channel_dict["laser"]], 0, 0)]
        bg_decay = \
            [(self.buffer_after_init, [], 0, 0)]
        readout = \
            [(self.readout_time, [self.channel_dict["gate"]], 0, 0)]
        rabi = \
            [(pi, [self.channel_dict["switch"]], 0, 0)]
        wait = \
            [(self.buffer_after_readout, [], 0, 0)]
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
            wait = longest_time-tau+self.buffer_after_readout
            excitation = \
                [(self.laser_time, [self.channel_dict["laser"]], 0, 0)]
            bg_decay = \
                [(self.buffer_after_init, [], 0, 0)]
            readout = \
                [(self.readout_time, [self.channel_dict["gate"]], 0, 0)]
            first_pi = \
                [(pi_ns//2, [self.channel_dict["switch"]], 0, 0)]
            dephase = \
                [(tau, [], 0, 0)]
            second_pi = \
                [(pi_ns // 2, [self.channel_dict["switch"]], 0, 0)]
            wait = \
                [(wait, [], 0, 0)]
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
            wait = longest_time-tau  + self.buffer_after_readout
            reset = \
                [(self.reset, [self.channel_dict["offr_laser"]], 0, 0)]
            polarize = \
                [(self.polarize_time, [self.channel_dict["laser"]], 0, 0)]
            background = \
                [(self.settle, [self.channel_dict["gate"], self.channel_dict["CTR"]], 0, 0)]
            first_pi = \
                [(pi_ns//2, [self.channel_dict["switch"]], 0, 0)]
            dephase = \
                [(tau, [], 0, 0)]
            second_pi = \
                [(pi_ns // 2, [self.channel_dict["switch"]], 0, 0)]
            probe = \
                [(self.laser_time, [self.channel_dict["laser"]], 0, 0)]
            bg_decay = \
                [(self.buffer_after_init, [], 0, 0)]
            readout = \
                [(self.readout_time, [self.channel_dict["gate"]], 0, 0)]
            wait = \
                [(wait, [], 0, 0)]
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
            wait = longest_time-tau + self.buffer_after_readout
            reset = \
                [(self.reset, [self.channel_dict["offr_laser"]], 0, 0)]
            polarize = \
                [(self.polarize_time, [self.channel_dict["laser"]], 0, 0)]
            background = \
                [(self.settle, [], 0, 0)]
            first_pi = \
                [(pi_ns//2, [self.channel_dict["switch"]], 0, 0)]
            dephase = \
                [(tau, [], 0, 0)]
            second_pi = \
                [(pi_ns // 2, [self.channel_dict["switch"]], 0, 0)]
            probe = \
                [(self.laser_time, [self.channel_dict["laser"]], 0, 0)]
            bg_decay = \
                [(self.buffer_after_init, [], 0, 0)]
            readout = \
                [(self.readout_time, [self.channel_dict["gate"]], 0, 0)]
            # Lockin Part
            L_first_pi = \
                [(pi_ns//2, [], 0, 0)]
            L_dephase = \
                [(tau, [], 0, 0)]
            L_second_pi = \
                [(pi_ns // 2, [], 0, 0)]
            L_readout = \
                [(self.readout_time, [self.channel_dict["gate"], self.channel_dict["CTR"]], 0, 0)]
            wait = \
                [(wait, [], 0, 0)]
            return reset + polarize + background + first_pi + dephase + second_pi + probe + bg_decay + readout + wait + \
                   reset + polarize + background + L_first_pi + L_dephase + L_second_pi + probe + bg_decay + L_readout + wait
        seqs = [single_ramsey(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
        return seqs

    def T1(self, params, pi):
        longest_time = int(round(params["stop"].to("ns").magnitude))
        pi_ns = int(pi.to("ns").magnitude)
        def single_T1(tau):
            wait = longest_time-tau+self.buffer_after_readout
            excitation = \
                [(self.laser_time, [self.channel_dict["laser"]], 0, 0)]
            bg_decay = \
                [(self.buffer_after_init, [], 0, 0)]
            readout = \
                [(self.readout_time, [self.channel_dict["gate"]], 0, 0)]
            pi = \
                [(pi_ns, [self.channel_dict["switch"]], 0, 0)]
            flip = \
                [(tau, [], 0, 0)]
            wait = \
                [(wait, [], 0, 0)]
            return excitation + bg_decay + readout + pi + flip + wait
        seqs = [single_T1(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
        return seqs


    def res_Topt(self, params):
        longest_time = int(round(params["stop"].to("ns").magnitude))
        bin_time = int(round(params["step"].to("ns").magnitude))
        def single_T1(start):
            wait = longest_time-start+bin_time+self.buffer_after_readout
            excitation = \
                [(self.laser_time, [self.channel_dict["laser"]], 0, 0)]
            bg_decay = \
                [(self.buffer_after_init, [], 0, 0)]
            before_bin = \
                [(start, [], 0, 0)]
            readout = \
                [(self.bin_time, [self.channel_dict["gate"]], 0, 0)]
            wait = \
                [(wait, [], 0, 0)]
            return excitation + bg_decay + before_bin + readout + wait
        seqs = [single_T1(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
        return seqs[:-1]

    def off_res_Topt(self, params):
        longest_time = int(round(params["stop"].to("ns").magnitude))
        bin_time = int(round(params["step"].to("ns").magnitude))
        def single_T1(start):
            wait = longest_time-start+bin_time+self.buffer_after_readout
            excitation = \
                [(self.laser_time, [self.channel_dict["offr_laser"]], 0, 0)]
            bg_decay = \
                [(self.buffer_after_init, [], 0, 0)]
            before_bin = \
                [(start, [], 0, 0)]
            readout = \
                [(self.bin_time, [self.channel_dict["gate"]], 0, 0)]
            wait = \
                [(wait, [], 0, 0)]
            return excitation + bg_decay + before_bin + readout + wait
        seqs = [single_T1(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
        return seqs[:-1]


    def red_Laser_Power(self, params):
        longest_time = int(round(params["stop"].to("ns").magnitude))
        def single_RLP(e_time):
            wait = longest_time-e_time+self.buffer_after_readout
            #wait = self.buffer_after_readout
            excitation = \
                [(e_time, [self.channel_dict["offr_laser"]], 0, 0)]
            bg_decay = \
                [(self.buffer_after_init, [], 0, 0)]
            readout = \
                [(self.readout_time, [self.channel_dict["gate"]], 0, 0)]
            wait = \
                [(wait, [], 0, 0)]
            return excitation + bg_decay + readout + wait
        seqs = [single_RLP(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
        return seqs

    def Laser_Power(self, params):
        longest_time = int(round(params["stop"].to("ns").magnitude))
        def single_LP(e_time):
            wait = longest_time-e_time+self.buffer_after_readout
            #wait = self.buffer_after_readout
            excitation = \
                [(e_time, [self.channel_dict["laser"]], 0, 0)]
            bg_decay = \
                [(self.buffer_after_init, [], 0, 0)]
            readout = \
                [(self.readout_time, [self.channel_dict["gate"]], 0, 0)]
            wait = \
                [(wait, [], 0, 0)]
            return excitation + bg_decay + readout + wait
        seqs = [single_LP(int(round(mw_time.to("ns").magnitude))) for mw_time in params.array]
        return seqs


