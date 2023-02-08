X = { {input_tray}, lock_output_by_<>], [unlock_output_by_<>] }
Y = { {output_tray[output_id]}, [lock_relatives] }
S = { RL[n], RU[n], QL[n], QU[n], [], [MoveRest], [MoveRequest] }
s0 = Rest
ta(Rest) = +
ta(Request) = <>


X = { [lock_output_by_<>], [unlock_output_by_<>] }
Y = { [lock_relatives] }
S = { Rest, Request, [Move], [MoveRest], [MoveRequest] }
s0 = Rest
ta(Rest) = +
ta(Request) = <>

