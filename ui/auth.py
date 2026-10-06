import flet as ft
import json
import os
from core.api import GigaChatManager

# ── Constants
FIGMA_W = 1920
FIGMA_H = 1080


class AuthView(ft.View):
    def __init__(self, page: ft.Page):
        super().__init__(
            route="/auth",
            padding=0,
            bgcolor="#FFFFFF"
        )

        # ── Ellipse (Ellipse 1.svg) - anchored to background stack
        self.ellipse_img = ft.Image(
            src="assets/glow_ellipse.png",
            fit=ft.BoxFit.FILL,
        )
        self.ellipse_container = ft.Container(
            content=self.ellipse_img,
            left=500,
            top=-150,
            width=1000,
            height=1000,
        )

        # Логотип CAIS — текстовый, без внешнего файла
        self.logo = ft.Text(
            "CAIS",
            size=28,
            weight=ft.FontWeight.W_700,
            color="#000000",
        )

        # ── Title
        self.title = ft.Text(
            "Ваш персональный GigaChat",
            size=28,
            weight=ft.FontWeight.W_500,
            color="#000000",
            no_wrap=True,  # Always one line
        )

        # ── Subtitle
        self.subtitle = ft.Text(
            "Введите Authorization key",
            size=16,
            color="#303030",
        )

        # ── Input field
        self.api_key_field = ft.TextField(
            hint_text="В формате Base64",
            hint_style=ft.TextStyle(color=ft.Colors.with_opacity(0.5, "#303030"), size=16),
            password=True,
            can_reveal_password=True,
            border_radius=10,
            border_width=2,
            border_color="#303030",
            focused_border_color="#000000",
            focused_border_width=2,
            color="#303030",
            text_size=16,
            width=280,
            height=42,
            content_padding=ft.padding.only(left=12, right=12, top=8, bottom=8),
            on_submit=self.on_connect_click,
        )

        # ── Connect button
        self.connect_btn = ft.Container(
            content=ft.Text("Подключить", color="#FFFFFF", size=16),
            width=110,
            height=42,
            bgcolor="#303030",
            border_radius=10,
            alignment=ft.Alignment.CENTER,
            on_click=self.on_connect_click,
            ink=True,
        )

        # ── Loading & error
        self.loading = ft.ProgressBar(
            width=400,
            visible=False,
            color="#303030",
            bgcolor=ft.Colors.with_opacity(0.15, "#303030"),
        )
        self.error_text = ft.Text(color=ft.Colors.RED_600, visible=False, size=13)

        # ── Form row
        self.form_row = ft.Row(
            controls=[self.api_key_field, self.connect_btn],
            spacing=16,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # ── Content column
        self.main_column = ft.Column(
            controls=[
                self.logo,
                self.title,
                self.subtitle,
                self.form_row,
                self.loading,
                self.error_text,
            ],
            spacing=20,
            tight=True,
        )

        # Container with absolute position — updated in _layout()
        self.content_container = ft.Container(
            content=self.main_column,
            left=125,
            top=300,
            width=420,
        )

        # ── Footer
        self.footer_container = ft.Container(
            content=ft.Text(
                "DESIGNED AND POWERED BY MAXIM PARKHOMENKO",
                size=11,
                color="#000000",
                style=ft.TextStyle(letter_spacing=0.8),
            ),
            left=125,
            bottom=30,
        )

        # ── Full-page Stack
        self.bg_stack = ft.Stack(
            controls=[
                self.ellipse_container,
                self.content_container,
                self.footer_container,
            ],
            expand=True,
        )

        self.controls = [self.bg_stack]

    def did_mount(self):
        self._layout()
        self.page.on_resize = self._on_resize
        # Авто-логин если ключ уже сохранён
        import asyncio
        asyncio.ensure_future(self._try_autologin())

    async def _try_autologin(self):
        # Fallback to home-dir file since client_storage is missing in this Flet version
        key_file = os.path.expanduser("~/.gigachat_key.json")
        saved_key = ""
        if os.path.exists(key_file):
            try:
                with open(key_file, "r") as f:
                    saved_key = json.load(f).get("api_key", "")
            except:
                pass
                
        if saved_key:
            self.api_key_field.value = saved_key
            self.api_key_field.update()
            await self.on_connect_click(None)

    def will_unmount(self):
        self.page.on_resize = None

    def _on_resize(self, e):
        self._layout()
        self.bg_stack.update()

    def _layout(self):
        """Scale all positions from Figma 1920×1080 to actual window size."""
        w = self.page.window.width or 1200
        h = self.page.window.height or 800

        sx = w / FIGMA_W
        sy = h / FIGMA_H

        # ── Content block: Figma left=200, top=405
        self.content_container.left = round(200 * sx)
        self.content_container.top = round(405 * sy)
        self.content_container.width = round(535 * sx)

        # ── Ellipse: Figma center=(1747, 575), radius=942
        radius = round(942 * sx)
        cx = round(1747 * sx)
        cy = round(575 * sy)
        self.ellipse_container.left = cx - radius
        self.ellipse_container.top = cy - radius
        self.ellipse_container.width = radius * 2
        self.ellipse_container.height = radius * 2

        # ── Footer: Figma left=200, top=1042
        self.footer_container.left = round(200 * sx)

        # ── Scale logo (text)
        self.logo.size = round(28 * max(sx, 0.65))

        # ── Scale typography and form
        ts = max(sx, 0.65)

        # Figma: subtitle=20px, input/btn=18px — always 2px gap
        title_size = round(40 * ts)
        subtitle_size = max(round(20 * ts), 14)
        field_text_size = subtitle_size - 2  # always 2px smaller

        self.title.size = title_size
        self.subtitle.size = subtitle_size
        self.error_text.size = max(round(14 * ts), 12)

        field_w = round(392 * sx)
        field_h = max(round(46 * sy), 40)  # minimum 40px height
        btn_w = max(round(122 * sx), 130)  # minimum 130px — enough for «Подключить»

        self.api_key_field.width = field_w
        self.api_key_field.height = field_h
        self.api_key_field.text_size = field_text_size
        # Sync hint_style size — fixes "В формате Base64" appearing larger than button
        self.api_key_field.hint_style = ft.TextStyle(
            color=ft.Colors.with_opacity(0.5, "#303030"),
            size=field_text_size,
        )

        self.connect_btn.width = btn_w
        self.connect_btn.height = field_h
        if self.connect_btn.content:
            self.connect_btn.content.size = field_text_size

        # Content container width: generous minimum so title "GigaChat" never clips
        self.content_container.width = max(round(535 * sx), 460, field_w + btn_w + 20)

        # Ellipse: original Figma radius, but shift center right so left edge > 55% screen
        radius = round(942 * sx)          # original Figma proportional radius
        cx = round(w * 1.04)              # center just past right edge (55% left-edge guaranteed)
        cy = round(575 * sy)              # same vertical proportion as Figma (575/1080)
        self.ellipse_container.left = cx - radius
        self.ellipse_container.top = cy - radius
        self.ellipse_container.width = radius * 2
        self.ellipse_container.height = radius * 2

    # ── Error helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _friendly_error(ex: Exception) -> str:
        print("CONNECTION ERROR:", repr(ex))
        msg = str(ex)
        if "401" in msg or "403" in msg or "Unauthorized" in msg or "Forbidden" in msg:
            return "Ключ авторизации недействителен. Получите новый ключ в личном кабинете GigaChat."
        if "400" in msg or "decode" in msg or "header" in msg or "Can't decode" in msg:
            return "Неверный формат ключа. Убедитесь, что вставлен полный Base64-ключ из личного кабинета."
        if "timeout" in msg.lower() or "timed out" in msg.lower():
            return "Сервер не ответил вовремя. Проверьте интернет-соединение и попробуйте ещё раз."
        if "connect" in msg.lower() or "network" in msg.lower() or "ssl" in msg.lower():
            return "Не удалось подключиться к серверам GigaChat. Проверьте интернет-соединение."
        return "Произошла ошибка при подключении. Попробуйте ещё раз."

    # ── Auth logic ─────────────────────────────────────────────────────────────

    async def on_connect_click(self, e):
        api_key = self.api_key_field.value.strip()
        if not api_key:
            self.show_error("Пожалуйста, введите ключ авторизации.")
            return

        self.loading.visible = True
        self.connect_btn.disabled = True
        self.error_text.visible = False
        self.page.update()

        manager = GigaChatManager(auth_key=api_key)
        try:
            await manager.check_connection()
            self.page.api_manager = manager
            
            # Save key in home-dir file as fallback
            try:
                key_file = os.path.expanduser("~/.gigachat_key.json")
                with open(key_file, "w") as f:
                    json.dump({"api_key": api_key}, f)
            except:
                pass

            self.content_container.opacity = 0
            self.page.update()

            import asyncio
            await asyncio.sleep(0.3)

            await self.page.push_route("/chat")
        except Exception as ex:
            self.show_error(self._friendly_error(ex))
            self.content_container.opacity = 1
        finally:
            self.loading.visible = False
            self.connect_btn.disabled = False
            self.page.update()

    def show_error(self, message: str):
        self.error_text.value = message
        self.error_text.visible = True
        self.page.update()
