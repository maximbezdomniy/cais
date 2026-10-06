import flet as ft
from core.api import GigaChatManager
from ui.message_bubble import MessageBubble
from ui.side_menu import SideMenu
from ui.model_settings import ModelSettingsPanel
from ui.app_settings import AppSettingsPanel
from gigachat.models import MessagesRole
import asyncio

# Figma canvas size
FIGMA_W = 1920
FIGMA_H = 1080


def _icon_btn(icon_src: str, tooltip: str, on_click=None) -> ft.Container:
    """42×42px icon button matching Figma: border rgba(193,193,193,0.8), radius 10px."""
    return ft.Container(
        content=ft.Image(src=icon_src, width=22, height=22, color="#303030"),
        width=42,
        height=42,
        border=ft.border.all(1, ft.Colors.with_opacity(0.8, "#C1C1C1")),
        border_radius=10,
        alignment=ft.Alignment.CENTER,
        tooltip=tooltip,
        ink=True,
        on_click=on_click,
    )


class ChatView(ft.View):
    def __init__(self, page: ft.Page):
        super().__init__(
            route="/chat",
            bgcolor="#FDFDFE",
            padding=0,
        )

        # ── State
        self._left_open = False
        self._right_open = False
        self._chat_titles: list[str] = []  # saved chat titles for history

        manager: GigaChatManager = getattr(page, "api_manager", None)
        current_model = manager.params.model if manager else "GigaChat"

        # ── Attached Files List
        self.attached_files = []
        self.files_row = ft.Row(spacing=8, scroll=ft.ScrollMode.AUTO, visible=False)

        # ── Header buttons
        self.menu_btn = _icon_btn("assets/icons/menu_open.svg", "Меню чатов", self._toggle_left)
        self.new_chat_btn = _icon_btn("assets/icons/edit_square.svg", "Новый чат", self._new_chat)
        self.settings_btn = _icon_btn("assets/icons/tune.svg", "Настройки модели", self._toggle_right)

        # Logo "CAIS" — text-based, no external file dependency
        self.logo = ft.Text(
            "CAIS",
            size=22,
            weight=ft.FontWeight.W_600,
            color="#000000",
            animate_opacity=50,
        )

        self.left_header_buttons = ft.Container(
            content=ft.Row(
                controls=[self.menu_btn, self.new_chat_btn],
                # spacing is set in _layout
            ),
            left=0,
            top=0,
            animate_position=ft.Animation(280, ft.AnimationCurve.EASE_OUT_CUBIC),
        )

        self.right_header_buttons = ft.Container(
            content=self.settings_btn,
            right=0,
            top=0,
            animate_position=ft.Animation(280, ft.AnimationCurve.EASE_OUT_CUBIC),
        )

        header = ft.Container(
            content=ft.Stack(
                controls=[
                    # Center: logo
                    ft.Container(
                        content=self.logo,
                        alignment=ft.Alignment(0, 0),
                        top=0, left=0, right=0, bottom=0,
                    ),
                    # Left: menu and new chat
                    self.left_header_buttons,
                    # Right: settings button
                    self.right_header_buttons,
                ],
                height=42,
            ),
            padding=ft.padding.only(left=30, right=30, top=30),
            # bgcolor removed so gradient is visible
        )

        # ── Welcome / empty state
        # Figma: "Привет!" 36px tracking -1.44, "Чем займемся сегодня?" 64px tracking -2.56
        self.welcome_hello = ft.Text("Привет!", size=36, color="#000000", weight=ft.FontWeight.W_400)
        self.welcome_what = ft.Text("Чем займемся сегодня?", size=64, color="#000000", weight=ft.FontWeight.W_400, no_wrap=False)
        self.welcome_state = ft.Container(
            content=ft.Column(
                controls=[
                    self.welcome_hello,
                    self.welcome_what,
                ],
                spacing=8,
            ),
            expand=True,
            alignment=ft.Alignment(0.0, -1.0),
        )

        # ── Chat messages list
        # Ширина контента ограничивается через горизонтальные отступы, которые обновляются в _layout().
        # Нижний отступ равен высоте панели ввода + немного запаса, чтобы текст плавно скрывался под панелью.
        self.chat_list = ft.ListView(
            expand=True,
            spacing=0,
            auto_scroll=True,
            padding=ft.padding.only(left=430, right=430, top=120, bottom=200),
            on_scroll=self._on_chat_scroll,
        )

        # ── Input panel (Figma canvas: 1920×1080, panel: 1060×148px)
        self._right_open = False
        self._is_generating = False
        self._is_recording = False
        self._stt_stop_requested = False
        self._stop_event = asyncio.Event()
        self._chat_titles = []  # track titles to avoid duplicates in sidebars to content; 30px gaps come from panel padding
        # content_padding only handles left/right indent of the cursor
        self.prompt_input = ft.TextField(
            hint_text="Спросите ГигаЧат",
            hint_style=ft.TextStyle(color="#A8A8A8", size=22, weight=ft.FontWeight.W_400),
            border=ft.InputBorder.NONE,
            multiline=True,
            min_lines=1,
            max_lines=4,
            color="#303030",
            text_size=22,
            text_style=ft.TextStyle(size=22, weight=ft.FontWeight.W_400, letter_spacing=-0.44),
            content_padding=0,
            dense=True,
            on_submit=self.on_send,
            shift_enter=True,
            on_change=self._on_input_change,
        )

        # ── Model selector — Figma: 93×32px pill, border #303030 1px, radius 30px
        _MODEL_LABELS = {"GigaChat": "Lite", "GigaChat-Pro": "Pro", "GigaChat-Max": "Max"}
        current_label = _MODEL_LABELS.get(current_model, "Lite")
        self._model_popup_open = False

        self.model_text = ft.Text(
            current_label, size=20, color="#303030",
            weight=ft.FontWeight.W_500, no_wrap=True,
        )
        self._model_arrow = ft.Icon(
            ft.Icons.KEYBOARD_ARROW_DOWN, size=26, color="#303030",
            animate_rotation=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
        )
        # The pill button
        self._model_btn_bg = ft.Container(
            content=ft.Row(
                controls=[self.model_text, self._model_arrow],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                tight=True,
            ),
            border=ft.border.all(1, "#303030"),
            border_radius=30,
            width=93, height=32,
            alignment=ft.Alignment(0, 0),
            padding=ft.padding.symmetric(horizontal=10),
            bgcolor=None,
            animate=ft.Animation(150, ft.AnimationCurve.EASE_IN_OUT),
        )
        self.model_selector = ft.GestureDetector(
            content=self._model_btn_bg,
            on_tap=self._toggle_model_popup,
            mouse_cursor=ft.MouseCursor.CLICK,
        )

        # Floating popup — Figma: 113×120px, white, border #303030, radius 16px
        _MODELS = [
            ("Lite", "GigaChat"),
            ("Pro",  "GigaChat-Pro"),
            ("Max",  "GigaChat-Max"),
        ]
        self._model_popup_items = []
        for label, key in _MODELS:
            item_text = ft.Text(
                label, size=20, color="#303030",
                weight=ft.FontWeight.W_500, no_wrap=True,
                text_align=ft.TextAlign.CENTER,
            )
            item = ft.Container(
                content=item_text,
                data=key,
                padding=ft.padding.symmetric(horizontal=20, vertical=6),
                border_radius=8,
                bgcolor=ft.Colors.WHITE,
                on_click=self._on_model_item_click,
                on_hover=self._on_model_item_hover,
                ink=False,
                alignment=ft.Alignment(0, 0),
            )
            self._model_popup_items.append(item)

        self._model_popup = ft.Container(
            content=ft.Column(
                controls=self._model_popup_items,
                spacing=4,
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, "#303030"),
            border_radius=16,
            padding=ft.padding.symmetric(vertical=10, horizontal=6),
            shadow=ft.BoxShadow(blur_radius=8, spread_radius=0,
                                color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
                                offset=ft.Offset(0, 3)),
            visible=False,
        )


        # ── Action button (Figma: 32×32px, 3 states)
        self._action_icon = ft.Image(
            src="assets/icons/mic.svg", width=32, height=32, fit=ft.BoxFit.CONTAIN,
        )
        self._action_icon_container = ft.Container(
            content=self._action_icon, 
            width=40, 
            height=40,
            border_radius=20,
            alignment=ft.Alignment(0, 0),
            on_click=self._on_action_btn,
            on_hover=self._on_action_hover,
        )
        self.action_btn = self._action_icon_container

        # ── Icons with refs for scaling
        self._attach_icon = ft.Image(src="assets/icons/attach_file.svg", width=32, height=32, fit=ft.BoxFit.CONTAIN)
        self._attach_icon_container = ft.Container(content=self._attach_icon, width=32, height=32)
        attach_btn = ft.GestureDetector(
            content=self._attach_icon_container, on_tap=self._on_attach_click,
            mouse_cursor=ft.MouseCursor.CLICK,
        )
        self._language_icon = ft.Image(src="assets/icons/language.svg", width=32, height=32, fit=ft.BoxFit.CONTAIN)
        self._language_icon_container = ft.Container(content=self._language_icon, width=32, height=32)
        language_btn = ft.GestureDetector(
            content=self._language_icon_container,
            mouse_cursor=ft.MouseCursor.CLICK, tooltip="Веб-поиск",
        )

        # ── Clusters (no extra padding — handled by panel outer padding)
        self._left_cluster = ft.Row(
            controls=[attach_btn, language_btn, self.model_selector],
            spacing=20,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self._right_cluster = ft.Row(
            controls=[self.action_btn],
            spacing=20,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # ── Bottom bar — NO extra padding, outer panel handles all spacing
        self._bottom_bar = ft.Container(
            content=ft.Row(
                controls=[
                    self._left_cluster,
                    ft.Container(expand=True),
                    self._right_cluster,
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        # ── Files section
        self._files_section = ft.Container(content=self.files_row)

        # ── Inner column: [files?] + text + [gap] + toolbar
        # The 30px equal gaps (top/bottom/between-text-and-bar) come
        # ENTIRELY from input_panel.padding — not from children.
        self._inner_gap = ft.Container(height=16)
        self._inner_col = ft.Column(
            controls=[
                self.prompt_input,
                self._inner_gap,   # gap between text and icons row
                self._bottom_bar,
            ],
            spacing=0,
            tight=True,
        )

        # ── Whole input panel — padding carries the 30px equal gaps
        # Figma: top=30px, bottom=30px, left is handled by text content_padding
        self.input_panel = ft.Container(
            content=self._inner_col,
            bgcolor="#FDFDFE",
            border=ft.border.all(1, "#303030"),
            border_radius=28,
            width=820,
            padding=ft.padding.symmetric(vertical=30, horizontal=30),
            shadow=ft.BoxShadow(
                blur_radius=40, spread_radius=-5,
                color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
                offset=ft.Offset(0, 3),
            ),
        )

        # ── Wrapper for Glow and Panel
        # In Figma, glow_rect.png is 1360x371, while the panel is 1060x148.
        # ── Bottom Mask to hide text scrolling below the panel
        self.bottom_mask = ft.Container(bgcolor="#FDFDFE")

        # ── Glow Image
        self.glow_image = ft.Image(src="assets/glow_rect.png", fit=ft.BoxFit.FILL)
        self.glow_container = ft.Container(content=self.glow_image)

        # ── Input Panel Container (to position absolutely)
        self.input_panel_container = ft.Container(
            content=ft.Column(
                controls=[
                    self._files_section,
                    self.input_panel,
                ],
                spacing=0,
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.START,
            )
        )

        # ── Body stack: welcome OR chat list
        body = ft.Stack(
            controls=[self.welcome_state, self.chat_list],
            expand=True,
        )

        # ── Top Gradient to hide scrolling text smoothly
        # Делаем верхние 40% (около 48px) полностью белыми, чтобы текст не просвечивал под лого при быстром скролле
        self.top_gradient = ft.Container(
            height=120,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(0, -1),
                end=ft.Alignment(0, 1),
                colors=["#FDFDFE", "#FDFDFE", ft.Colors.with_opacity(0.0, "#FDFDFE")],
                stops=[0.0, 0.4, 1.0],
            ),
        )

        # ── Main layout (Stack — layered to hide text properly)
        main_stack = ft.Stack(
            controls=[
                # Layer 0: Chat content (background)
                ft.Container(content=body, expand=True),
                # Layer 1: Top gradient (hides scrolling text at the top)
                ft.Container(content=self.top_gradient, top=0, left=0, right=0),
                # Layer 2: Bottom mask (hides text that scrolls below the panel)
                self.bottom_mask,
                # Layer 3: Glow image (centered behind panel)
                self.glow_container,
                # Layer 4: Header (Logo + Menus)
                ft.Container(content=header, top=0, left=0, right=0),
                # Layer 5: Input Panel (at the bottom)
                self.input_panel_container,
            ],
            expand=True,
        )

        # ── Overlay menus (absolute over main)
        self.left_menu = SideMenu(
            on_close=self._toggle_left,
            on_new_chat=self._new_chat,
            on_chat_select=self._on_chat_select,
            on_settings=self._toggle_app_settings,
            chat_history=manager.get_sessions_list() if manager else [],
        )
        self.right_menu = ModelSettingsPanel(
            params=manager.params if manager else __import__("core.api", fromlist=["ModelParams"]).ModelParams(),
            on_close=self._toggle_right,
        )

        # ── Root Stack: main content + overlay panels + model popup
        # ── App Settings (Floating Window -> Modal Dialog)
        self.app_settings = AppSettingsPanel(page, on_close=self._on_app_settings_close)
        
        self.settings_dialog = ft.AlertDialog(
            content=self.app_settings,
            content_padding=0,
            shape=ft.RoundedRectangleBorder(radius=20),
            bgcolor=ft.Colors.TRANSPARENT,
        )
        page.overlay.append(self.settings_dialog)

        root = ft.Stack(
            controls=[
                ft.Container(content=main_stack, expand=True),
                self.left_menu,
                self.right_menu,
                self._model_popup,
            ],
            expand=True,
        )

        self.controls = [root]

    # ── Layout helpers ──────────────────────────────────────────────────────

    def _on_chat_scroll(self, e: ft.OnScrollEvent):
        # e.pixels indicates how far we've scrolled.
        # Hide logo when scrolled down
        try:
            if e.pixels > 20:
                if self.logo.opacity != 0:
                    self.logo.opacity = 0
                    self.logo.update()
            else:
                if self.logo.opacity != 1:
                    self.logo.opacity = 1
                    self.logo.update()
        except RuntimeError:
            pass

    def _get_scale(self):
        w  = self.page.width  or 1200
        h  = self.page.height or 800
        sx = max(0.65, w / 1920.0)
        sy = max(0.65, h / 1080.0)
        return sx, sy, min(sx, sy)

    def _wrap_bubble(self, bubble: MessageBubble, role) -> ft.Control:
        """Wrap a bubble in proper alignment container.
        User: right-aligned text bubble, then attachment cards below.
        AI:   returned directly (expands full width).
        """
        if role == MessagesRole.USER:
            items = [
                ft.Row(controls=[bubble], alignment=ft.MainAxisAlignment.END),
            ]
            attachments = bubble.make_attachments_row()
            if attachments:
                items.append(attachments)
            return ft.Column(controls=items, spacing=0, tight=True)
        return bubble


    def did_mount(self):
        self._layout()
        self.page.on_resize = self._on_resize

    def will_unmount(self):
        self.page.on_resize = None

    def _on_resize(self, e):
        self._layout()
        self.update()

    def _layout(self):
        w = self.page.width or 1200
        h = self.page.height or 800

        # Base scale factors
        sx = max(0.65, w / 1920.0)
        sy = max(0.65, h / 1080.0)
        scale_min = min(sx, sy)

        # ── Panel exact proportions (Figma: 1060×148)
        panel_w = round(1060 * sx)
        panel_h = round(148 * sy)
        
        self.input_panel.width = panel_w
        self.input_panel_container.content.width = panel_w
        self.input_panel.border_radius = round(28 * scale_min)

        # ── Positioning panel at 50px from bottom
        panel_bottom = round(50 * sy)
        self.input_panel_container.bottom = panel_bottom
        self.input_panel_container.left = 0
        self.input_panel_container.right = 0
        self.input_panel_container.alignment = ft.Alignment(0, 0)

        # ── Positioning glow perfectly behind panel
        glow_w = round(1360 * sx)
        glow_h = round(371 * sy)
        # Свечение должно быть немного выше панели ввода (bottom = 0 поднимает его)
        glow_bottom = 0
        
        self.glow_container.bottom = glow_bottom
        self.glow_container.left = 0
        self.glow_container.right = 0
        self.glow_container.alignment = ft.Alignment(0, 0)
        self.glow_image.width = glow_w
        self.glow_image.height = glow_h

        # ── Bottom mask to hide text
        self.bottom_mask.bottom = 0
        self.bottom_mask.left = 0
        self.bottom_mask.right = 0
        self.bottom_mask.height = panel_bottom + (panel_h // 2)

        # ── Font sizes & Inner layout (Figma: 22px for text, 20px for labels)
        pad_x = round(30 * sx)
        pad_y = round(30 * sy)
        txt_size  = round(22 * scale_min)
        lbl_size  = round(20 * scale_min)

        # Text field
        self.prompt_input.width = panel_w - (pad_x * 2)
        self.prompt_input.text_size = txt_size
        self.prompt_input.hint_style = ft.TextStyle(
            color="#A8A8A8", size=txt_size, weight=ft.FontWeight.W_400, letter_spacing=txt_size * -0.04
        )
        self.prompt_input.text_style = ft.TextStyle(
            size=txt_size, weight=ft.FontWeight.W_400, letter_spacing=txt_size * -0.04,
        )
        self.prompt_input.content_padding = 0

        # Labels
        self.model_text.size = lbl_size
        self.model_text.style = ft.TextStyle(letter_spacing=lbl_size * -0.02)

        # Welcome text
        self.welcome_hello.size = round(36 * scale_min)
        self.welcome_hello.style = ft.TextStyle(letter_spacing=round(36 * scale_min * -0.04))
        self.welcome_what.size = round(64 * scale_min)
        self.welcome_what.style = ft.TextStyle(letter_spacing=round(64 * scale_min * -0.04))
        
        self.welcome_state.padding = ft.padding.only(
            top=round(407 * sy)
        )

        # Logo (text)
        self.logo.size = round(22 * scale_min)

        # ── Icon sizes (Figma: 32px)
        icon_sz = round(32 * scale_min)
        action_bg_sz = round(40 * scale_min)
        
        for img, ctr in [
            (self._attach_icon,   self._attach_icon_container),
            (self._language_icon, self._language_icon_container),
        ]:
            img.width  = icon_sz
            img.height = icon_sz
            ctr.width  = icon_sz
            ctr.height = icon_sz
            ctr.border_radius = icon_sz / 2

        self._action_icon.width = icon_sz
        self._action_icon.height = icon_sz
        self._action_icon_container.width = action_bg_sz
        self._action_icon_container.height = action_bg_sz
        self._action_icon_container.border_radius = action_bg_sz / 2


        # ── Cluster spacing (Figma: gap=20px)
        gap = round(20 * sx)
        self._left_cluster.spacing  = gap
        self._right_cluster.spacing = gap

        # ── Gap between text field and toolbar
        self._inner_gap.height = pad_y

        # ── Panel outer padding (handles all inner spacing)
        self.input_panel.padding = ft.padding.symmetric(vertical=pad_y, horizontal=pad_x)
        self._bottom_bar.padding = 0

        # ── Files section padding
        self._files_section.padding = ft.padding.only(bottom=round(12 * sy))

        # ── Chat list padding — центрирование через боковые отступы
        panel_w = round(1060 * sx)
        side_pad = max(0, (w - panel_w) // 2)

        # Отступ снизу: 50px над панелью + высота панели + 50px под панелью = panel_bottom + panel_h + 50*sy
        bottom_pad = panel_bottom + panel_h + round(50 * sy)
        self.chat_list.padding = ft.padding.only(
            left   = side_pad,
            right  = side_pad,
            top    = round(112 * sy),           # 62px лого + 50px отступ
            bottom = bottom_pad,
        )

        # ── Welcome title sizes
        for ctrl in self.welcome_state.content.controls:
            if hasattr(ctrl, "value"):
                if "Привет" in ctrl.value:
                    ctrl.size = round(36 * scale_min)
                else:
                    ctrl.size = round(64 * scale_min)
                ctrl.style = ft.TextStyle(letter_spacing=ctrl.size * -0.04)

        # ── Top bar buttons scaling
        try:
            self.left_header_buttons.content.spacing = round(10 * sx)
            if self._left_open:
                self.left_header_buttons.left = round(380 * sx)
            else:
                self.left_header_buttons.left = 0
            self.left_header_buttons.update()

            if self._right_open:
                self.right_header_buttons.right = round(380 * sx)
            else:
                self.right_header_buttons.right = 0
            self.right_header_buttons.update()

            btn_sz = round(42 * scale_min)
            icon_sz2 = round(22 * scale_min)
            for btn in [self.menu_btn, self.new_chat_btn, self.settings_btn]:
                btn.width = btn_sz
                btn.height = btn_sz
                btn.border_radius = round(10 * scale_min)
                btn.content.width = icon_sz2
                btn.content.height = icon_sz2
            self.left_menu.update_layout(sx, sy)
            self.right_menu.update_layout(sx, sy)
        except Exception:
            pass

        # ── Model selector pill scaling
        try:
            btn_w = round(93 * sx)
            btn_h = round(32 * sy)
            self._model_btn_bg.width = btn_w
            self._model_btn_bg.height = btn_h
            self._model_arrow.size = round(26 * scale_min)
            self.model_text.size = round(20 * scale_min)
            self.model_text.style = ft.TextStyle(letter_spacing=round(20 * scale_min * -0.02))

            self._model_popup.border_radius = round(16 * scale_min)
            # Y: bottom of panel area, above the panel
            self._model_popup.bottom = panel_bottom + panel_h + round(12 * sy)
            # X: aligned to the left cluster start + attach_icon(32) + gap(20) + language_icon(32) + gap(20)
            popup_left = side_pad + pad_x + round((32 + 20 + 32 + 20) * sx)
            self._model_popup.left = popup_left
            # Scale popup item text
            for item in self._model_popup_items:
                item.content.size = round(20 * scale_min)
                item.padding = ft.padding.symmetric(
                    horizontal=round(20 * sx), vertical=round(6 * sy)
                )
        except Exception:
            pass

        # Force update on all changed controls
        try:
            self.input_panel.update()
            self.prompt_input.update()
            self._bottom_bar.update()
            self._left_cluster.update()
            self._right_cluster.update()
        except Exception:
            pass  # not yet mounted — initial _layout call before controls are added to page


    # ── Toggle handlers ─────────────────────────────────────────────────────

    def _on_app_settings_close(self):
        self.settings_dialog.open = False
        try:
            self.settings_dialog.update()
        except Exception:
            pass

    def _toggle_app_settings(self, e=None):
        self.settings_dialog.open = True
        try:
            self.settings_dialog.update()
        except Exception:
            pass

    def _toggle_left(self, e=None):
        self._left_open = not self._left_open
        self._layout()
        if self._left_open:
            self.left_menu.show()
        else:
            self.left_menu.hide()

    def _toggle_right(self, e=None):
        self._right_open = not self._right_open
        self._layout()
        if self._right_open:
            self.right_menu.show()
        else:
            self.right_menu.hide()

    def _toggle_model_popup(self, e=None):
        """Toggle the floating model selection popup and rotate the arrow."""
        self._model_popup_open = not self._model_popup_open
        self._model_popup.visible = self._model_popup_open
        # Rotate arrow 180° when open
        self._model_arrow.rotate = 3.14159 if self._model_popup_open else 0
        try:
            self._model_popup.update()
            self._model_arrow.update()
        except Exception:
            pass

    def _on_action_hover(self, e):
        """Highlight action button background on hover."""
        hovered = str(e.data).lower() == "true"
        e.control.bgcolor = "#EFEFEF" if hovered else None
        try:
            e.control.update()
        except Exception:
            pass

    def _on_model_item_hover(self, e):
        """Highlight item background on hover."""
        hovered = str(e.data).lower() == "true"
        e.control.bgcolor = "#EFEFEF" if hovered else ft.Colors.WHITE
        try:
            e.control.update()
        except Exception:
            pass

    def _on_model_item_click(self, e):
        """Select model and close popup."""
        _MODEL_LABELS = {"GigaChat": "Lite", "GigaChat-Pro": "Pro", "GigaChat-Max": "Max"}
        model_name = e.control.data
        manager: GigaChatManager = getattr(self.page, "api_manager", None)
        if manager:
            manager.params.model = model_name
        self.model_text.value = _MODEL_LABELS.get(model_name, model_name)
        # Close popup
        self._model_popup_open = False
        self._model_popup.visible = False
        self._model_arrow.rotate = 0
        try:
            self.model_text.update()
            self._model_popup.update()
            self._model_arrow.update()
        except Exception:
            pass

    def _change_model(self, e):
        _MODEL_LABELS = {"GigaChat": "Lite", "GigaChat-Pro": "Pro", "GigaChat-Max": "Max"}
        manager: GigaChatManager = getattr(self.page, "api_manager", None)
        model_name = e.control.data
        if manager:
            manager.params.model = model_name
        self.model_text.value = _MODEL_LABELS.get(model_name, model_name)
        self.model_text.update()

    def _on_input_change(self, e):
        """Switch action button between Mic and Send based on input content."""
        if self._is_generating:
            return
        has_text = bool(self.prompt_input.value and self.prompt_input.value.strip())
        self._action_icon.src = self._ICON_SEND if has_text else self._ICON_MIC
        self._action_icon.update()

    async def _on_action_btn(self, e):
        """Action button handler: Mic / Send / Stop depending on state."""
        if self._is_generating:
            # Stop state — set event
            self._stop_event.set()
            return
        has_text = bool(self.prompt_input.value and self.prompt_input.value.strip())
        if has_text:
            await self.on_send(e)
        else:
            await self._start_voice_input()

    async def _start_voice_input(self):
        """Handle STT using speech_recognition with toggle-to-stop."""
        if self._is_recording:
            # Second click — request stop
            self._stt_stop_requested = True
            # Visual feedback is immediate
            self._action_icon.src = self._ICON_MIC
            self.prompt_input.hint_text = "Спросите ГигаЧат"
            self.prompt_input.disabled = False
            self.page.update()
            return
            
        import speech_recognition as sr
        import asyncio

        self._is_recording = True
        self._stt_stop_requested = False
        
        # Change icon to active state
        self._action_icon.src = self._ICON_MIC_ACTIVE
        old_hint = self.prompt_input.hint_text
        self.prompt_input.hint_text = "Слушаю... (говорите)"
        self.prompt_input.disabled = True
        self.page.update()

        def _recognize():
            recognizer = sr.Recognizer()
            try:
                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    # We check flag BEFORE blocking listen
                    if self._stt_stop_requested: return ""
                    
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
                    
                    # Check flag AFTER blocking listen but BEFORE cloud call
                    if self._stt_stop_requested: return ""
                    
                    return recognizer.recognize_google(audio, language="ru-RU")
            except sr.WaitTimeoutError:
                return ""
            except Exception as e:
                print(f"STT Error: {e}")
                return None

        loop = asyncio.get_event_loop()
        try:
            text = await loop.run_in_executor(None, _recognize)
            if text and not self._stt_stop_requested:
                self.prompt_input.value = text
            elif text is None and not self._stt_stop_requested:
                self.prompt_input.hint_text = "Ошибка микрофона"
                self.page.update()
                await asyncio.sleep(1.5)
        finally:
            self._is_recording = False
            # Only reset if we haven't already reset via the second click logic
            if not self._stt_stop_requested:
                self._action_icon.src = self._ICON_MIC
                self.prompt_input.hint_text = old_hint
                self.prompt_input.disabled = False
                self._on_input_change(None)
                self.page.update()
                await self.prompt_input.focus()
            else:
                # If we did stop, finalize flag
                self._stt_stop_requested = False

    # Figma SVG asset paths (local) for action states
    _ICON_MIC         = "assets/icons/mic.svg"
    _ICON_MIC_ACTIVE  = "assets/icons/mic_active.svg"
    _ICON_SEND        = "assets/icons/send.svg"
    _ICON_STOP        = "assets/icons/stop_circle.svg"

    def _set_generating(self, generating: bool):
        """Switch panel into/out of generating state."""
        self._is_generating = generating
        self._stop_requested = False
        if generating:
            self.prompt_input.hint_text = "Генерация..."
            self.prompt_input.disabled = True
            self._action_icon.src = self._ICON_STOP
        else:
            self.prompt_input.hint_text = "Спросите ГигаЧат"
            self.prompt_input.disabled = False
            self._action_icon.src = self._ICON_MIC
        self._action_icon.update()
        self.prompt_input.update()



    async def _on_attach_click(self, e):
        """Выбор файлов через tkinter.filedialog в отдельном subprocess.
        ft.FilePicker сломан в desktop-режиме Flet 0.85 (аналогичный баг был на macOS с osascript).
        Запуск tkinter в subprocess (не в потоке!) — единственный надёжный способ.
        """
        import asyncio
        import os
        import sys
        import subprocess

        def _open_dialog():
            script = (
                "import tkinter as tk; from tkinter import filedialog; "
                "root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True); "
                "files = filedialog.askopenfilenames(title='Выберите файлы'); "
                "print('\\n'.join(files))"
            )
            result = subprocess.run(
                [sys.executable, "-c", script],
                capture_output=True, text=True, timeout=60
            )
            raw = result.stdout.strip()
            if not raw:
                return []
            return [p.strip() for p in raw.splitlines() if p.strip()]

        loop = asyncio.get_event_loop()
        try:
            file_paths = await loop.run_in_executor(None, _open_dialog)
        except Exception as ex:
            print(f"FilePicker error: {ex}")
            file_paths = []

        if not file_paths:
            return


        class _FileInfo:
            def __init__(self, path):
                self.path = path
                self.name = os.path.basename(path)

        for path in file_paths:
            f = _FileInfo(path)
            self.attached_files.append(f)
            
            def create_remove_fn(file_obj, chip_ref):
                def remove(e):
                    self.attached_files.remove(file_obj)
                    self.files_row.controls.remove(chip_ref)
                    if not self.attached_files:
                        self.files_row.visible = False
                    self.files_row.update()
                return remove

            extension = os.path.splitext(f.name)[1][1:].upper()
            if not extension:
                extension = "FILE"

            top_row = ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.INSERT_DRIVE_FILE, size=16, color=ft.Colors.with_opacity(0.6, "#303030")),
                    ft.Text(extension, size=12, color=ft.Colors.with_opacity(0.6, "#303030"), weight=ft.FontWeight.W_400, style=ft.TextStyle(letter_spacing=-0.48)),
                ], spacing=4),
                ft.IconButton(
                    icon=ft.Icons.CLOSE, 
                    icon_size=16, 
                    icon_color=ft.Colors.with_opacity(0.6, "#303030"),
                    width=20, height=20,
                    padding=0,
                    on_click=None
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

            bottom_row = ft.Text(
                f.name, size=14, color="#000000", weight=ft.FontWeight.W_400,
                max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, style=ft.TextStyle(letter_spacing=-0.56)
            )

            chip = ft.Container(
                content=ft.Column([
                    top_row,
                    bottom_row
                ], spacing=6),
                bgcolor="#e1e1e1",
                border=ft.border.all(1, "#303030"),
                border_radius=15,
                width=180,
                height=65,
                padding=ft.padding.symmetric(horizontal=10, vertical=10),
                margin=ft.padding.only(bottom=15, right=10),
            )
            
            top_row.controls[1].on_click = create_remove_fn(f, chip)
            self.files_row.controls.append(chip)

        self.files_row.visible = True
        self.files_row.update()

    # ── Chat logic ──────────────────────────────────────────────────────────

    def _on_chat_select(self, session_id: str):
        manager: GigaChatManager = getattr(self.page, "api_manager", None)
        if not manager:
            return
            
        manager.switch_session(session_id)
        
        self.chat_list.controls.clear()
        bubbles = []
        sx, sy, scale_min = self._get_scale()
        for msg in manager.history:
            bubble = MessageBubble(role=msg.role, content=msg.content, scale_min=scale_min, sx=sx, sy=sy)
            self.chat_list.controls.append(self._wrap_bubble(bubble, msg.role))
            bubbles.append(bubble)
            
        self.welcome_state.visible = False
        self.glow_container.visible = False
        if self._left_open:
            self._toggle_left()
            
        self.page.update()
        
        for bubble in bubbles:
            bubble.appear()

    def _new_chat(self, e=None):
        manager: GigaChatManager = getattr(self.page, "api_manager", None)
        if manager:
            manager.start_new_session()
            sx = max(0.65, (self.page.width or 1200) / 1920.0)
            sy = max(0.65, (self.page.height or 800) / 1080.0)
            self.left_menu.refresh_chats(manager.get_sessions_list(), sx, sy)

        self.chat_list.controls.clear()
        self.welcome_state.visible = True
        self.glow_container.visible = True
        self.glow_container.update()
        if self._left_open:
            self._toggle_left()
        self.page.update()

    async def on_send(self, e=None):
        prompt = self.prompt_input.value.strip()
        if not prompt:
            return

        manager: GigaChatManager = getattr(self.page, "api_manager", None)
        if not manager:
            await self.page.push_route("/auth")
            return

        # Close menus on send
        if self._left_open:
            self._toggle_left()
        if self._right_open:
            self._toggle_right()

        # Сохраняем пути файлов до очистки UI
        pending_files = [f.path for f in self.attached_files]

        # Clear UI states
        self.prompt_input.value = ""
        self.attached_files.clear()
        self.files_row.controls.clear()
        self.files_row.visible = False
        self.welcome_state.visible = False
        self.glow_container.visible = False
        self.glow_container.update()

        # Switch to generating state
        self._set_generating(True)
        self._stop_event.clear()
        self.page.update()

        is_first_msg = not bool(manager.history)

        # User bubble — pass file paths so cards render
        sx, sy, scale_min = self._get_scale()
        user_bubble = MessageBubble(role=MessagesRole.USER, content=prompt, files=list(pending_files), scale_min=scale_min, sx=sx)
        self.chat_list.controls.append(self._wrap_bubble(user_bubble, MessagesRole.USER))
        self.page.update()
        user_bubble.appear()

        if is_first_msg:
            # Save new session immediately to populate sidebar
            manager.save_current_session(title=prompt[:40] + ("..." if len(prompt) > 40 else ""))
            sx = max(0.65, (self.page.width or 1200) / 1920.0)
            sy = max(0.65, (self.page.height or 800) / 1080.0)
            self.left_menu.refresh_chats(manager.get_sessions_list(), sx, sy)

        # AI bubble (streaming)
        ai_bubble = MessageBubble(role=MessagesRole.ASSISTANT, content="", scale_min=scale_min, sx=sx, sy=sy)
        self.chat_list.controls.append(self._wrap_bubble(ai_bubble, MessagesRole.ASSISTANT))
        self.page.update()
        ai_bubble.appear()

        try:
            # Загружаем файлы если есть
            file_ids = []
            if pending_files:
                ai_bubble.update_text("⏳ Загрузка файлов...")
                self.page.update()
                file_ids = await manager.upload_files(pending_files)
                ai_bubble.update_text("")  # сбрасываем индикатор загрузки

            async for item in manager.stream_chat(prompt, attachments=file_ids or None, stop_event=self._stop_event):
                if self._stop_event.is_set():
                    break
                if isinstance(item, dict):
                    # Usage sentinel from API — ignore
                    pass
                else:
                    ai_bubble.update_text(item)
                    await self.chat_list.scroll_to(offset=-1, duration=80)
        except Exception as ex:
            ai_bubble.update_text(f"\n\n**Ошибка**: {str(ex)}")
        finally:
            manager.save_current_session()
            self._set_generating(False)
            await self.prompt_input.focus()
            self.page.update()
