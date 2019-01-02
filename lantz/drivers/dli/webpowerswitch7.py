from lantz import Driver, Action, Feat, DictFeat, ureg
import requests
import re

class WebPowerSwitch7(Driver):
	timeout = 1

	def __init__(self, host='192.168.1.20:80', user='admin', pwd='1234', *args, **kwargs):
		self.host, self.user, self.pwd = host, user, pwd
		super().__init__(*args, **kwargs)

	def send_cmd(self, cmd):
		url = "http://%s/%s" % (self.host, cmd)
		resp = requests.get(url, auth=(self.user, self.pwd,),  timeout=self.timeout)
		return resp

	@Action()
	def get_status(self):
		resp = self.send_cmd('status')
		pattern = lambda id: '<div id="'+id+'">(..)</div>'
		to_bin = lambda string: bin(int(string, 16))[2:].zfill(8)
		to_bool = lambda bin_array: list(map(lambda x: x=='1', bin_array))
		def get_val(id):
			bool_arr = to_bool(to_bin(re.search(pattern(id), str(resp.content)).group(1)))
			bool_arr.reverse()
			return bool_arr
		
		return {k:get_val(k) for k in ['state', 'lock', 'perm']}

	@DictFeat(keys=range(1,9), values={True: 'ON', False: 'OFF'})
	def state(self, key):
		return 'ON' if self.get_status()['state'][key-1] else 'OFF'

	@state.setter
	def state(self, key, value):
		self.send_cmd('outlet?{}={}'.format(key, value))
