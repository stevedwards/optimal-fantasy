from mip import BINARY, CONTINUOUS

def shorthand(data, description):
    return {
        "P": data["players"],
        "R": data["rounds"],
        "T_t": data["trades_per_season"],
        "T": data["trades_per_round"]
    }

def binary(m):
    return m.add_var(var_type=BINARY)

def continuous(m):
    return m.add_var(var_type=CONTINUOUS)
