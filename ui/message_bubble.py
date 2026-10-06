import flet as ft
from gigachat.models import MessagesRole
import os

# ── Базовые размеры из Figma (1920×1080) ─────────────────────────────────
_BASE_BUBBLE_PADDING_H = 20   # px horizontal
_BASE_BUBBLE_PADDING_V = 20   # px vertical
_BASE_BUBBLE_RADIUS    = 20   # px
_BASE_MARGIN_BOTTOM    = 20   # px between bubbles
_BASE_FILE_CARD_W      = 200  # px
_BASE_FILE_CARD_H      = 100  # px
_BASE_FILE_CARD_RADIUS = 20   # px
_BASE_IMG_THUMB        = 100  # px (square)
_BASE_IMG_RADIUS       = 20   # px
_BASE_TEXT_SIZE        = 20   # px  (user + AI paragraph)
_BASE_FILE_NAME_SIZE   = 16   # px
_BASE_FILE_EXT_SIZE    = 16   # px
_BASE_FILE_ICON_SIZE   = 24   # px


class FileDocCard(ft.Container):
    """Карточка документа (DOCX/PDF/…).
    Figma: 200×100, bg #e1e1e1, border-radius 20, иконка + тип + имя.
    """
    def __init__(self, file_path: str, scale_min: float = 1.0, sx: float = 1.0):
        super().__init__()
        name = os.path.basename(file_path)
        ext  = os.path.splitext(name)[1].upper().lstrip(".") or "FILE"

        doc_icon = ft.Image(
            src="assets/icons/article.svg",
            width  = _BASE_FILE_ICON_SIZE * scale_min,
            height = _BASE_FILE_ICON_SIZE * scale_min,
            color  = ft.Colors.with_opacity(0.5, "#303030"),
        )
        ext_text = ft.Text(
            ext,
            size   = _BASE_FILE_EXT_SIZE * scale_min,
            color  = ft.Colors.with_opacity(0.5, "#303030"),
            style  = ft.TextStyle(letter_spacing=_BASE_FILE_EXT_SIZE * scale_min * -0.04),
        )
        name_text = ft.Text(
            name,
            size     = _BASE_FILE_NAME_SIZE * scale_min,
            color    = "#000000",
            overflow = ft.TextOverflow.ELLIPSIS,
            no_wrap  = True,
            style    = ft.TextStyle(letter_spacing=_BASE_FILE_NAME_SIZE * scale_min * -0.04),
        )

        self.width         = _BASE_FILE_CARD_W * sx
        self.height        = _BASE_FILE_CARD_H * scale_min
        self.bgcolor       = "#e1e1e1"
        self.border_radius = _BASE_FILE_CARD_RADIUS * scale_min
        self.padding = ft.padding.symmetric(
            horizontal = _BASE_FILE_CARD_W * sx * 0.10,
            vertical   = _BASE_FILE_CARD_H * scale_min * 0.20,
        )
        # Главное: имя сверху, иконка+тип снизу (по макету)
        self.content = ft.Column(
            controls = [
                name_text,
                ft.Row(
                    controls = [doc_icon, ext_text],
                    spacing  = 5 * scale_min,
                    vertical_alignment = ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing = 17 * scale_min,
            tight   = True,
        )


class FileImageThumb(ft.Container):
    """Миниатюра изображения.
    Figma: 100×100, border-radius 20.
    """
    def __init__(self, file_path: str, scale_min: float = 1.0):
        super().__init__()
        self.width         = _BASE_IMG_THUMB * scale_min
        self.height        = _BASE_IMG_THUMB * scale_min
        self.border_radius = _BASE_IMG_RADIUS * scale_min
        self.clip_behavior = ft.ClipBehavior.ANTI_ALIAS
        self.content = ft.Image(
            src     = file_path,
            width   = _BASE_IMG_THUMB * scale_min,
            height  = _BASE_IMG_THUMB * scale_min,
            fit     = ft.BoxFit.COVER,
        )


# ── Helpers ───────────────────────────────────────────────────────────────
_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}

def _is_image(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in _IMAGE_EXTS


class MessageBubble(ft.Container):
    """Пузырь сообщения в чате.

    Пользователь: голубой пузырь rgba(114,177,254,0.3), текст отдельно.
                  Файлы — отдельные карточки/миниатюры НИЖЕ пузыря.
    AI:           прозрачный, Markdown, левый край, вся ширина.

    Параметр files — список путей к файлам, используется только для USER.
    scale_min, sx передаются из _layout() через chat_layout.
    """

    def __init__(
        self,
        role: MessagesRole,
        content: str = "",
        files: list = None,
        scale_min: float = 1.0,
        sx: float = 1.0,
        sy: float = 1.0,
    ):
        super().__init__()
        self.role            = role
        self.message_content = content
        self.files           = files or []
        self.scale_min       = scale_min
        self.sx              = sx
        self.sy              = sy

        is_user = (role == MessagesRole.USER)

        # Анимация появления
        self.animate  = ft.Animation(300, ft.AnimationCurve.EASE_OUT)
        self.scale    = ft.Scale(0.96)
        self.opacity  = 0

        if is_user:
            self._build_user(content)
        else:
            self._build_ai(content)

    # ── USER ─────────────────────────────────────────────────────────────

    def _build_user(self, content: str):
        sm = self.scale_min
        sx = self.sx

        self.default_bgcolor = ft.Colors.with_opacity(0.3, "#72B1FE")
        self.hover_bgcolor   = ft.Colors.with_opacity(0.4, "#72B1FE")
        self.bgcolor       = self.default_bgcolor
        self.border_radius = _BASE_BUBBLE_RADIUS * sm
        self.padding       = ft.padding.symmetric(
            horizontal = _BASE_BUBBLE_PADDING_H * sx,
            vertical   = _BASE_BUBBLE_PADDING_V * sm,
        )
        self.margin    = ft.margin.only(bottom=_BASE_MARGIN_BOTTOM * sm)
        self.on_hover  = self._hover

        self._user_text = ft.Text(
            content,
            size   = _BASE_TEXT_SIZE * sm,
            color  = "#000000",
            weight = ft.FontWeight.W_400,
            style  = ft.TextStyle(letter_spacing=_BASE_TEXT_SIZE * sm * -0.04),
            selectable = True,
        )
        self.content = self._user_text

    def make_attachments_row(self) -> ft.Control | None:
        """Создаёт ряд карточек/миниатюр ниже пузыря (вызывается из chat_layout)."""
        if not self.files:
            return None
        sm = self.scale_min
        sx = self.sx

        images = [f for f in self.files if _is_image(f)]
        docs   = [f for f in self.files if not _is_image(f)]

        rows = []
        if images:
            rows.append(ft.Row(
                controls=[FileImageThumb(f, sm) for f in images],
                spacing=10 * sx,
                alignment=ft.MainAxisAlignment.END,
            ))
        for f in docs:
            rows.append(ft.Row(
                controls=[FileDocCard(f, sm, sx)],
                alignment=ft.MainAxisAlignment.END,
            ))

        if not rows:
            return None
        return ft.Column(
            controls=rows,
            spacing=10 * sm,
            horizontal_alignment=ft.CrossAxisAlignment.END,
        )

    # ── AI ───────────────────────────────────────────────────────────────

    def _build_ai(self, content: str):
        sm = self.scale_min
        sy = self.sy

        self.default_bgcolor = ft.Colors.TRANSPARENT
        self.hover_bgcolor   = ft.Colors.TRANSPARENT
        self.bgcolor         = ft.Colors.TRANSPARENT
        self.border_radius   = 0
        self.padding         = ft.padding.only(bottom=_BASE_MARGIN_BOTTOM * sm)
        # Figma: 50px gap above AI response
        self.margin          = ft.margin.only(top=round(50 * sy))

        self.parts_col = ft.Column(spacing=15 * sm, expand=True)
        self.content = self.parts_col
        self.expand  = True
        
        self._update_markdown_parts()

    def _parse_markdown(self, text: str):
        blocks = []
        lines = text.split('\n')
        in_code = False
        current_text = []
        current_lang = ""
        
        for line in lines:
            if line.startswith('```'):
                if not in_code:
                    if current_text:
                        blocks.append({'type': 'text', 'content': '\n'.join(current_text)})
                        current_text = []
                    in_code = True
                    current_lang = line[3:].strip()
                else:
                    blocks.append({'type': 'code', 'lang': current_lang, 'content': '\n'.join(current_text)})
                    current_text = []
                    in_code = False
            else:
                current_text.append(line)
                
        if current_text or not blocks:
            blocks.append({'type': 'code' if in_code else 'text', 'lang': current_lang, 'content': '\n'.join(current_text)})
            
        return blocks

    def _create_text_md(self, text):
        sm = self.scale_min
        return ft.Markdown(
            text,
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            md_style_sheet=ft.MarkdownStyleSheet(
                p_text_style=ft.TextStyle(
                    color="#000000",
                    size=_BASE_TEXT_SIZE * sm,
                    letter_spacing=_BASE_TEXT_SIZE * sm * -0.04,
                ),
                h1_text_style=ft.TextStyle(color="#000000", size=26 * sm, weight=ft.FontWeight.W_500),
                h2_text_style=ft.TextStyle(color="#000000", size=22 * sm, weight=ft.FontWeight.W_500),
                h3_text_style=ft.TextStyle(color="#000000", size=20 * sm, weight=ft.FontWeight.W_500),
                code_text_style=ft.TextStyle(font_family="Monospace", size=20 * sm),
                block_spacing=15 * sm,
            ),
        )

    def _create_code_block(self, lang, code):
        sm = self.scale_min
        
        async def copy_click(e):
            await e.page.clipboard.set(code)
            
        lang_display = lang.capitalize() or "Code"
        
        header = ft.Container(
            bgcolor="#f6f8fa",
            padding=ft.padding.symmetric(horizontal=20 * sm, vertical=10 * sm),
            border_radius=ft.BorderRadius(top_left=28 * sm, top_right=28 * sm, bottom_left=10 * sm, bottom_right=10 * sm),
            content=ft.Row(
                controls=[
                    ft.Text(lang_display, color="#000000", size=20 * sm, weight=ft.FontWeight.W_400),
                    ft.IconButton(
                        icon=ft.Icons.CONTENT_COPY,
                        icon_size=24 * sm,
                        icon_color="#303030",
                        tooltip="Копировать код",
                        on_click=copy_click,
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        )
        
        code_md = ft.Markdown(
            f"```{lang}\n{code}\n```",
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            code_theme="github",
            md_style_sheet=ft.MarkdownStyleSheet(
                code_text_style=ft.TextStyle(font_family="Monospace", size=20 * sm),
                codeblock_decoration=ft.BoxDecoration(
                    bgcolor="#f6f8fa",
                    border_radius=ft.BorderRadius(
                        top_left=10 * sm, top_right=10 * sm,
                        bottom_left=28 * sm, bottom_right=28 * sm,
                    ),
                ),
                codeblock_padding=ft.padding.symmetric(horizontal=20 * sm, vertical=16 * sm),
            ),
        )
        
        container = ft.Container(
            content=ft.Column([
                header,
                code_md
            ], spacing=10 * sm),
        )
        container.is_code_block = True
        return container

    def _update_markdown_parts(self):
        blocks = self._parse_markdown(self.message_content)
        
        for i, block in enumerate(blocks):
            if i < len(self.parts_col.controls):
                ctrl = self.parts_col.controls[i]
                if block['type'] == 'text':
                    if isinstance(ctrl, ft.Markdown):
                        ctrl.value = block['content']
                    else:
                        self.parts_col.controls[i] = self._create_text_md(block['content'])
                else:
                    if isinstance(ctrl, ft.Container) and getattr(ctrl, "is_code_block", False):
                        md_code = ctrl.content.controls[1]
                        md_code.value = f"```{block['lang']}\n{block['content']}\n```"
                        lang_text = ctrl.content.controls[0].content.controls[0]
                        lang_text.value = block['lang'].capitalize() or "Code"
                        
                        copy_btn = ctrl.content.controls[0].content.controls[1]
                        def make_copy(code_text):
                            async def handler(e):
                                await e.page.clipboard.set(code_text)
                            return handler
                        copy_btn.on_click = make_copy(block['content'])
                    else:
                        self.parts_col.controls[i] = self._create_code_block(block['lang'], block['content'])
            else:
                if block['type'] == 'text':
                    self.parts_col.controls.append(self._create_text_md(block['content']))
                else:
                    self.parts_col.controls.append(self._create_code_block(block['lang'], block['content']))
                    
        while len(self.parts_col.controls) > len(blocks):
            self.parts_col.controls.pop()
            
        try:
            self.update()
        except RuntimeError:
            pass

    # ── Shared ───────────────────────────────────────────────────────────

    def _hover(self, e):
        if self.role != MessagesRole.USER:
            return
        self.bgcolor = self.hover_bgcolor if e.data == "true" else self.default_bgcolor
        try:
            self.update()
        except RuntimeError:
            pass

    def update_text(self, delta: str):
        self.message_content += delta
        self._update_markdown_parts()

    def appear(self):
        """Плавное появление при добавлении в дерево."""
        self.scale   = ft.Scale(1.0)
        self.opacity = 1
        try:
            self.update()
        except RuntimeError:
            pass
