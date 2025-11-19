from typing import Optional, List

class PlotConfig:
    """Configuration d'un graphique"""
    def __init__(
            self,
            title: str,
            ylabel: str,
            plot_type: str,
            components: Optional[List[str]] = None,
            colors: Optional[List[str]] = None,
            show_setpoint: bool = False,
            setpoint_value: Optional[float] = None
    ):
        self.title = title
        self.ylabel = ylabel
        self.plot_type = plot_type
        self.components = components or []
        self.colors = colors or []
        self.show_setpoint = show_setpoint
        self.setpoint_value = setpoint_value

    def __repr__(self) -> str:
        return (
            f"<PlotConfig: title={self.title}, ylabel={self.ylabel}, plot_type={self.plot_type}, "
            f"components={self.components}, colors={self.colors}, show_setpoint={self.show_setpoint}, "
            f"setpoint_value={self.setpoint_value}>"
        )