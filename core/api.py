import os
import uuid
import sys
from typing import List, Optional, Dict, Any
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole


# Размер контекстного окна для каждой модели (токены)
MODEL_CONTEXT_WINDOW = {
    "GigaChat":     128_000,
    "GigaChat-Pro": 128_000,
    "GigaChat-Max": 128_000,
}


class ModelParams:
    """Параметры модели, управляемые пользователем через правую панель."""
    def __init__(self):
        self.model = "GigaChat"          # GigaChat / GigaChat-Pro / GigaChat-Max
        self.temperature = 0.8
        self.repetition_penalty = 1.0
        self.top_p = 0.5
        self.max_tokens = 1024
        self.stream = True
        self.system_prompt = ""

    @property
    def context_window(self) -> int:
        """Размер контекстного окна текущей модели."""
        return MODEL_CONTEXT_WINDOW.get(self.model, 128_000)


class GigaChatManager:
    def __init__(self, auth_key: str, scope: str = "GIGACHAT_API_PERS"):
        self.auth_key = auth_key
        self.scope = scope
        self.history = []
        self.sessions: Dict[str, Dict[str, Any]] = {}  # uuid -> {'title': str, 'history': list}
        self.current_session_id: Optional[str] = None
        self.params = ModelParams()
        
        # Получаем абсолютный путь к сертификату (с учетом сборки через PyInstaller)
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        cert_path = os.path.join(base_path, "russian_trusted_ca_bundle.crt")
        if os.path.exists(cert_path):
            self.verify_ssl = True
            self.ca_bundle_file = cert_path
        else:
            self.verify_ssl = False  # Фолбэк, если файл не найден
            self.ca_bundle_file = None
            
        # Последнее известное использование токенов
        self.last_usage: Optional[dict] = None   # {"prompt": N, "completion": N, "total": N, "max": N}
        # Load configured history path
        key_file = os.path.expanduser("~/.gigachat_key.json")
        custom_path = None
        if os.path.exists(key_file):
            try:
                import json
                with open(key_file, "r") as f:
                    custom_path = json.load(f).get("history_file")
            except Exception:
                pass
        self.history_file = custom_path if custom_path else os.path.expanduser("~/.gigachat_history.json")
        self._load_sessions_from_disk()

    def _load_sessions_from_disk(self):
        if os.path.exists(self.history_file):
            import json
            try:
                with open(self.history_file, "r") as f:
                    data = json.load(f)
                    # Convert dict representations back to Messages objects
                    for sid, session in data.items():
                        history_objs = []
                        for msg in session.get('history', []):
                            history_objs.append(Messages(role=msg['role'], content=msg['content']))
                        self.sessions[sid] = {
                            'title': session.get('title', 'Чат'), 
                            'history': history_objs,
                            'usage': session.get('usage', None)
                        }
            except Exception as e:
                print(f"Failed to load history: {e}")

    def _save_sessions_to_disk(self):
        import json
        try:
            data = {}
            for sid, session in self.sessions.items():
                history_dicts = [{'role': m.role, 'content': m.content} for m in session['history']]
                data[sid] = {
                    'title': session['title'], 
                    'history': history_dicts,
                    'usage': session.get('usage', None)
                }
            with open(self.history_file, "w") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save history: {e}")

    def start_new_session(self):
        """Очищает текущую историю для начала нового диалога."""
        if self.current_session_id and self.history:
            self.save_current_session()
            
        self.history = []
        self.current_session_id = None
        self.last_usage = None

    def save_current_session(self, title: Optional[str] = None):
        """Сохраняет текущую историю сообщений в сессию."""
        if not self.history and title is None:
            return
            
        if not self.current_session_id:
            self.current_session_id = str(uuid.uuid4())
            
        # Если заголовок не передан, берем начало первого сообщения пользователя
        if title is None:
            first_user_msg = next((m.content for m in self.history if m.role == MessagesRole.USER), "Новый чат")
            title = first_user_msg[:40].replace('\n', ' ') + ("..." if len(first_user_msg) > 40 else "")
            
        # Если сессия уже существует, оставляем её старый заголовок, обновляем только историю
        if self.current_session_id in self.sessions:
            title = self.sessions[self.current_session_id]['title']

        self.sessions[self.current_session_id] = {
            'title': title,
            'history': list(self.history),
            'usage': self.last_usage.copy() if self.last_usage else None
        }
        self._save_sessions_to_disk()

    def switch_session(self, session_id: str) -> bool:
        """Переключается на существующую сессию по её ID."""
        if self.current_session_id and self.history:
            self.save_current_session()
            
        if session_id in self.sessions:
            self.current_session_id = session_id
            self.history = list(self.sessions[session_id]['history'])
            usage = self.sessions[session_id].get('usage', None)
            self.last_usage = usage.copy() if usage else None
            return True
        return False
        
    def get_sessions_list(self) -> List[dict]:
        """Возвращает список сохраненных сессий для отображения в UI."""
        return [{'id': sid, 'title': data['title']} for sid, data in self.sessions.items()]

    def _get_client(self):
        kwargs = {
            "credentials": self.auth_key,
            "scope": self.scope,
            "verify_ssl_certs": self.verify_ssl
        }
        if self.ca_bundle_file:
            kwargs["ca_bundle_file"] = self.ca_bundle_file
            
        return GigaChat(**kwargs)

    def _limit_context(self):
        # Ограничиваем историю последними 20 репликами
        if len(self.history) > 20:
            self.history = self.history[-20:]

    async def check_connection(self):
        """Проверка соединения и авторизации при входе."""
        async with self._get_client() as client:
            response = await client.achat(Chat(
                messages=[Messages(role=MessagesRole.USER, content="ping")],
                max_tokens=2
            ))
            return response

    async def upload_files(self, file_paths: List[str]) -> List[str]:
        """Загружает файлы в API и возвращает список file_id."""
        file_ids = []
        async with self._get_client() as client:
            for path in file_paths:
                try:
                    with open(path, "rb") as f:
                        uploaded = await client.aupload_file(file=f, purpose="general")
                        file_ids.append(uploaded.id_)
                except Exception as ex:
                    print(f"[upload_files] Ошибка загрузки {path}: {ex}")
        return file_ids

    async def stream_chat(self, prompt: str, attachments: Optional[List[str]] = None, stop_event: Optional["asyncio.Event"] = None):
        """Стриминг ответа модели.
        Yields:
            str  — очередной токен текста
            dict — финальное использование токенов {"prompt", "completion", "total", "max"}
                   отправляется одним элементом ПОСЛЕ всех токенов
        """
        messages = []
        if self.params.system_prompt.strip():
            messages.append(Messages(
                role=MessagesRole.SYSTEM,
                content=self.params.system_prompt.strip()
            ))
        messages += self.history

        user_msg_kwargs = {"role": MessagesRole.USER, "content": prompt}
        if attachments:
            user_msg_kwargs["attachments"] = attachments
        user_msg = Messages(**user_msg_kwargs)
        messages.append(user_msg)
        self.history.append(Messages(role=MessagesRole.USER, content=prompt))
        self._limit_context()

        response_text = ""
        last_usage = None
        try:
            async with self._get_client() as client:
                payload = Chat(
                    messages=messages,
                    model=self.params.model,
                    temperature=self.params.temperature,
                    top_p=self.params.top_p,
                    repetition_penalty=self.params.repetition_penalty,
                    max_tokens=self.params.max_tokens,
                    stream=self.params.stream,
                )
                async for chunk in client.astream(payload):
                    if stop_event and stop_event.is_set():
                        break
                    if chunk.choices:
                        delta = chunk.choices[0].delta.content
                        if delta:
                            response_text += delta
                            yield delta
                    # Собираем usage из чанка (обычно populated в последнем)
                    if chunk.usage and chunk.usage.total_tokens:
                        usage = chunk.usage
                        last_usage = {
                            "prompt": usage.prompt_tokens or 0,
                            "completion": usage.completion_tokens or 0,
                            "total": usage.total_tokens or 0,
                            "max": self.params.max_tokens,
                        }
        except Exception as e:
            yield f"\n\n**Ошибка**: {str(e)}"
            return

        self.history.append(Messages(role=MessagesRole.ASSISTANT, content=response_text))

        # Сохраняем и отдаём usage одним финальным элементом
        if last_usage:
            # Заменяем max на контекстное окно модели
            last_usage["max"] = self.params.context_window
            self.last_usage = last_usage
            yield last_usage  # dict — сигнал для UI обновить индикатор

