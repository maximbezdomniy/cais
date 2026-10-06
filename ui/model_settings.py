import flet as ft
from core.api import ModelParams


class CustomSlider(ft.GestureDetector):
    def __init__(self, value: float, min_v: float, max_v: float, divisions: int, on_change):
        super().__init__()
        self.value = value
        self.min_v = min_v
        self.max_v = max_v
        self.divisions = divisions
        self.on_change_cb = on_change
        
        self.scale_min = 1.0
        self.sx = 1.0
        self.base_total_width = 248
        
        self.active_track = ft.Container(
            height=8, bgcolor="#303030", 
            border_radius=ft.border_radius.only(top_left=10, bottom_left=10, top_right=1, bottom_right=1),
            left=0, top=10,
        )
        self.inactive_track = ft.Container(
            height=8, bgcolor="#a9a9a9", 
            border_radius=ft.border_radius.only(top_right=10, bottom_right=10, top_left=1, bottom_left=1),
            right=0, top=10,
        )
        self.thumb = ft.Container(
            width=4, height=28, bgcolor="#303030", border_radius=10, top=0,
            animate_size=ft.Animation(150, "easeOut")
        )
        
        self.stack = ft.Stack(
            controls=[self.active_track, self.inactive_track, self.thumb],
            height=28,
        )
        
        self.content = self.stack
        self.on_pan_start = self._on_pan
        self.on_pan_update = self._on_pan
        self.on_pan_end = self._on_pan_end
        self.on_tap_down = self._on_pan
        self.on_tap_up = self._on_pan_end
        
        self.height = 28
        self._update_ui(False)
        
    def _get_pct(self):
        return (self.value - self.min_v) / (self.max_v - self.min_v)
        
    def _update_ui(self, pressed=False):
        sf = self.scale_min
        tw = self.base_total_width * self.sx
        self.stack.width = tw
        
        pct = max(0.0, min(1.0, self._get_pct()))
        x = pct * tw
        
        thumb_w = (2 if pressed else 4) * sf
        self.thumb.width = thumb_w
        self.thumb.height = 28 * sf
        self.thumb.left = x - (thumb_w / 2)
        self.thumb.border_radius = 10 * sf
        
        gap = 5 * self.sx
        active_w = max(0, x - (thumb_w / 2) - gap)
        inactive_w = max(0, tw - x - (thumb_w / 2) - gap)
        
        self.active_track.width = active_w
        self.active_track.height = 8 * sf
        self.active_track.top = 10 * sf
        self.active_track.border_radius = ft.border_radius.only(top_left=10*sf, bottom_left=10*sf, top_right=1*sf, bottom_right=1*sf)
        
        self.inactive_track.width = inactive_w
        self.inactive_track.height = 8 * sf
        self.inactive_track.top = 10 * sf
        self.inactive_track.border_radius = ft.border_radius.only(top_right=10*sf, bottom_right=10*sf, top_left=1*sf, bottom_left=1*sf)
        
        try:
            self.update()
        except RuntimeError:
            pass

    def _on_pan(self, e):
        tw = self.base_total_width * self.sx
        
        if hasattr(e, 'local_position'):
            x = e.local_position.x
        elif hasattr(e, 'local_delta'):
            pct = self._get_pct()
            current_x = pct * tw
            x = current_x + e.local_delta.x
        else:
            return
            
        x = max(0, min(tw, x))
        pct = x / tw
        
        if self.divisions:
            pct = round(pct * self.divisions) / self.divisions
            
        new_val = self.min_v + pct * (self.max_v - self.min_v)
        if new_val != self.value:
            self.value = new_val
            if self.on_change_cb:
                self.on_change_cb(self.value)
        self._update_ui(pressed=True)
        
    def _on_pan_end(self, e):
        self._update_ui(pressed=False)
        
    def update_layout(self, sx: float, scale_min: float):
        self.sx = sx
        self.scale_min = scale_min
        self.height = 28 * scale_min
        self._update_ui(False)


