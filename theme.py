class Theme:
    def __init__(self):
        self.current_theme = "dark"
        
    def toggle(self):
        pass
    
    @property
    def colors(self):
        if self.current_theme == "light":
            return {
                "bg": (240, 240, 240),
                "text": (0, 0, 0),
                "button": (0, 100, 200),
                "button_hover": (100, 200, 255),
                "button_text": (255, 255, 255),
                "panel_bg": (200, 200, 200, 30),
                "field_border": (0, 0, 0),
                "overlay": (0, 0, 0),
                "title": (0, 100, 200),
                "error_bg": (255, 0, 0),
                "error_text": (255, 255, 255),
                "disabled": (150, 150, 150),
                "disabled_text": (100, 100, 100),
                "ship": (0, 255, 0),
                "hit": (255, 0, 0),
                "miss": (0, 0, 0),
                "destroyed": (255, 165, 0),
                "preview": (0, 255, 0, 100),
                "gold": (255, 215, 0),
                "gray": (200, 200, 200),
                "dark_gray": (100, 100, 100)
            }
        else:
            return {
                "bg": (30, 30, 30),
                "text": (220, 220, 220),
                "button": (0, 80, 160),
                "button_hover": (0, 120, 200),
                "button_text": (255, 255, 255),
                "panel_bg": (60, 60, 60, 30),
                "field_border": (100, 100, 100),
                "overlay": (255, 255, 255),
                "title": (100, 180, 255),
                "error_bg": (180, 0, 0),
                "error_text": (255, 255, 255),
                "disabled": (60, 60, 60),
                "disabled_text": (120, 120, 120),
                "ship": (0, 200, 0),
                "hit": (220, 0, 0),
                "miss": (150, 150, 150),
                "destroyed": (200, 120, 0),
                "preview": (0, 200, 0, 100),
                "gold": (200, 180, 0),
                "gray": (60, 60, 60),
                "dark_gray": (80, 80, 80)
            }

theme = Theme()