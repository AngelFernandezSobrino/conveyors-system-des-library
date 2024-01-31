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

ta((OCCUPIED, _, DESTINY_AVAILABLE[n])) = 0
ta((SENDING, ONGOING[n], _)) = 0
ta((SENDING, DELAY[n], _)) = $release_time

delta_int((OCCUPIED, _, DESTINY_AVAILABLE[n])) = (SENDING, ONGOING[n], DESTINY_NOT_AVAILABLE[n])
delta_int((SENDING, ONGOING[n], _)) = (SENDING, DELAY[n], _)
delta_int((SENDING, DELAY[n], _)) = (REST, NOTHING[n], _)

X = {receive, re serve, destiny_is_available[n_destinies], destiny_isnt_available[n_destinies]}

delta_ext((_, DESTINY_AVAILABLE[n]), destiny_isnt_available[n]) = (_, DESTINY_NOT_AVAILABLE[n])
delta_ext((_, DESTINY_NOT_AVAILABLE[n]), destiny_is_available[n]) = (_, DESTINY_AVAILABLE[n])
delta_ext((REST, _,_), reserve) = (RESERVED, _)
delta_ext((RESERVED, _,_), receive) = (OCCUPIED, _,_)


Y = {reserve[n_destinies], send[n_destinies], available[n_origins], not_available[n_origins]}

lambda((REST, _)) = not_available[n_origins]
lambda((SENDING, _)) = available[n_origins]
lambda((OCCUPIED, _, _)) = reserve[n]
lambda((SENDING, DELAY[n], _)) = send[n]

## Conveyor (tranfer_time)

S = {AVAILABLE, NOT_AVAILABLE_BY_MOVING, WAITING_RECEPTION, MOVING, NOT_AVAILABLE}

s0 = AVAILABLE

ta(MOVING) = $transfer_time
ta(NOT_AVAILABLE_BY_MOVING) = 0

delta_int(MOVING) = NOT_AVAILABLE
delta_int(NOT_AVAILABLE_BY_MOVING) = WAITING_RECEPTION


X = {reserve, receive, destiny_not_available, destiny_available}

delta_ext(AVAILABLE, reserve) = NOT_AVAILABLE_BY_MOVING
delta_ext(AVAILABLE, destiny_not_available) = NOT_AVAILABLE
delta_ext(WAITING_RECEPTION, receive) = MOVING
delta_ext(NOT_AVAILABLE, destiny_available) = AVAILABLE


Y = {reserve, send, available, not_available}

lambda(AVAILABLE) = not_available
lambda(NOT_AVAILABLE_BY_MOVING) = reserve
lambda(NOT_AVAILABLE) = available
lambda(MOVING) = send