class CustomSwitch(ft.GestureDetector):
    def __init__(self, value=False, on_change=None):
        super().__init__()
        self.value = value
        self.on_change_cb = on_change
        
        self.scale_min = 1.0
        
        self.thumb = ft.Container(
            animate_position=ft.Animation(150, "easeOut"),
            animate_size=ft.Animation(150, "easeOut"),
            shape=ft.BoxShape.CIRCLE,
        )
        
        self.track = ft.Container(
            animate=ft.Animation(150, "easeOut"),
            content=ft.Stack([self.thumb]),
            border_radius=20,
        )
        self.content = self.track
        
        self.on_tap = self._handle_tap
        self.on_hover = self._handle_hover
        self.on_tap_down = self._handle_tap_down
        self.on_tap_up = self._handle_tap_up
        self.on_tap_cancel = self._handle_tap_up
        
        self._is_hover = False
        self._is_pressed = False
        self._update_state()

    def _update_state(self):
        sf = self.scale_min
        
        self.track.width = 36 * sf
        self.track.height = 22 * sf
        self.track.border_radius = 20 * sf
        
        if self.value:
            self.track.bgcolor = "#303030"
            self.track.border = None
            self.thumb.bgcolor = ft.Colors.WHITE
            if self._is_pressed:
                self.thumb.width = 18 * sf
                self.thumb.height = 18 * sf
                self.thumb.left = 16 * sf
                self.thumb.top = 2 * sf
            else:
                self.thumb.width = 16 * sf
                self.thumb.height = 16 * sf
                self.thumb.left = 17 * sf
                self.thumb.top = 3 * sf
        else:
            self.track.bgcolor = ft.Colors.with_opacity(0.1, "#303030") if self._is_hover or self._is_pressed else ft.Colors.TRANSPARENT
            self.track.border = ft.border.all(2 * sf, "#303030")
            self.thumb.bgcolor = "#303030"
            if self._is_pressed:
                self.thumb.width = 14 * sf
                self.thumb.height = 14 * sf
                self.thumb.left = 2 * sf
                self.thumb.top = 2 * sf
            else:
                self.thumb.width = 12 * sf
                self.thumb.height = 12 * sf
                self.thumb.left = 3 * sf
                self.thumb.top = 3 * sf
                
        try:
            self.update()
        except RuntimeError:
            pass
        
    def _handle_tap(self, e):
        self.value = not self.value
        self._update_state()
        if self.on_change_cb:
            self.on_change_cb(self.value)
            
    def _handle_hover(self, e):
        self._is_hover = e.data == "true"
        self._update_state()
        
    def _handle_tap_down(self, e):
        self._is_pressed = True
        self._update_state()
        
    def _handle_tap_up(self, e):
        self._is_pressed = False
        self._update_state()
        
    def update_layout(self, scale_min: float):
        self.scale_min = scale_min
        self._update_state()


