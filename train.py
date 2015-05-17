import brian2 as br
import numpy as np
import math as ma
import random as rnd
import initial as init
import pudb
import snn
import sys

br.prefs.codegen.target = 'cython'

def DesiredOut(label, bench):
    return_val = None

    if bench == 'xor':
        if label == 1:
            return_val = 1*br.ms
        else:
            return_val = 7*br.ms

    return return_val

def WeightChange(s):
    A = 0.5*10**1
    tau = 0.5*br.ms
    return A*ma.exp(-s / tau)

def L(t):
    tau = 5.0*br.ms
    if t > 0:
        return ma.exp(float(-t / tau))
    else:
        return 0

def P_Index(S_l, S_d):
    return_val = 0

    return_val += abs(L(S_d) - L(S_l[0][0]*br.second))

    return return_val

def ReadTimes(filename):
    f = open(filename, 'r')

    #pudb.set_trace()
    lines = f.readlines()
    f.close()

    desired_times = [-1] * len(lines)

    for i in range(len(lines)):
        tmp = float(lines[i][:-1])
        desired_times[i] = tmp * br.second

    return desired_times

def _resume_step(ta, tb):
    A = 0.7
    tau = 0.5
    #pudb.set_trace()
    array = tb - ta
    max_indices = np.greater_equal(array, 0)
    max_indices = max_indices.astype(int, copy=False)
    d = array*max_indices
    a = 0.2

    return a + A*np.exp(-d / tau)

def _set_out_spike(net, S_i, l, d):
    """
        Returnsthe change in weight for a particular synaptic
        connection between learning neurons and output neurons.
        as computed by ReSuMe-style learning rule.

        However, it is modified from ReSuMe to get neurons
        to spike certain number of times (either 0 or 1) 
        as oposed to certain spike times.

        ToDo: Make this more efficient using numpy
        array handling etc...
    """
    if len(l) != d:
        x, y = 1.8, 1.8
        if d == 1:
            a = _resume_step(S_i, d)
            b = _resume_step(S_i, x*d)
        elif d == 0:
            dn = l[0]/br.ms
            a = _resume_step(S_i, x*dn)
            b = _resume_step(S_i, dn)
        return a - b
    return 0

def _netoutput(net, spike_monitor_names, N_hidden):
    indices_l, spikes_l = net[spike_monitor_names[-1]].it
    indices_i, spikes_i = net[spike_monitor_names[-2]].it

    S_l = init.collect_spikes(indices_l, spikes_l, 4)
    S_i = init.collect_spikes(indices_i, spikes_i, N_hidden[-1])

    return S_l, S_i

def Compare(S_l, S_d):
    if len(S_l) != len(S_d):
        print "ERROR: Mismatch in tuple length!"
        sys.exit()
    for i in range(len(S_l)):
        if len(S_l[i]) != S_d[i]:
            return False
    return True
        

def ReSuMe(net, mnist, start, end, Pc, N_hidden, T, N_h, N_o, v0, u0, I0, ge0, neuron_names, synapse_names, state_monitor_names, spike_monitor_names, parameters):

    trained = False
    N = len(mnist[0])
    N_hidden_last = len(net[neuron_names[-2]])
    N_out = len(net[neuron_names[-1]])

    N_h = 1
    N_o = 1

    for number in range(start, end):

        trained = False
        print "number = ", number
        dw = np.zeros(len(net[synapse_names[-1]]))

        count = 0
        for i in range(5):
            
            print "\tnumber = ", number, "count = ", count
            count += 1

            N_h = init.out(mnist[1][number][0])
            desired_index = number / 2

            lst = range(N_hidden_last)
            rnd.shuffle(lst)

            k = 0
            net = snn.Run(net, mnist, number, T, v0, u0, I0, ge0, \
                        neuron_names, synapse_names, state_monitor_names, \
                        spike_monitor_names, parameters)

            S_l, S_i = _netoutput(net, spike_monitor_names, N_hidden)
            label = mnist[1][number]
            S_d = init.out(label)

            t_min, t_max = min(S_i)[0], max(S_i)[0]

            modified = False
            for j in range(N_out):
                print "\t\ti = ", j
                t_in_tmp = S_i[j:-1:4]
                t_in = np.copy(t_in_tmp / br.ms)
                t_in = t_in.flatten()
                dw = _set_out_spike(net, t_in, S_l[j], S_d[j])
                if type(dw) == list:
                    #modified == True
                    S_i[j:-1:4] += dw

            #if modified == False:
            #    trained = True

    init._save_weights(net, synapse_names, len(synapse_names)-1, len(synapse_names))
    F = open("weights/trained.txt", 'w')
    F.write("True")
    F.close()

    return net

def Test(net, mnist, start, end, N_hidden, T, v0, u0, I0, ge0, \
        neuron_names, synapse_names, state_monitor_names, spike_monitor_names, parameters):

    hit, miss = 0, 0

    print "Testing"
    for number in range(start, end):
        #pudb.set_trace()
        print "\tnumber = ", number
        net = snn.Run(net, mnist, number, T, v0, u0, I0, ge0, \
                    neuron_names, synapse_names, state_monitor_names, \
                    spike_monitor_names, parameters)
        S_l, S_i = _netoutput(net, spike_monitor_names, N_hidden)
        label = mnist[1][number]
        S_d = init.out(label)
        result = Compare(S_l, S_d)
        if result == True:
            hit += 1
        else:
            miss += 1

    return hit, miss
