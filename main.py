import flet as ft
import ssl

import platform

# Отключен фикс (ssl._create_unverified_context), так как теперь
# проверка сертификатов корректно обрабатывается в core/api.py

# Совместимость с Flet 0.85+: ft.padding / ft.border / ft.border_radius / ft.margin helpers были удалены
from compat import FletPaddingCompat, FletBorderCompat, FletBorderRadiusCompat, FletMarginCompat
ft.padding = FletPaddingCompat()
ft.border = FletBorderCompat()
ft.border_radius = FletBorderRadiusCompat()
ft.margin = FletMarginCompat()

from ui.auth import AuthView
from ui.chat_layout import ChatView

async def main(page: ft.Page):
    page.title = "CAIS"
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Конфигурация темы Material 3
    page.theme = ft.Theme(
        use_material3=True,
        color_scheme_seed=ft.Colors.TEAL,
        visual_density=ft.VisualDensity.COMPACT,
    )
    page.window.width = 1200
    page.window.height = 800
    page.window.min_width = 750
    page.window.min_height = 600
    await page.window.center()

    async def route_change(route):
        page.views.clear()

        if page.route == "/auth":
            page.views.append(AuthView(page))
        elif page.route == "/chat":
            page.views.append(ChatView(page))

        page.update()

    async def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        await page.push_route(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    await page.push_route("/auth")

if __name__ == "__main__":
    ft.run(main, assets_dir=".")
