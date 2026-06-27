import config
import json

from pathlib import Path

from main import MachineTwin

class TestMachineTwin:

    def __init__(self):
        self.FIRST_BASE_DIR = config.BASE_DIR
        self.FIRST_DATA_DIR = config.DATA_DIR
        self.FIRST_LOGS_DIR = config.LOGS_DIR
        self.FIRST_DOCS_DIR = config.DOCS_DIR
        
        # set test folder
        config.BASE_DIR = Path(__file__).parent / "test_folder"
        config.DATA_DIR = config.BASE_DIR / "data"
        config.LOGS_DIR = config.BASE_DIR / "logs"
        config.DOCS_DIR = config.BASE_DIR / "docs-machines"
    
        # rm test folder files if exists
        if config.BASE_DIR.exists():
            for file in config.BASE_DIR.glob("**/*"):
                if file.is_file():
                    file.unlink()
        else:
            config.BASE_DIR.mkdir(parents=True, exist_ok=True)

    def rag_archives(self, archives):
        self.rag_archives = archives
        
        # copy archives to the docs-machines folder
        for archive in archives:
            archive_path = self.FIRST_BASE_DIR / Path(archive)
            dest_path = config.DOCS_DIR / archive_path.name
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            if not dest_path.exists():
                dest_path.write_text(archive_path.read_text())

    def sim_archives(self, sim_archives):
        self.sim_archives = sim_archives
        
        # copy sim_archives to the data folder
        for file_name, content in sim_archives.items():
            dest_path = config.DATA_DIR / file_name
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, dict):
                dest_path.write_text(json.dumps(content))
            else:
                dest_path.write_text(content)
                
    def load(self):
        # loads rag and agent
        self.twin = MachineTwin()
        

    def input(self, msg, conversation_id=None):
        traces_path = config.LOGS_DIR / "traces.jsonl"
        offset = traces_path.stat().st_size if traces_path.exists() else 0

        chat = self.twin.process(msg, conversation_id=conversation_id)

        trace = []
        if traces_path.exists():
            with open(traces_path, "r", encoding="utf-8") as f:
                f.seek(offset)
                for line in f:
                    line = line.strip()
                    if line:
                        trace.append(json.loads(line))

        return chat, trace

    










