from mip import Model, maximize
from mip import xsum as Σ 
from notation import shorthand, binary, continuous

def model(data):
    m = Model("Complete")
    # Notation
    P  = shorthand(data, "Set of players p ∈ P")
    P_ = shorthand(data, "Subset of players P_q ⊆ P eligible in position q ∈ Q")
    Q  = shorthand(data, "Set of positions q ∈ Q")
    Q_ = shorthand(data, "Subset of positions Q_p ⊆ Q eligible to player p ∈ P")
    T  = shorthand(data, "Trades allowed per season")
    T_ = shorthand(data, "Trades T_r allowed in round r ∈ R")
    R  = shorthand(data, "Set of rounds r ∈ R")
    C_ = shorthand(data, "Number of players required in position q ∈ Q")
    X_ = shorthand(data, "Number of scoring positions in round r ∈ R")
    B  = shorthand(data, "The starting budget to select team in first round")
    Ψ_ = shorthand(data, "Ψ_[p,r]: Points scored by player p ∈ P in round r ∈ R")
    v_ = shorthand(data, "v_[p,r]: Value of player p ∈ P in round r ∈ R")
    # Variables
    variables = {
                    # 1 iff player p ∈ P is in position q ∈ Q_p in round r ∈ R.
        "in team":  (x := {(p, q, r): binary(m)   for p in P for q in Q_[p] for r in R}),
                    # 1 iff the points of player p ∈ P in round r ∈ R count to the score.
        "scoring":  (x_bar := {(p, r) : binary(m) for p in P for r in R}),
                    # 1 iff player p ∈ P is captain in round r ∈ R.
        "captain":  (c := {(p, r): binary(m)      for p in P for r in R}),
                    # 1 iff player p ∈ P is traded into the team in round r ∈ R.
        "trade in": (t_in := {(p, r): binary(m)   for p in P for r in R}),
                    # 1 iff player p ∈ P is traded out of the team in round r ∈ R.
        "trade out":(t_out := {(p, r): binary(m)  for p in P for r in R}),
                    # remaining budget available in round r ∈ R.
        "budget":   (b := {r: continuous(m)       for r in R})
    }
    # Objective
    m.objective = maximize(
        # (1) Maximise the number of points scored by the team throughout the season.
        Σ(Σ(Ψ_[p, r]*(x_bar[p, r] + c[p, r]) for p in P)   for r in R)
        ) 
    # Constriants
    for constraint_set in (constraints := {
        # The number of trades across the season is less than or equal T.
        (2):   [Σ(t_in[p, r] for p in P for r in R[1:]) <= T],    
        # The number of trades per round is less than or requal to T_r.
        (3):   [Σ(t_in[p, r] for p in P) <= T_[r]         for r in R],   
        # Links player trade variables with whether they are in the team
        (4):   [Σ(x[p, q, r] - x[p, q, r-1] for q in Q_[p]) 
                    <= t_in[p, r] - t_out[p, r]           for p in P for r in R[1:]],    
        # Exactly one captain per round.
        (5):   [Σ(c[p, r] for p in P) == 1                for r in R],    
        # Captain must be a member of the team.
        (6):   [c[p, r] <= Σ(x[p, q, r] for q in Q_[p])   for r in R for p in P], 
        # Each position must contain a exact number of players.
        (7):   [Σ(x[p, q, r] for p in P_[q]) == C_[q]     for r in R for q in Q],
        # Each player can be in at most one position
        (8):   [Σ(x[p,q,r] for q in P_[q]) <= 1           for r in R for p in P],
        # Player must be in scoring position to score
        (9):   [x_bar[p, r] <= Σ(x[p,q,r] for q in P_[q]) for r in R for p in P],
        # The number of scoring players are limited each round
        (10):  [Σ(x_bar[p, r] for p in P) <= X_[r]        for r in R],
        # Remaining budget after selection of initial team
        (11):  [b[1] + Σ(v_[p,1]*x[p,q,1] for p in P for q in Q_[p]) == B],
        # Budget consistency constraints links budget and trades
        (12):  [b[r] == b[r-1] + 
                    Σ(v_[p,r]*(t_out[p,r]-t_in[p,r]) for p in P)  for r in R[1:]]
        }).values():
        for constraint in constraint_set:
            model += constraint
    return m, variables, constraints

