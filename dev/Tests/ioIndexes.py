from pyo import pa_get_devices_infos

inputs, outputs =  pa_get_devices_infos()

def getInput(*args):
    if len(args) == 1:
        for input in inputs:
            if args[0] in inputs[input]['name']:
                return input
        return 0
    elif len(args) == 0:
        for input in inputs:
            print "Input index : ", input, ", Name : ", inputs[input]['name']
    else:
        return -1

def getOutput(*args):
    if len(args) == 1:
        for output in outputs:
            if args[0] in outputs[output]['name']:
                return output
        return 0
    elif len(args) == 0:
        for output in outputs:
            print "Output index: ", output, ", Name: ", outputs[output]['name']
    else:
        return -1
            
def clean():
    global inputs, outputs
    del inputs
    del outputs
