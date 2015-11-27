import logging
import sys

class log_obj():
   ''' Object for handling logging across sevaral modules/scripts
   USAGE:
   >>> from log import _logger
   >>> _logger.Set(filename='metadata.log')
   >>> _logger.error("error msg %s, %s", 'arg1', 'arg2')
   '''
   def __init__(self):
        self.level=logging.INFO,
        self.stream=sys.stdout,
        self.format='%(levelname)s:%(message)s',
        self.filemode='w'
   def Set(filename='metadata.log'):
    # Setup of what?
    logging.basicConfig(
        level=self.level,
        stream=self.stream,
        format=self.format,
        filename=filename,
        filemode=self.filemode
    )
    self.logger = logging.getLogger(__name__)
   def debug(self, *msg):
      self.logger.debug(*msg)
   def info(self, *msg):
      self.logger.info(*msg)
   def warning(self, *msg):
      self.logger.warning(*msg)
   def error(self, *msg):
      self.logger.error(*msg)
   def log(self, *msg):
      self.logger.log(*msg)

# Init _logger
_logger = log_obj()
