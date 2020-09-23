from lantz.core import Feat, MessageBasedDriver


class Lakeshore475(MessageBasedDriver):

    @Feat(units='gauss')
    def field(self):
        return self.query('RDGFIELD?')

    @Feat(units='Hz')
    def frequency(self):
        return self.query('RDGFRQ?')
