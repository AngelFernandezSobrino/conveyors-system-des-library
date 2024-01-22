# DEVS model

## DEVS model specification

X set of inputs events
Y set of output events
S set of states
so initial state
ta time advance function for state
delta ext transition function for external events

delta int 

## Buffer size one with object transfer delay atomic model

S = ({REST, RESERVED, OCCUPIED, SENDING},{NOTHING, ONGOING, DELAY}[n_destinies], {DESTINY_AVAILABLE, DESTINY_NOT_AVAILABLE}[n_destinies], {DESTINY_UNLOCKED, DESTINY_LOCKED}[n_destinies])

s0 = (REST, NOTHING, DESTINY_AVAILABLE, DESTINY_UNLOCKED) 
<!-- ta((SENDING, _)) = $release_time -->
ta((OCCUPIED, _, DESTINY_AVAILABLE[n])) = 0
ta((SENDING, SENDING[n], _)) = 0
ta((SENDING, DELAY[n], _)) = $release_time

delta_int((OCCUPIED, _, DESTINY_AVAILABLE[n])) = (SENDING, SENDING[n], DESTINY_NOT_AVAILABLE[n])
delta_int((SENDING, SENDING[n], _)) = (SENDING, DELAY[n], _)
delta_int((SENDING, SENDING[n], _)) = (REST, NOTHING[n], _)

X = {input, reserve, destiny_is_available[n_destinies], destiny_isnt_available[n_destinies]}

delta_ext((_, DESTINY_AVAILABLE[n]), destiny_is_available[n]) = ERROR
delta_ext((_, DESTINY_AVAILABLE[n]), destiny_isnt_available[n]) = (_, DESTINY_NOT_AVAILABLE[n])
delta_ext((_, DESTINY_NOT_AVAILABLE[n]), destiny_is_available[n]) = (_, DESTINY_AVAILABLE[n])
delta_ext((_, DESTINY_NOT_AVAILABLE[n]), destiny_isnt_available[n]) = ERROR

delta_ext((REST, _,_), input) = ERROR
delta_ext((REST, _,_), reserve) = (RESERVED, _)

delta_ext((RESERVED, _,_), input) = OCCUPIED
delta_ext((RESERVED, _,_), reserve) = ERROR

delta_ext((OCCUPIED, _,_), input) = ERROR
delta_ext((OCCUPIED, _,_), reserve) = ERROR

delta_ext((SENDING, _,_), input) = ERROR
delta_ext((SENDING, _,_), reserve) = ERROR


Y = {available[n_origins], not_available[n_origins], output[n_origins], moving[n_origins]}

lambda((REST, _)) = not_available[n_origins]
lambda((SENDING, _)) = available[n_origins]
lambda((OCCUPIED, _, _)) = output[n]
lambda((SENDING, SEND_DELAY[n], _)) = moving[n]

## Conveyor (tranfer_time)

S = {AVAILABLE, NOT_AVAILABLE_BY_DESTINY, NOT_AVAILABLE_BY_MOVING, MOVING, NOT_AVAILABLE}

s0 = AVAILABLE

ta(MOVING) = $transfer_time
ta(NOT_AVAILABLE_BY_DESTINY) = 0
ta(NOT_AVAILABLE_BY_MOVING) = 0

delta_int(MOVING) = NOT_AVAILABLE
delta_int(NOT_AVAILABLE_BY_DESTINY) = NOT_AVAILABLE
delta_int(NOT_AVAILABLE_BY_MOVING) = MOVING


X = {input, moving, destiny_not_available, destiny_available}

delta_ext(AVAILABLE, input) = NOT_AVAILABLE_BY_MOVING
delta_ext(AVAILABLE, destiny_not_available) = NOT_AVAILABLE_BY_DESTINY
delta_ext(NOT_AVAILABLE_BY_MOVING, moving) = MOVING
delta_ext(NOT_AVAILABLE, destiny_available) = AVAILABLE
delta_ext(_, _) = ERROR


Y = {output, not_available, available, destiny_reserve}

lambda(NOT_AVAILABLE_BY_DESTINY) = not_available
lambda(NOT_AVAILABLE_BY_MOVING) = not_available, destiny_reserve
lambda(NOT_AVAILABLE) = available
lambda(MOVING) = output

## Buffer and one transfer coupled model

X = {destiny_available, object_input}
Y = 