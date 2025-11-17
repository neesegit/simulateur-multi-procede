def create_subplot_layout(n_plots: int):
    if n_plots <= 2:
        return 1, n_plots
    elif n_plots <= 4:
        return 2, 2
    elif n_plots <= 6:
        return 2, 3
    else:
        return 3, 3

def hex_to_rgb(hex_color: str) -> str:
    """Convertit une couleur hex en RGB"""
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f'{r}, {g}, {b}'