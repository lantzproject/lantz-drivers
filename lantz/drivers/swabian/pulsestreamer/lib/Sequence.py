import sys

import numpy as np
from enum import Enum


class Sequence():
    def __init__(self):
        self.__channel_digital = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: []}
        self.__channel_analog = {0: [], 1: []}
        self.__union_seq = [(0, 0, 0, 0)]
        self.__setby = self.Setby.UNDEFINED
        self.__union_seq_up_to_date = True

    def __union(self):
        # idea of the algorithm
        # 1) for each channel, calculate  the absolute timestamps (not the relative) -> t_cumsums
        # 2) join all these absolute timestamps together to a sorted unique list. This results in the timestamps (unique_t_cumsum) of the final pulse list 
        # 3) expand every single channel to final pulse list (unique_t_cumsum)
        # 4) join the channels together

        all_channel_arrays = []
        all_t_cumsums = []
        all_t_cumsums_concatinated = np.array([], dtype=np.int64)
        count_digital_channels = len(self.__channel_digital)
        count_analog_channels = len(self.__channel_analog)
        count_all_channels = count_digital_channels + count_analog_channels

        # 1) for each channel, calculate  the absolute timestamps (not the relative) -> t_cumsums
        # optimization: this loop could be fully parallized with minor changes
        for i in range(count_all_channels):
            if i < count_digital_channels:
                channel_sequence = self.__channel_digital[i]
            else:
                channel_sequence = self.__channel_analog[i - count_digital_channels]

            if len(channel_sequence) > 0:
                # store last entry
                last_touple = channel_sequence[-1]
                # remove all entries which have dt = 0
                channel_sequence = list(filter(lambda x: x[0] != 0, channel_sequence))
                # if the last dt is 0, add it again to the list
                if (last_touple[0]) == 0:
                    channel_sequence.append[last_touple]
                # make a numeric array
                sequence_array = np.array(channel_sequence)
                # and add it to the full list
                all_channel_arrays.append(sequence_array)
                # finally, update the unique list of t for which a new pulse is generated
                cumsum = np.cumsum(sequence_array[:, 0])
            else:
                all_channel_arrays.append([(0, 0)])
                cumsum = np.array([0], dtype=np.int64)

            all_t_cumsums.append(cumsum)
            all_t_cumsums_concatinated = np.append(all_t_cumsums_concatinated, cumsum)

        # 2) join all these absolute timestamps together to a sorted unique list which. This results in the timestamps (unique_t_cumsum) of the final pulse list 
        unique_t_cumsum = np.unique(all_t_cumsums_concatinated)

        # 3) expand every single channel to final pulse list (unique_t_cumsum)
        # create 2d array for every channel and timestamp
        data = np.zeros([count_all_channels, len(unique_t_cumsum)], dtype=np.int64)
        last = 0
        # optimization: this loop could be fully parallized with minor changes
        for i in range(count_all_channels):
            sequence_array = all_channel_arrays[i]
            cumsum = all_t_cumsums[i]
            if len(cumsum) > 0:
                i_cumsum = 0
                last = sequence_array[0][1]
                for x in range(len(unique_t_cumsum)):
                    data[i, x] = last
                    if (unique_t_cumsum[x] == cumsum[i_cumsum]):
                        if i_cumsum + 1 < len(cumsum):
                            i_cumsum = i_cumsum + 1
                        last = sequence_array[i_cumsum][1]

        # 4) join the channels together
        digi = data[0, :]
        for i in range(1, count_digital_channels):
            digi = digi + data[i, :]
            # revert the cumsum to get the relative pulse durations
        ts = np.insert(np.diff(unique_t_cumsum), 0, unique_t_cumsum[0])
        digi = digi
        a0 = data[count_digital_channels + 0]
        a1 = data[count_digital_channels + 1]

        # create the final pulse list
        result = list(zip(ts, digi, a0, a1))

        # there might be a pulse duration of 0 in the very beginning - remove it
        if len(result) > 0:
            if result[0][0] == 0:
                return result[1::]

        return result

    # def simplify(self, sequence):
    #     return self.__simplify(sequence)

    def __simplify(self, sequence):
        """Merge adjacent pulses that have equal channels"""
        i = 0
        while i + 1 < len(sequence):
            p0 = sequence[i]
            p1 = sequence[i + 1]
            if ((p0[1:] == p1[1:])):
                sequence.pop(i + 1)
                sequence[i] = ((p0[0] + p1[0]), p0[1], p0[2], p0[3])
            else:  # move one to the right
                i += 1
        return sequence

    class Setby(Enum):
        UNDEFINED = 0
        SETCHANNEL = 1
        SETSEQUENCE = 2

    def check_and_set_setby(self, setby):
        if self.__setby == self.Setby.UNDEFINED or self.__setby == setby:
            self.__setby = setby
        else:
            raise RuntimeError(
                'Sequence was defined already via ' + self.__setby + ' and connot be defined by ' + setby + ' afterwards.')

    def setDigitalChannel(self, channel, channel_sequence):
        assert channel in range(len(self.__channel_digital))
        # check if sequence is already set by other setMode
        self.check_and_set_setby(self.Setby.SETCHANNEL)

        self.__sequence_up_to_date = False
        ### the shifting could also be done in the union function
        ### argument check? t >= 0, value == 0/1
        sequence = []
        for t in channel_sequence:
            sequence.append((t[0], (1 << channel) * t[1]))

        self.__channel_digital[channel] = sequence

    def setAnalogChannel(self, channel, channel_sequence):
        assert channel in range(len(self.__channel_analog))

        ### argument check? t >= 0, value >= -1 and value <= 1

        self.check_and_set_setby(self.Setby.SETCHANNEL)

        self.__sequence_up_to_date = False
        sequence = []
        for t in channel_sequence:
            sequence.append((t[0], int(round(0x7fff * t[1]))))

        self.__channel_analog[channel] = sequence

    def setOutputList(self, pulse_list):
        self.check_and_set_setby(self.Setby.SETSEQUENCE)
        self.__union_seq = []

        for p in pulse_list:
            chan_byte = 0
            for c in p[1]:
                chan_byte |= 1 << c
            self.__union_seq.append((p[0], chan_byte, int(round(0x7fff * p[2])), int(round(0x7fff * p[3]))))

        self.__union_seq = self.__simplify(self.__union_seq)
        self.__sequence_up_to_date = True

    def getSequence(self):
        # check if sequence has to be rebuild
        if not self.__sequence_up_to_date:
            self.__union_seq = self.__union()
            self.__union_seq = self.__simplify(self.__union_seq)
            self.__sequence_up_to_date = True

        return self.__union_seq


# -------------cut off here

def random_digi():
    # creating random sequence
    t = np.random.uniform(20, 256, 1).astype(int)
    seq = []
    for i, ti in enumerate(t):
        state = i % 2
        seq += [(ti, state)]
    return seq


def random_ana():
    # creating random sequence
    t = np.random.uniform(20, 256, 1).astype(int)
    seq = []
    for i, ti in enumerate(t):
        a = np.random.random_integers(-1, 1)
        seq += [(ti, a)]
    return seq


if __name__ == '__main__':
    seq_ana = random_ana()

    s = Sequence()
    s.setDigitalChannel(0, random_digi())
    s.setDigitalChannel(1, random_digi())
    s.setDigitalChannel(2, random_digi())
    s.setDigitalChannel(3, random_digi())
    s.setDigitalChannel(4, random_digi())
    s.setDigitalChannel(5, random_digi())
    s.setDigitalChannel(6, random_digi())
    s.setDigitalChannel(7, random_digi())
    s.setAnalogChannel(0, seq_ana)
    s.setAnalogChannel(1, seq_ana)

    # the merge algorithm adds a few not required pulses - for the sake of comparison please remove it
    # merged_simplified = s.simplify(merged)
    merged_simplified = s.getSequence()
    print(merged_simplified)
