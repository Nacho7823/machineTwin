import config
import json

from pathlib import Path

from main import MachineTwin

class TestMachineTwin:

    def __init__(self, base_folder, work_folder):
        self.FIRST_BASE_DIR = Path(base_folder)
        self.FIRST_DATA_DIR = self.FIRST_BASE_DIR / "data"
        self.FIRST_LOGS_DIR = self.FIRST_BASE_DIR / "logs"
        self.FIRST_DOCS_DIR = self.FIRST_BASE_DIR / "docs-machines"
        
        # set test folder
        self.work_dir = Path(work_folder)
        self.data_dir = self.work_dir / "data"
        self.logs_dir = self.work_dir / "logs"
        self.docs_dir = self.work_dir / "docs-machines"
        
        # Configure LOGS_DIR for the event trace logger which reads from config.LOGS_DIR
        config.LOGS_DIR = self.logs_dir
    
        # rm test folder files if exists
        if self.work_dir.exists():
            for file in self.work_dir.glob("**/*"):
                if file.is_file():
                    file.unlink()
        else:
            self.work_dir.mkdir(parents=True, exist_ok=True)

    def rag_archives(self, archives):
        self.rag_archives = archives
        
        # copy archives to the docs-machines folder
        for archive in archives:
            archive_path = self.FIRST_BASE_DIR / Path(archive)
            dest_path = self.docs_dir / archive_path.name
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            if not dest_path.exists():
                dest_path.write_text(archive_path.read_text())

    def sim_archives(self, sim_archives):
        self.sim_archives = sim_archives

        if "__machines__" in sim_archives:
            for machine_dir_name, archives in sim_archives["__machines__"].items():
                for file_name, content in archives.items():
                    dest_path = self.data_dir / machine_dir_name / file_name
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    if isinstance(content, dict):
                        dest_path.write_text(json.dumps(content))
                    else:
                        dest_path.write_text(content)
            return
        
        # Determine machine directory name from machine_current.json
        machine_current = sim_archives.get("machine_current.json", {})
        machine_id = machine_current.get("machine_id", "unknown")
        
        machine_dir_name = "unknown"
        if "T-100" in machine_id:
            machine_dir_name = "cooling_tower"
        elif "C-300" in machine_id:
            machine_dir_name = "compressor"
        elif "M-200" in machine_id:
            machine_dir_name = "electric_motor"
        else:
            machine_dir_name = machine_id.lower().replace("-", "_")
            
        # copy sim_archives to the machine data folder
        for file_name, content in sim_archives.items():
            dest_path = self.data_dir / machine_dir_name / file_name
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, dict):
                dest_path.write_text(json.dumps(content))
            else:
                dest_path.write_text(content)
                
    def load(self):
        # loads rag and agent
        self.twin = MachineTwin(data_dir=self.data_dir, docs_dir=self.docs_dir)
        

    def input(self, msg, conversation_id=None):
        traces_path = self.logs_dir / "traces.jsonl"
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

    









