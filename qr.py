from pathlib import Path
import asyncio
import os
import platform
import subprocess
import qrcode

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Header, Footer, Input, Button, Static, Label
from textual.reactive import reactive


SAVE_DIR = Path("qrcodes")
if not SAVE_DIR.exists():
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
else:
    if not SAVE_DIR.is_dir():
        raise NotADirectoryError(f"{SAVE_DIR} exists and is not a directory.")


def open_path(path: Path):
    system = platform.system()

    if system == "Windows":
        os.startfile(path)
    elif system == "Darwin":
        subprocess.run(["open", str(path)])
    else:
        subprocess.run(["xdg-open", str(path)])


def qr_to_terminal_blocks(data: str) -> str:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=1,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)

    matrix = qr.get_matrix()

    lines = []
    for y in range(0, len(matrix), 2):
        line = ""
        top = matrix[y]
        bottom = matrix[y + 1] if y + 1 < len(matrix) else [False] * len(top)

        for x in range(len(top)):
            if top[x] and bottom[x]:
                line += "█"
            elif top[x] and not bottom[x]:
                line += "▀"
            elif not top[x] and bottom[x]:
                line += "▄"
            else:
                line += " "
        lines.append(line)

    return "\n".join(lines)


class QRApp(App):
    CSS = """
    Screen {
    background: #050014;
    color: #00ffe1;
    }

    Header,
    Footer {
        background: #140024;
        color: #ff2bd6;
    }

    #main {
        width: 100%;
        height: 100%;
        padding: 1;
    }

    #layout {
        width: 100%;
        height: 100%;
    }

    #left_panel {
        width: 34%;
        min-width: 34;
        height: 100%;
        border: double #ff2bd6;
        background: #09001f;
        padding: 1;
    }

    #right_panel {
        width: 66%;
        height: 100%;
        border: double #00ffe1;
        background: #070018;
        padding: 1;
        margin-left: 1;
    }

    #title {
        text-align: center;
        text-style: bold;
        color: #ffff00;
    }

    #qr_title {
        text-align: center;
        text-style: bold;
        color: #39ff14;
    }

    Input {
        width: 100%;
        border: tall #00ffe1;
        background: #10002b;
        color: #ffffff;
        margin-bottom: 1;
    }

    Button {
        width: 100%;
        margin-bottom: 1;
        background: #1a0033;
        color: #00ffe1;
        border: tall #00ffe1;
    }

    Button:hover {
        background: #ff2bd6;
        color: #050014;
    }

    #qrbox {
    width: 100%;
    height: 1fr;
    border: heavy #39ff14;
    background: #f5f5f5;
    color: #000000;
    content-align: center middle;
    text-align: center;
    overflow: hidden;
    }

    #status {
        height: 1;
        color: #39ff14;
    }

    .warning {
        color: #ff5555;
    }

    .glow {
        color: #ffff00;
        text-style: bold;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+g", "generate", "Generate QR"),
    ]

    saved_path: Path | None = None
    build_step = reactive(0)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Container(id="main"):
            with Horizontal(id="layout"):

                with Container(id="left_panel"):
                    yield Static("◆ CYBER QR ◆", id="title")

                    yield Label("URL / Data")
                    yield Input(placeholder="https://presoft.com.my", id="url")

                    yield Label("PNG File Name")
                    yield Input(placeholder="example.png", id="filename")

                    yield Button("Generate QR", id="generate")
                    yield Button("Open PNG", id="open_file")
                    yield Button("Open Folder", id="open_folder")
                    yield Button("Exit", id="exit")

                with Container(id="right_panel"):
                    # yield Static("QR Preview", id="qr_title")
                    yield Static("", id="qrbox")
                    yield Static("Saved path will appear here.", id="status")

        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        if button_id == "generate":
            await self.generate_qr()

        elif button_id == "open_file":
            if self.saved_path and self.saved_path.exists():
                open_path(self.saved_path)
            else:
                self.set_status("No QR PNG generated yet.", warning=True)

        elif button_id == "open_folder":
            SAVE_DIR.mkdir(exist_ok=True)
            open_path(SAVE_DIR.resolve())

        elif button_id == "exit":
            self.exit()

    async def action_generate(self) -> None:
        await self.generate_qr()

    def set_status(self, message: str, warning: bool = False):
        status = self.query_one("#status", Static)
        status.update(message)
        status.set_class(warning, "warning")

    async def generate_qr(self):
        url = self.query_one("#url", Input).value.strip()
        filename = self.query_one("#filename", Input).value.strip()

        if not url:
            self.set_status("URL cannot be empty.", warning=True)
            return

        if not filename:
            self.set_status("Filename cannot be empty.", warning=True)
            return

        if not filename.lower().endswith(".png"):
            filename += ".png"

        SAVE_DIR.mkdir(exist_ok=True)
        self.saved_path = (SAVE_DIR / filename).resolve()

        qrbox = self.query_one("#qrbox", Static)

        loading_frames = [
            "Initializing neon matrix...",
            "Encoding URL signal...",
            "Drawing QR modules...",
            "Injecting CRT glow...",
            "Saving PNG file...",
        ]

        for frame in loading_frames:
            self.set_status(frame)
            qrbox.update(self.fake_build_frame())
            await asyncio.sleep(0.25)

        img_qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=12,
            border=4,
        )

        img_qr.add_data(url)
        img_qr.make(fit=True)

        img = img_qr.make_image(
            fill_color="black",
            back_color="white",
        )

        img.save(self.saved_path)

        terminal_qr = qr_to_terminal_blocks(url)
        qrbox.update(terminal_qr)

        self.set_status(f"QR generated: {self.saved_path}")

    def fake_build_frame(self) -> str:
        self.build_step += 1
        width = 28
        rows = []

        for y in range(14):
            row = ""
            for x in range(width):
                if (x * y + self.build_step) % 5 == 0:
                    row += "██"
                else:
                    row += "  "
            rows.append(row)

        return "\n".join(rows)


if __name__ == "__main__":
    QRApp().run()
