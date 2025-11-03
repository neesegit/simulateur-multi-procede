def create_subplot_layout(n_plots: int):
    if n_plots <= 2:
        return 1, n_plots
    elif n_plots <= 4:
        return 2, 2
    elif n_plots <= 6:
        return 2, 3
    else:
        return 3, 3
