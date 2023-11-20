
# DEVS model specification

X set of inputs events
Y set of output events
S set of states
so initial state
ta time advance function for state
delta ext transition function for external events

delta int 

# Destiny status atomic model

X = {destiny_available, destiny_unavailable}
Y = {available}
S = {available, unavailable}


# Buffer size one atomic model

X = {destiny_available, reserve, object_input}
Y = {available, object_output}
S = {free, reserved, occupied}
s0 = free
ta(free) = inf
ta(occupied) = $delay

delta_ext(free, object_input) = occupied

delta_ext(reserved, object_input) = fatal_error

delta_ext(occupied, destiny_available) = k

# Object transfer atomic model

X = {object_input}
Y = {object_output}
S = {free, occupied }
s0 = free
ta(free) = inf
ta(occupied) = $transfer_time

delta_ext(free, object_input) = occupied
delta_ext(occupied, object_input) = fatal_error

delta_int(occupied) = free

lambda(occupied) = object_output

# Buffer and one transfer coupled model

X = {destiny_available, object_input}
Y = 