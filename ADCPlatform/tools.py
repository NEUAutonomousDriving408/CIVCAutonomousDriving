#coding=utf-8
from PIL import Image
import numpy
import threading
import ctypes
from time import sleep

def convert_image_to_numpy_ndarray(imageframe_byte):
	#image2 = Image.fromarray(array) # image2 is a PIL image,array is a numpy
	#array
   return numpy.array(Image.open(imageframe_byte))

def _async_raise(tid, exctype:'exctype'):
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid),
                                                     ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # "if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), None)
        raise SystemError("PyThreadState_SetAsyncExc failed")

class ThreadWithExc(threading.Thread):

	def _get_my_tid(self):
		if not self.isAlive():
			raise threading.ThreadError("the thread is not active")

		# do we have it cached?
		if hasattr(self, "_thread_id"):
			return self._thread_id

		# no, look for it in the _active dict
		for tid, tobj in threading._active.items():
			if tobj is self:
				self._thread_id = tid
				return tid
		raise AssertionError("could not determine the thread's id")

	def raise_exc(self,excobj):
		if self.isAlive():
			_async_raise(self._get_my_tid(),excobj)


	def stop(self):
		self.raise_exc(SystemExit)
		while self.isAlive():
			sleep( 0.1 )
			self.raise_exc(SystemExit)



