from lantz import Driver, DictFeat, Action
import requests
import re
from urllib.parse import urlparse, ParseResult

class Relay(Driver):

    def __init__(self, host='192.168.1.4', endpoint='30000'):
        super().__init__()

        p = urlparse(host, 'http')
        netloc = p.netloc or p.path
        path = p.path if p.netloc else ''
        p = ParseResult('http', netloc, path, *p[3:])
        self.host = p.geturl()
        self.endpoint = str(endpoint)
        self.status_page = requests.compat.urljoin(self.host, '{}/42'.format(self.endpoint))
        self.all_on_page = requests.compat.urljoin(self.host, '{}/45'.format(self.endpoint))
        self.all_off_page = requests.compat.urljoin(self.host, '{}/46'.format(self.endpoint))
        return

    def parse_state(self, resp_text):
        relay_words = [m.start() for m in re.finditer('Relay', resp_text)][2:]
        relay_status = [resp_text[s+33:s+36] for s in relay_words]
        relay_status = [False if v == 'OFF' else True for v in relay_status]
        return relay_status

    def get_all_states(self):
        resp1 = requests.get(self.status_page)
        resp2 = requests.get(self.status_page)
        if 'Relay-01' not in resp1:
            resp1, resp2 = resp2, resp1
        states = self.parse_state(resp1.text) + self.parse_state(resp2.text)
        return states

    @DictFeat(keys=range(1, 9), values={True, False})
    def state(self, key):
        states = self.get_all_states()
        state = states[key - 1]
        return state

    @state.setter
    def state(self, key, value):
        offset = 1 if value else 0
        page = requests.compat.urljoin(self.host, '{}/{:02d}'.format(self.endpoint, 2 * key - 2 + offset))
        requests.get(page)
        return

    @Action()
    def all_on(self):
        resp = requests.get(self.all_on_page)
        return

    @Action()
    def all_off(self):
        resp = requests.get(self.all_off_page)
        return
