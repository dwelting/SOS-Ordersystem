import time

class DebugMeasureTiming():
	_dictionary = dict()
	_enable = False

	def enable(self, set_enable=True):
		self._enable = set_enable

	def start(self, identifier=""):
		if self._enable:
			start_time = time.time()
			self._start_time = start_time
			if not identifier == "":
				self._dictionary[identifier] = dict()
				self._dictionary[identifier][identifier] = identifier
				self._dictionary[identifier]['start_time'] = start_time

	def finish(self, identifier=""):
		if self._enable:
			end_time = time.time()
			if identifier != "":
				if identifier not in self._dictionary: return
				start_time = self._dictionary[identifier]['start_time']
				identifier = ' ➤ ' + identifier
			else:
				start_time = self._start_time

			difference_ms = (end_time - start_time) * 1000
			difference_us = difference_ms * 1000

			if difference_ms >= 1000:
				difference_s = (end_time - start_time)
				print("Time elapsed: {:2.2f}s ({:.0f}ms) ({:.0f}us){}".format(difference_s, difference_ms, difference_us, identifier))
			else:
				print("Time elapsed: {:3.0f}ms ({:6.0f}us){}".format(difference_ms, difference_us, identifier))


DebugTiming = DebugMeasureTiming()




#high performance timer as context manager
#https://www.python.org/dev/peps/pep-0564/
class DebugMeasureTiming_context():
	def __init__(self):
		pass

	def __enter__(self):
		self.start()

	def __exit__(self, exc_type, exc_value, exc_traceback):
		self.finish()

	def start(self):
		try:
			self.start_time = time.perf_counter_ns()
		except:
			self.start_time = time.perf_counter()*1000000000

	def finish(self):
		try:
			end_time = time.perf_counter_ns()
		except:
			end_time = time.perf_counter()*1000000000

		difference_ns = end_time - self.start_time

		if difference_ns < 1000:
			print("Time elapsed: {:.0f}ns".format(difference_ns))
		else:
			difference_us = difference_ns / 1000
			if difference_us < 1000:
				print("Time elapsed: {:.0f}us ({:.0f}ns)".format(difference_us, difference_ns))
			else:
				difference_ms = difference_us / 1000
				if difference_ms < 1000:
					print("Time elapsed: ({:.0f}ms) ({:.0f}us) ({:.0f}ns)".format(difference_ms, difference_us, difference_ns))
				else:
					difference_s = difference_ms / 1000
					print("Time elapsed: {:2.2f}s ({:.0f}ms) ({:.0f}us) ({:.0f}ns)".format(difference_s, difference_ms, difference_us, difference_ns))




from contextlib import contextmanager
@contextmanager
def indent():
	try:
		yield
	finally:
		pass