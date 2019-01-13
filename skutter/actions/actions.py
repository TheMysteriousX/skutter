import abc


class ActionBase(object):
    @abc.abstractmethod
    def do(self):
        raise NotImplemented

    @abc.abstractmethod
    def undo(self):
        raise NotImplemented

