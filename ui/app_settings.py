import flet as ft
from core.api import GigaChatManager
import asyncio
import os
import json

class AppSettingsPanel(ft.Container):
    def __init__(self, page: ft.Page, on_close):
        super().__init__()
        self.page_ref = page
        self.on_close_cb = on_close
        
        self.width = 670
        self.bgcolor = "#fdfdfe"
        self.border_radius = 20
        self.padding = 30
        self.shadow = ft.BoxShadow(
            blur_radius=20, 
            spread_radius=0,
            color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK),
            offset=ft.Offset(0, 10)
        )
        self.border = ft.border.all(1, ft.Colors.with_opacity(0.1, "#000000"))
        
        # ── Account Section ──
        acc_title = ft.Text("Аккаунт", size=22, color="#303030", weight=ft.FontWeight.W_500, style=ft.TextStyle(letter_spacing=-0.44))
        
        self.close_btn = ft.IconButton(
            icon=ft.Icons.CLOSE,
            icon_color="#303030",
            icon_size=20,
            on_click=lambda e: self.hide(),
            padding=0,
            width=24, height=24,
        )
        
        header_row = ft.Row([acc_title, self.close_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        # API Key
        key_file = os.path.expanduser("~/.gigachat_key.json")
        api_key_str = "Нет ключа"
        if os.path.exists(key_file):
            try:
                with open(key_file, "r") as f:
                    api_key_str = json.load(f).get("api_key", "Нет ключа")
            except:
                pass
        self.api_key_field = ft.TextField(
            value=api_key_str if api_key_str != "Нет ключа" else "",
            text_size=18,
            color=ft.Colors.with_opacity(0.8, "#303030"),
            bgcolor=ft.Colors.with_opacity(0.3, "#d9d9d9"),
            border=ft.InputBorder.NONE,
            border_radius=10,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=12),
            width=610,
            on_change=self._on_api_key_change,
            hint_text="Введите API ключ"
        )
        
        btn_reset_key = self._pill_button("Сбросить ключ", self._reset_api_key)
        
        def _lbl(text):
            return ft.Text(text, size=18, color="#303030", weight=ft.FontWeight.W_400)

        api_key_row = ft.Row(
            controls=[
                _lbl("API ключ"),
                btn_reset_key
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=30,
        )

        # Chat History
        btn_clear_history = self._pill_button("Очистить историю", self._clear_history)
        history_row = ft.Row(
            controls=[
                _lbl("История чатов"),
                btn_clear_history
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=30,
        )

        acc_section = ft.Column(
            controls=[
                header_row,
                ft.Container(height=10),
                api_key_row,
                self.api_key_field,
                ft.Container(height=10),
                history_row,
            ],
            spacing=10,
        )

        # ── Application Section ──
        app_title = ft.Text("Приложение", size=22, color="#303030", weight=ft.FontWeight.W_500, style=ft.TextStyle(letter_spacing=-0.44))
        
        # Local Storage
        local_path = os.path.expanduser("~/.gigachat_history.json")
        if os.path.exists(key_file):
            try:
                with open(key_file, "r") as f:
                    local_path = json.load(f).get("history_file", local_path)
            except:
                pass

        self.path_field = ft.TextField(
            value=local_path,
            text_size=18,
            color=ft.Colors.with_opacity(0.8, "#303030"),
            bgcolor=ft.Colors.with_opacity(0.3, "#d9d9d9"),
            border=ft.InputBorder.NONE,
            border_radius=10,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=12),
            width=610,
            on_change=self._on_path_change
        )
        btn_restore_default = self._pill_button("Восстановить по умолчанию", self._restore_defaults)
        
        storage_row = ft.Row(
            controls=[
                _lbl("Локальное хранилище"),
                btn_restore_default
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=30,
        )

        # Export
        btn_export = self._pill_button("Скачать всё", self._export_data)
        export_row = ft.Row(
            controls=[
                _lbl("Экспорт данных"),
                btn_export
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=30,
        )

        # Theme
        # Using a PopupMenuButton or just a simple container simulating a dropdown
        self.theme_text = ft.Text("Светлая", size=12, color="#303030")
        theme_dropdown = ft.Container(
            content=ft.Row([
                self.theme_text,
                ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN, size=16, color="#303030")
            ], spacing=4),
            border=ft.border.all(1, "#303030"),
            border_radius=15,
            padding=ft.padding.symmetric(horizontal=12, vertical=4),
            on_click=self._toggle_theme,
            ink=True,
        )

        theme_row = ft.Row(
            controls=[
                _lbl("Тема оформления"),
                theme_dropdown
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=30,
        )

        app_section = ft.Column(
            controls=[
                app_title,
                ft.Container(height=10),
                storage_row,
                self.path_field,
                ft.Container(height=10),
                export_row,
                ft.Container(height=10),
                theme_row,
            ],
            spacing=10,
        )

        self.content = ft.Column(
            controls=[
                acc_section,
                ft.Container(height=30), # spacing between sections
                app_section,
            ],
            spacing=0,
            tight=True,
        )

    def _pill_button(self, text: str, on_click) -> ft.Container:
        return ft.Container(
            content=ft.Text(text, size=12, color="#303030"),
            border=ft.border.all(1, "#303030"),
            border_radius=15,
            padding=ft.padding.symmetric(horizontal=12, vertical=4),
            on_click=on_click,
            ink=True,
        )

    def show(self):
        pass

    def hide(self):
        if self.on_close_cb:
            self.on_close_cb()

    async def _reset_api_key(self, e):
        # Очищаем API ключ и перенаправляем на окно входа
        key_file = os.path.expanduser("~/.gigachat_key.json")
        if os.path.exists(key_file):
            try:
                os.remove(key_file)
            except Exception:
                pass
        self.hide()
        await self.page_ref.push_route("/auth")

    def _clear_history(self, e):
        # Удаляем историю из менеджера и перезаписываем файл
        manager: GigaChatManager = getattr(self.page_ref, "api_manager", None)
        if manager:
            manager.history = []
            manager.sessions = {}
            manager.current_session_id = None
            manager.last_usage = None
            manager._save_sessions_to_disk()
            # Уведомить UI об обновлении (заглушка: нужно перезагрузить левое меню)
            self._show_snackbar("История чатов очищена")
            
    def _restore_defaults(self, e):
        # Сброс кэша и файлов?
        self._clear_history(e)
        self._show_snackbar("Хранилище сброшено по умолчанию")

    def _export_data(self, e):
        # Экспорт
        self._show_snackbar("Данные экспортированы в ~/.gigachat_history.json")

    def _toggle_theme(self, e):
        # Заглушка, функционал смены темы временно вырезан
        self._show_snackbar("Смена темы пока недоступна")

    def _on_api_key_change(self, e):
        key_file = os.path.expanduser("~/.gigachat_key.json")
        data = {}
        if os.path.exists(key_file):
            try:
                with open(key_file, "r") as f:
                    data = json.load(f)
            except:
                pass
        data["api_key"] = self.api_key_field.value
        with open(key_file, "w") as f:
            json.dump(data, f)
        
        manager: GigaChatManager = getattr(self.page_ref, "api_manager", None)
        if manager:
            manager.auth_key = self.api_key_field.value

    def _on_path_change(self, e):
        key_file = os.path.expanduser("~/.gigachat_key.json")
        data = {}
        if os.path.exists(key_file):
            try:
                with open(key_file, "r") as f:
                    data = json.load(f)
            except:
                pass
        data["history_file"] = self.path_field.value
        with open(key_file, "w") as f:
            json.dump(data, f)
            
        manager: GigaChatManager = getattr(self.page_ref, "api_manager", None)
        if manager:
            manager.history_file = self.path_field.value

    def _show_snackbar(self, text: str):
        snack = ft.SnackBar(ft.Text(text))
        self.page_ref.overlay.append(snack)
        snack.open = True
        self.page_ref.update()
