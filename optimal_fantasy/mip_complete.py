def variables(model, data):
    pass


def constraints(model, variables, data):
    # Define shorthand
    P = data.players
    R = data.rounds
    T_t = data.trades_per_season
    T = data.trades_per_round
    # Model as per paper
    [(sum(t_in[p][r] for p in P for r in R) <= T) for r in R_]
    [(sum(t_in[p][r] for p in P) <= T[r]) for r in R]
    [(sum(x[p][q][r] - x[p][q][r-1] for q in p.Q]) <= t_in[p][r] - t_out[p][r] for p in P for r in R_]
    [(sum(c[p][r] for p in P) == 1) for r in R]
    [(c[p][r] <= sum(x[p][q][r] for q in Q_s[p])) for r in R for p in P]

def objective(model, variables, data):
    pass