class ModelSettingsPanel(ft.Container):
    """
    Правая панель настроек модели.
    """
    def __init__(self, params: ModelParams, on_close):
        super().__init__()

        self.params = params
        self.on_close_cb = on_close

        self.base_width = 350
        self.base_padding = 30
        self.base_text_h3 = 18
        self.base_text_p = 16
        self.base_text_small = 14
        self.base_text_field = 15

        def ls(size):
            return size * -0.04

        self.system_prompt_label = ft.Text("Системный промт", size=self.base_text_h3, color="#303030", weight=ft.FontWeight.W_400, style=ft.TextStyle(letter_spacing=ls(self.base_text_h3)))
        self.system_prompt_field = ft.TextField(
            hint_text='Можете задать "личность" AI',
            hint_style=ft.TextStyle(color=ft.Colors.with_opacity(0.5, "#303030"), size=self.base_text_p, letter_spacing=ls(self.base_text_p)),
            multiline=True,
            min_lines=2,
            max_lines=4,
            border_radius=10,
            border_color=ft.Colors.with_opacity(0.3, "#303030"),
            focused_border_color="#303030",
            border_width=1,
            color="#303030",
            text_style=ft.TextStyle(size=self.base_text_field, letter_spacing=ls(self.base_text_field)),
            bgcolor=ft.Colors.with_opacity(0.08, "#d9d9d9"),
            on_change=lambda e: setattr(params, "system_prompt", e.control.value),
            value=params.system_prompt,
        )

        self.char_label = ft.Text("Характер", size=self.base_text_h3, color="#303030", weight=ft.FontWeight.W_400, style=ft.TextStyle(letter_spacing=ls(self.base_text_h3)))
        self.sliders = [] 

        self.temp_slider_col = self._create_slider_row("Температура", params.temperature, 0.0, 2.0, 40, lambda v: setattr(params, "temperature", v))
        self.rep_slider_col = self._create_slider_row("Штраф за повторения", params.repetition_penalty, 0.0, 2.0, 40, lambda v: setattr(params, "repetition_penalty", v))
        self.top_p_slider_col = self._create_slider_row("Порог выборки", params.top_p, 0.0, 1.0, 20, lambda v: setattr(params, "top_p", v))

        self.limits_label = ft.Text("Лимиты и скорость", size=self.base_text_h3, color="#303030", weight=ft.FontWeight.W_400, style=ft.TextStyle(letter_spacing=ls(self.base_text_h3)))
        self.max_tok_slider_col = self._create_slider_row("Макс. количество токенов", params.max_tokens / 4096, 0.0, 1.0, 20, lambda v: setattr(params, "max_tokens", int(v * 4096) or 1))

        self.stream_label = ft.Text("Потоковая передача", size=self.base_text_p, color="#303030", expand=True, style=ft.TextStyle(letter_spacing=ls(self.base_text_p)))
        self.stream_toggle = CustomSwitch(
            value=params.stream,
            on_change=lambda v: setattr(params, "stream", v),
        )
        self.stream_row = ft.Row(
            controls=[self.stream_label, self.stream_toggle],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self.div1 = ft.Divider(height=1, color=ft.Colors.with_opacity(0.15, "#303030"))
        self.div2 = ft.Divider(height=1, color=ft.Colors.with_opacity(0.15, "#303030"))

        self.panel_content = ft.Column(
            controls=[
                self.system_prompt_label,
                self.system_prompt_field,
                self.div1,
                self.char_label,
                self.temp_slider_col,
                self.rep_slider_col,
                self.top_p_slider_col,
                self.div2,
                self.limits_label,
                self.max_tok_slider_col,
                self.stream_row,
            ],
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
        )

        self.width = self.base_width
        self.bgcolor = ft.Colors.WHITE
        self.border = ft.border.all(1, "#303030")
        self.border_radius = 28
        self.shadow = ft.BoxShadow(
            blur_radius=8,
            spread_radius=0,
            color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
            offset=ft.Offset(0, 3),
        )
        self.padding = ft.padding.symmetric(vertical=20, horizontal=self.base_padding)
        self.content = self.panel_content
        self.animate_position = ft.Animation(280, ft.AnimationCurve.EASE_OUT_CUBIC)
        self.right = -400  
        self.top = 30
        self.bottom = 30
        self._is_open = False

    def _create_slider_row(self, label: str, value: float, min_v: float, max_v: float, divisions: int, on_change) -> ft.Column:
        label_text = ft.Text(label, size=self.base_text_p, color="#303030", style=ft.TextStyle(letter_spacing=self.base_text_p * -0.04))
        val_text = ft.Text(f"{value:.1f}", size=self.base_text_p, color="#303030", width=25, style=ft.TextStyle(letter_spacing=self.base_text_p * -0.04))

        def _on_change(val):
            val_text.value = f"{val:.1f}"
            val_text.update()
            on_change(val)

        slider = CustomSlider(
            value=value,
            min_v=min_v,
            max_v=max_v,
            divisions=divisions,
            on_change=_on_change,
        )
        
        self.sliders.append({"label": label_text, "val": val_text, "slider": slider})

        return ft.Column(
            controls=[
                label_text,
                ft.Row(
                    controls=[slider, val_text],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
            ],
            spacing=4,
        )

    def update_layout(self, sx: float, sy: float):
        scale_min = min(sx, sy)
        self.width = self.base_width * sx
        self.border_radius = 28 * scale_min
        self.padding = ft.padding.symmetric(vertical=20 * sy, horizontal=self.base_padding * sx)
        self.top = 30 * sy
        self.bottom = 50 * sy
        
        def ls(size): return size * -0.04
        
        self.system_prompt_label.size = self.base_text_h3 * scale_min
        self.system_prompt_label.style = ft.TextStyle(letter_spacing=ls(self.system_prompt_label.size))
        
        self.system_prompt_field.text_style.size = self.base_text_field * scale_min
        self.system_prompt_field.text_style.letter_spacing = ls(self.system_prompt_field.text_style.size)
        self.system_prompt_field.hint_style.size = self.base_text_p * scale_min
        self.system_prompt_field.hint_style.letter_spacing = ls(self.system_prompt_field.hint_style.size)
        self.system_prompt_field.border_radius = 10 * scale_min

        self.char_label.size = self.base_text_h3 * scale_min
        self.char_label.style = ft.TextStyle(letter_spacing=ls(self.char_label.size))
        
        self.limits_label.size = self.base_text_h3 * scale_min
        self.limits_label.style = ft.TextStyle(letter_spacing=ls(self.limits_label.size))
        
        self.stream_label.size = self.base_text_p * scale_min
        self.stream_label.style = ft.TextStyle(letter_spacing=ls(self.stream_label.size))

        for s_refs in self.sliders:
            sz_p = self.base_text_p * scale_min
            s_refs["label"].size = sz_p
            s_refs["label"].style = ft.TextStyle(letter_spacing=ls(sz_p))
            
            s_refs["val"].size = sz_p
            s_refs["val"].style = ft.TextStyle(letter_spacing=ls(sz_p))
            s_refs["val"].width = 25 * sx
            
            s_refs["slider"].update_layout(sx, scale_min)

        self.stream_toggle.update_layout(scale_min)
        self.panel_content.spacing = 14 * sy

        if self._is_open:
            self.right = 30 * sx
        else:
            self.right = - (self.base_width * sx + 50)
            
        self.update()

    def show(self, sx: float = 1.0):
        self._is_open = True
        self.right = 30 * sx
        self.update()

    def hide(self, sx: float = 1.0):
        self._is_open = False
        self.right = - (self.base_width * sx + 50)
        self.update()
