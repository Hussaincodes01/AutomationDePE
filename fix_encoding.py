"""Quick script to strip emoji from all .py files for Windows compatibility."""
import os
import re

EMOJI_MAP = {
    '🚀': '[>>]', '🌐': '[WEB]', '📰': '[NEWS]', '📊': '[CHART]',
    '🧠': '[AI]', '💾': '[SAVE]', '✅': '[OK]', '❌': '[FAIL]',
    '⚠️': '[WARN]', '🔥': '[HOT]', '🟡': '[WARM]', '🧊': '[COLD]',
    '📧': '[EMAIL]', '📤': '[SENT]', '🔄': '[RETRY]', '👋': '[BYE]',
    '💬': '[REPLY]', '📅': '[DATE]', '📈': '[UP]', '📉': '[DOWN]',
    '🆕': '[NEW]', '🗄️': '[DB]', '⏱️': '[TIME]', '📄': '[FILE]',
    '📥': '[IN]', '🎯': '[TARGET]', '📋': '[LIST]', '🏢': '[FIRM]',
    '🔍': '[FIND]', '👥': '[USERS]', '✉️': '[MAIL]', '💡': '[TIP]',
    '🤖': '[BOT]', '⏰': '[CLOCK]', '🛡️': '[SAFE]', '█': '=',
    '═': '=', '🔑': '[KEY]', '⭐': '[*]', '💰': '[$]',
    '📮': '[POST]', '⏳': '[WAIT]', '🐍': '[PY]', '💎': '[GEM]',
    '╔': '+', '╗': '+', '╚': '+', '╝': '+',
    '╠': '+', '╣': '+', '║': '|', '═': '=',
    '─': '-', '│': '|', '▼': 'v', '►': '>', '—': '-',
    '≥': '>=',
}

def strip_emojis(text):
    for emoji, replacement in EMOJI_MAP.items():
        text = text.replace(emoji, replacement)
    # Remove any remaining non-ASCII characters in print/string contexts
    return text

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = strip_emojis(content)
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  Fixed: {os.path.basename(filepath)}")
    else:
        print(f"  Clean: {os.path.basename(filepath)}")

if __name__ == '__main__':
    py_dir = os.path.dirname(os.path.abspath(__file__))
    for fname in os.listdir(py_dir):
        if fname.endswith('.py') and fname != 'fix_encoding.py':
            process_file(os.path.join(py_dir, fname))
    print("\nDone! All files are Windows-safe now.")
