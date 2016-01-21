a_global = "A VALUE!"

def obpm_say_this(_subject, _message):
    print(_subject)
    print(_message)

def cantcallme(_nope):
    raise Exception("SO DON'T!")

class TerminationException(Exception):
    pass