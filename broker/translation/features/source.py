"""
This process file is a part of the Optimal BPM Python parsing testing,
It is neither runnable or thought of as a example.
"""
import agent.lib.worker.handler

"""  Import the tricks of the trade
 Import the tricks of the trade row #2
"""
import plugins.optimalbpm.broker.lib.translation.features.fake_bpm_lib

""" Import the obpm_say_this function
"""
from plugins.optimalbpm.broker.lib.translation.features.fake_bpm_lib import cantcallme





""" Set the author name properly
特殊页面
"""
__author__ = 'nibo'

plugins.optimalbpm.broker.lib.translation.features.fake_bpm_lib = 'nibo'


"""
Tell computer far away to say "Hello!"

:param data: Sending hello, as this is the common thing under these circumstances.\\nMaking this line multiline, see if it works.
:param extra_param: Just sending this to complicate matters
:return: Ain't returning nothing

"""
try:
    plugins.optimalbpm.broker.lib.translation.features.fake_bpm_lib.obpm_say_this(plugins.optimalbpm.broker.lib.translation.features.fake_bpm_lib.obpm_say_this("Hello!", "Hey!"), plugins.optimalbpm.broker.lib.translation.features.fake_bpm_lib.a_global)
except plugins.optimalbpm.agent.lib.worker.handler.TerminationException as e:
    print("Wow, we are being told to terminate..better be nice and exit or re-raise the error..raising : " + str(e))
    raise("error")

"""
För varje kund, skicka papper
"""
for a in range(0, 3):
    print("This should happen three times")
    if 1 == 1:
        print("This should always happen three times.")

"""
If there are items left in the store house
"""
if 1 == 0:
    output1, output2 = "There is actually data coming out of it.", "sdf"
    output = str("This should never happen.")
else:
    print("This should always happen.")



"""
Set counter to 0
"""
counter = 0
"""
Tell the same thing to "the same person" 3 times
"""
while counter < 6:
    send_message("sdf", "the same person")
    counter = counter + 1
    counter += counter

print("printing a global: " + test)



callback("Hello from within process!")

def function_1_declaration(parameter_1_1, parameter_1_2 = None):
    """
    Testing a function declaration 1

    :param parameter_1_1: Parameter 1 is for testing parameters
    :param parameter_1_2: Parameter 2 is also for testing parameters
    :return:

    """
    print("This should happen, printing parameter_1_1 :" + parameter_1_1 + " and parameter_1_2 : " + parameter_1_2)

function_1_declaration(parameter_1_1 = "Param 1_1 value", parameter_1_2 = "Param 1_2 value")

def function_2_declaration(parameter_2_1, parameter_2_2):
    """
    Testing a function declaration 2

    :param parameter_2_1: Parameter 1 is for testing parameters
    :param parameter_2_2: Parameter 2 is also for testing parameters
    :return:

    """
    print("This should happen, printing parameter_2_1 :" + parameter_2_1 + " and parameter_2_2 : " + parameter_2_2)

function_2_declaration("Param 2_1 value", "Param 2_2 value")