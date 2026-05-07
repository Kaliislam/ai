"""Gradio web arayüzü — TurkishJARVIS."""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any

import gradio as gr

logger = logging.getLogger(__name__)


class GradioUI:
    """Jarvis Gradio web arayüzü.

    ChatInterface + ses giriş/çıkış + ayarlar paneli.
    """

    PERSONALITY_OPTIONS = {
        "professional_friendly": "Profesyonel & Dostane",
        "casual_humorous": "Gündelik & Esprili",
        "formal_precise": "Resmi & Kesin",
        "empathetic_warm": "Empatik & Sıcak",
    }

    def __init__(
        self,
        config: Any | None = None,
        llm_client: Any | None = None,
        conversation_store: Any | None = None,
        episodic_memory: Any | None = None,
        long_term_memory: Any | None = None,
        rag: Any | None = None,
        tool_registry: Any | None = None,
        personality_builder: Any | None = None,
        stt_engine: Any | None = None,
        tts_engine: Any | None = None,
    ):
        self.config = config
        self.llm = llm_client
        self.conv_store = conversation_store
        self.episodic = episodic_memory
        self.longterm = long_term_memory
        self.rag = rag
        self.tools = tool_registry
        self.personality = personality_builder
        self.stt = stt_engine
        self.tts = tts_engine

        self._sessions: dict[str, dict] = {}
        self._default_session_id = str(uuid.uuid4())

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(self) -> gr.Blocks:
        """Gradio Blocks arayüzünü oluştur ve döndür."""
        theme = gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="slate",
            font=["Inter", "sans-serif"],
        ).set(
            body_background_fill="*neutral_50",
            block_background_fill="*neutral_100",
            block_border_width="0px",
            button_primary_background_fill="*primary_600",
        )

        with gr.Blocks(
            theme=theme,
            title="TurkishJARVIS",
            css="""
            .jarvis-header { text-align: center; padding: 1rem; }
            .jarvis-header h1 { margin: 0; font-weight: 700; color: #2563eb; }
            .jarvis-header p { margin: 0; color: #64748b; }
            .settings-panel { border-left: 1px solid #e2e8f0; padding-left: 1rem; }
            """,
        ) as demo:
            self._render_header()
            with gr.Row():
                with gr.Column(scale=3):
                    self._render_chat_panel()
                with gr.Column(scale=1, min_width=250):
                    self._render_settings_panel()

        return demo

    # ------------------------------------------------------------------
    # Render helpers
    # ------------------------------------------------------------------

    def _render_header(self) -> None:
        with gr.Row(elem_classes="jarvis-header"):
            gr.Markdown(
                "# 🤖 TurkishJARVIS\n"
                "> Kişisel AI Asistanınız — Metin ve sesle etkileşim."
            )

    def _render_chat_panel(self) -> None:
        session_state = gr.State(value=self._default_session_id)

        chatbot = gr.Chatbot(
            label="Mesaj Geçmişi",
            type="messages",
            height=500,
            bubble_full_width=False,
            show_copy_button=True,
        )

        with gr.Row():
            audio_input = gr.Audio(
                sources=["microphone"],
                type="filepath",
                label="🎤 Sesli Mesaj",
                waveform_options=gr.WaveformOptions(
                    waveform_color="#2563eb",
                    waveform_progress_color="#1e40af",
                ),
            )
            audio_output = gr.Audio(
                label="🔊 Sesli Yanıt",
                autoplay=False,
                interactive=False,
            )

        msg_input = gr.Textbox(
            placeholder="Jarvis'e bir şeyler söyleyin...",
            label="Metin Girişi",
            show_label=False,
            lines=1,
            max_lines=3,
        )

        with gr.Row():
            submit_btn = gr.Button("Gönder", variant="primary", scale=4)
            clear_btn = gr.Button("Temizle", variant="secondary", scale=1)

        status = gr.Markdown("")

        # Events
        submit_btn.click(
            fn=self._on_text_submit,
            inputs=[msg_input, chatbot, session_state],
            outputs=[chatbot, msg_input, status, audio_output, session_state],
        )

        msg_input.submit(
            fn=self._on_text_submit,
            inputs=[msg_input, chatbot, session_state],
            outputs=[chatbot, msg_input, status, audio_output, session_state],
        )

        audio_input.stop_recording(
            fn=self._on_audio_submit,
            inputs=[audio_input, chatbot, session_state],
            outputs=[chatbot, status, audio_output, session_state],
        )

        clear_btn.click(
            fn=self._on_clear,
            inputs=[session_state],
            outputs=[chatbot, status, session_state],
        )

    def _render_settings_panel(self) -> None:
        with gr.Column(elem_classes="settings-panel"):
            gr.Markdown("### ⚙️ Ayarlar")

            voice_toggle = gr.Checkbox(
                label="Sesli Yanıt",
                value=True,
                info="Yanıtları sesli olarak duyur.",
            )

            personality_dropdown = gr.Dropdown(
                choices=list(self.PERSONALITY_OPTIONS.keys()),
                value="professional_friendly",
                label="Kişilik",
                info="Jarvis'in iletişim tarzı.",
            )

            voice_name = gr.Textbox(
                label="Asistan Adı",
                value=self.config.voice_name if self.config else "Jarvis",
                max_lines=1,
            )

            gr.Markdown("### 📊 Oturum")
            session_info = gr.Markdown("Oturum: `default`")

            # Store settings in session for later use
            settings_state = gr.State(
                {
                    "voice_enabled": True,
                    "personality": "professional_friendly",
                    "voice_name": self.config.voice_name if self.config else "Jarvis",
                }
            )

            voice_toggle.change(
                fn=lambda v, s: {**s, "voice_enabled": v},
                inputs=[voice_toggle, settings_state],
                outputs=[settings_state],
            )
            personality_dropdown.change(
                fn=lambda p, s: {**s, "personality": p},
                inputs=[personality_dropdown, settings_state],
                outputs=[settings_state],
            )
            voice_name.change(
                fn=lambda n, s: {**s, "voice_name": n},
                inputs=[voice_name, settings_state],
                outputs=[settings_state],
            )

            gr.Markdown("---")
            gr.Markdown(
                "**Kısayollar**\n"
                "- `Enter` → Gönder\n"
                "- `Shift+Enter` → Yeni satır\n"
                "- Mikrofon simgesine tıkla → Sesli mesaj"
            )

    # ------------------------------------------------------------------
    # Event handlers (sync wrappers → async core)
    # ------------------------------------------------------------------

    async def _on_text_submit(
        self,
        message: str,
        history: list,
        session_id: str,
    ) -> tuple[list, str, str, str | None, str]:
        if not message or not message.strip():
            return history, "", "*Boş mesaj*", None, session_id

        history = history or []
        history.append({"role": "user", "content": message.strip()})

        try:
            response = await self._process_message(
                message=message.strip(),
                session_id=session_id,
                enable_voice=False,
            )
        except Exception as exc:
            logger.exception("Text submit error")
            response = {"response": f"Üzgünüm, bir hata oluştu: {exc}", "voice_url": None}

        assistant_msg = response.get("response", "Yanıt alınamadı.")
        history.append({"role": "assistant", "content": assistant_msg})

        voice_url = response.get("voice_url")
        tool_calls = response.get("tool_calls_used", [])
        tool_info = f" *(Araçlar: {', '.join(tool_calls)})*" if tool_calls else ""

        return (
            history,
            "",
            f"✅ Yanıt alındı.{tool_info}",
            voice_url,
            response.get("session_id", session_id),
        )

    async def _on_audio_submit(
        self,
        audio_path: str | None,
        history: list,
        session_id: str,
    ) -> tuple[list, str, str | None, str]:
        if not audio_path or not os.path.exists(audio_path):
            return history, "❌ Ses dosyası bulunamadı.", None, session_id

        # STT
        transcript = ""
        if self.stt is not None:
            try:
                transcript = await self.stt.transcribe(audio_path)
            except Exception as exc:
                logger.exception("STT error")
                return history, f"❌ Ses tanıma hatası: {exc}", None, session_id
        else:
            transcript = "[Sesli mesaj — STT motoru mevcut değil]"

        history = history or []
        history.append({"role": "user", "content": f"🎤 {transcript}"})

        try:
            response = await self._process_message(
                message=transcript,
                session_id=session_id,
                enable_voice=True,
            )
        except Exception as exc:
            logger.exception("Audio submit error")
            response = {"response": f"Üzgünüm, bir hata oluştu: {exc}", "voice_url": None}

        assistant_msg = response.get("response", "Yanıt alınamadı.")
        history.append({"role": "assistant", "content": assistant_msg})

        voice_url = response.get("voice_url")
        return (
            history,
            f"✅ Sesli mesaj işlendi: \"{transcript}\"",
            voice_url,
            response.get("session_id", session_id),
        )

    async def _on_clear(self, session_id: str) -> tuple[list, str, str]:
        if self.conv_store is not None:
            try:
                self.conv_store.clear(session_id)
            except Exception:
                pass
        return [], "Sohbet temizlendi.", str(uuid.uuid4())

    # ------------------------------------------------------------------
    # Core processing
    # ------------------------------------------------------------------

    async def _process_message(
        self,
        message: str,
        session_id: str,
        enable_voice: bool = False,
    ) -> dict:
        """Mesajı işle ve yanıt döndür.

        Bu metod main.py'deki chat endpoint'i ile aynı pipeline'ı izler.
        """
        from fastapi import HTTPException

        if not self.llm:
            return {
                "response": "LLM istemcisi henüz yapılandırılmamış.",
                "session_id": session_id,
                "tool_calls_used": [],
                "voice_url": None,
            }

        # 1. Session yönetimi
        if not session_id:
            session_id = str(uuid.uuid4())

        # 2. Konuşma geçmişi
        history: list[dict] = []
        if self.conv_store is not None:
            try:
                history = self.conv_store.get_history(session_id, limit=20)
            except Exception:
                logger.exception("History fetch error")

        # 3. Episodic memory araması
        episodic_context = ""
        if self.episodic is not None:
            try:
                memories = self.episodic.search(message, k=3)
                if memories:
                    episodic_context = "\n".join(
                        f"- {m.get('text', m)}" for m in memories
                    )
            except Exception:
                logger.exception("Episodic search error")

        # 4. Long-term tercihler
        user_prefs: dict = {}
        if self.longterm is not None:
            try:
                user_prefs = self.longterm.get_all_preferences(session_id)
            except Exception:
                logger.exception("Preferences fetch error")

        # 5. Tool schemas
        tool_schemas: list[dict] = []
        if self.tools is not None:
            try:
                tool_schemas = self.tools.get_schemas()
            except Exception:
                logger.exception("Tool schemas error")

        # 6. Sistem prompt
        system_prompt = "Sen TurkishJARVIS'sin. Kullanıcıya yardımcı ol."
        if self.personality is not None:
            try:
                system_prompt = self.personality.build(
                    user_preferences=user_prefs,
                    memory_context=episodic_context,
                    tool_schemas=tool_schemas,
                )
            except Exception:
                logger.exception("System prompt build error")

        # 7. LLM messages
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": message})

        # 8. LLM çağrısı
        try:
            llm_result = await self.llm.chat(messages, tools=tool_schemas or None)
        except Exception as exc:
            logger.exception("LLM chat error")
            raise HTTPException(status_code=503, detail=f"LLM hatası: {exc}")

        content = llm_result.get("content", "")
        tool_calls = llm_result.get("tool_calls") or []
        tool_names_used: list[str] = []

        # 9. Tool çağrıları
        if tool_calls and self.tools is not None:
            for tc in tool_calls:
                name = tc.get("function", {}).get("name") if isinstance(tc, dict) else getattr(tc, "function", {}).get("name", "")
                if not name:
                    continue
                arguments = tc.get("function", {}).get("arguments", {}) if isinstance(tc, dict) else getattr(getattr(tc, "function", None), "arguments", {})
                if isinstance(arguments, str):
                    import json
                    arguments = json.loads(arguments)
                try:
                    tool_result = await self.tools.execute(name, arguments)
                    tool_names_used.append(name)
                    messages.append({
                        "role": "tool",
                        "name": name,
                        "content": str(tool_result),
                    })
                except Exception:
                    logger.exception("Tool execution error: %s", name)
                    messages.append({
                        "role": "tool",
                        "name": name,
                        "content": "Araç çalıştırma hatası.",
                    })

            # Tool sonuçlarıyla tekrar LLM
            try:
                llm_result = await self.llm.chat(messages, tools=tool_schemas or None)
                content = llm_result.get("content", "")
            except Exception as exc:
                logger.exception("LLM re-chat error")
                content = f"Araç sonuçları işlenirken hata: {exc}"

        # 10. Konuşmayı kaydet
        if self.conv_store is not None:
            try:
                self.conv_store.add_message(session_id, "user", message)
                self.conv_store.add_message(session_id, "assistant", content, tool_calls=tool_names_used)
            except Exception:
                logger.exception("Conversation save error")

        # 11. TTS (ses üretimi)
        voice_url: str | None = None
        if enable_voice and self.tts is not None and content:
            try:
                voice_path = await self.tts.synthesize(content)
                if voice_path and os.path.exists(voice_path):
                    voice_url = voice_path
            except Exception:
                logger.exception("TTS error")

        return {
            "response": content,
            "session_id": session_id,
            "tool_calls_used": tool_names_used,
            "voice_url": voice_url,
        }

    def get_blocks(self) -> gr.Blocks:
        """Alias for build()."""
        return self.build()
