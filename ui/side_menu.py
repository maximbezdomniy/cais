import flet as ft


class SideMenu(ft.Container):
    """
    Левое боковое меню (overlay поверх экрана).
    Figma: 350×1000px, border #303030, radius 28px, shadow.
    Адаптируется к размерам окна через update_layout.
    """

    def __init__(self, on_close, on_new_chat, on_chat_select, on_settings, chat_history: list):
        super().__init__()

        self.on_close_cb = on_close
        self.on_new_chat_cb = on_new_chat
        self.on_chat_select_cb = on_chat_select
        self.on_settings_cb = on_settings
        self.chat_history = chat_history  # list of dict: [{'id': 'uuid', 'title': '...'}, ...]

        # Базовые размеры из Figma (для 1920x1080)
        self.base_width = 350
        self.base_icon_size = 25
        self.base_text_size_menu = 18
        self.base_text_size_title = 22
        self.base_text_size_item = 16
        self.base_padding = 30  # 8.5% от 350px это ~30px
        
        # ── Иконки меню
        self.icon_settings = ft.Image(src="assets/icons/settings.svg", width=self.base_icon_size, height=self.base_icon_size, color="#303030")
        self.text_settings = ft.Text("Настройки", size=self.base_text_size_menu, color="#303030", weight=ft.FontWeight.W_400)
        
        settings_row = ft.Container(
            content=ft.Row(
                controls=[self.icon_settings, self.text_settings],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=self.base_padding, vertical=15),
            border_radius=10,
            on_click=self._on_settings_click,
            ink=True,
        )

        self.icon_content = ft.Image(src="assets/icons/hallway.svg", width=self.base_icon_size, height=self.base_icon_size, color="#303030")
        self.text_content = ft.Text("Мой контент", size=self.base_text_size_menu, color="#303030", weight=ft.FontWeight.W_400)

        content_row = ft.Container(
            content=ft.Row(
                controls=[self.icon_content, self.text_content],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=self.base_padding, vertical=15),
            border_radius=10,
            on_click=self._on_content_click,
            ink=True,
        )

        # ── Список чатов
        self.chats_label_text = ft.Text("Чаты", size=self.base_text_size_title, color="#303030", weight=ft.FontWeight.W_400)
        self.chats_label = ft.Container(
            content=self.chats_label_text,
            padding=ft.padding.only(left=self.base_padding, top=20, bottom=10),
        )

        self.chat_list_col = ft.Column(
            controls=self._build_chat_items(1.0, 1.0),
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
        )

        # ── Панель целиком
        panel = ft.Column(
            controls=[
                settings_row,
                content_row,
                ft.Divider(height=1, color=ft.Colors.with_opacity(0.15, "#303030")),
                self.chats_label,
                self.chat_list_col,
            ],
            spacing=4,
            scroll=ft.ScrollMode.AUTO,
        )

        # Container with white bg, border, shadow — matches Figma exactly
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
        self.padding = ft.padding.symmetric(vertical=20)
        self.content = panel
        
        # Анимация выезда (исходная ширина + небольшой запас)
        self.animate_position = ft.Animation(280, ft.AnimationCurve.EASE_OUT_CUBIC)
        self.left = -400  # starts hidden off-screen
        self.top = 30
        self.bottom = 30
        self._is_open = False

    def update_layout(self, sx: float, sy: float):
        """Адаптация размеров под текущее разрешение окна."""
        self.width = self.base_width * sx
        self.border_radius = 28 * min(sx, sy)
        self.padding = ft.padding.symmetric(vertical=20 * sy)
        self.top = 30 * sy
        self.bottom = 50 * sy
        
        # Иконки
        icon_size = self.base_icon_size * min(sx, sy)
        self.icon_settings.width = icon_size
        self.icon_settings.height = icon_size
        self.icon_content.width = icon_size
        self.icon_content.height = icon_size
        
        # Тексты
        self.text_settings.size = self.base_text_size_menu * min(sx, sy)
        self.text_settings.style = ft.TextStyle(letter_spacing=self.text_settings.size * -0.04)
        self.text_content.size = self.base_text_size_menu * min(sx, sy)
        self.text_content.style = ft.TextStyle(letter_spacing=self.text_content.size * -0.04)
        self.chats_label_text.size = self.base_text_size_title * min(sx, sy)
        self.chats_label_text.style = ft.TextStyle(letter_spacing=self.chats_label_text.size * -0.04)
        
        # Отступы
        pad_x = self.base_padding * sx
        
        self.chats_label.padding = ft.padding.only(left=pad_x, top=20 * sy, bottom=10 * sy)
        
        # Пересобираем элементы списка с новым масштабом
        self.chat_list_col.controls = self._build_chat_items(sx, sy)
        
        # Положение (скрыто/показано)
        if self._is_open:
            self.left = 30 * sx
        else:
            self.left = - (self.base_width * sx + 50)
            
        self.update()

    def _build_chat_items(self, sx: float, sy: float):
        items = []
        pad_x = self.base_padding * sx
        text_size = self.base_text_size_item * min(sx, sy)
        
        for chat_data in self.chat_history:
            session_id = chat_data['id']
            title = chat_data['title']
            
            items.append(
                ft.Container(
                    content=ft.Text(
                        title,
                        size=text_size,
                        color="#303030",
                        style=ft.TextStyle(letter_spacing=text_size * -0.04),
                        overflow=ft.TextOverflow.ELLIPSIS,
                        no_wrap=True,
                    ),
                    padding=ft.padding.symmetric(horizontal=pad_x, vertical=10 * sy),
                    ink=True,
                    data=session_id, # Храним ID
                    on_click=self._on_chat_item_click,
                )
            )
            
        if not items:
            items.append(
                ft.Container(
                    content=ft.Text(
                        "Нет сохранённых чатов",
                        size=text_size * 0.9,
                        color=ft.Colors.with_opacity(0.5, "#303030"),
                        style=ft.TextStyle(letter_spacing=(text_size * 0.9) * -0.04),
                        italic=True,
                    ),
                    padding=ft.padding.symmetric(horizontal=pad_x, vertical=10 * sy),
                )
            )
        return items
        
    def _on_chat_item_click(self, e):
        session_id = e.control.data
        if self.on_chat_select_cb:
            self.on_chat_select_cb(session_id)
        self.hide() # Закрываем меню после выбора

    def refresh_chats(self, chat_history: list, sx: float = 1.0, sy: float = 1.0):
        self.chat_history = chat_history
        self.chat_list_col.controls = self._build_chat_items(sx, sy)
        self.chat_list_col.update()

    def show(self, sx: float = 1.0):
        self._is_open = True
        self.left = 30 * sx
        self.update()

    def hide(self, sx: float = 1.0):
        self._is_open = False
        self.left = - (self.base_width * sx + 50)
        self.update()

    def _on_settings_click(self, e):
        if self.on_settings_cb:
            self.on_settings_cb()

    def _on_content_click(self, e):
        pass
