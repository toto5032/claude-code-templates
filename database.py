import sqlite3
import os
from datetime import datetime


class TemplateDB:
    def __init__(self, db_path=None):
        if db_path is None:
            db_dir = os.environ.get('DB_DIR', os.path.dirname(__file__))
            db_path = os.path.join(db_dir, 'templates.db')
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        conn = self._get_conn()
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT DEFAULT 'new',
                created_at DATETIME DEFAULT (datetime('now', 'localtime')),
                updated_at DATETIME DEFAULT (datetime('now', 'localtime')),
                project_name TEXT,
                tech_stack TEXT,
                work_files TEXT,
                goal TEXT,
                background TEXT,
                requirements TEXT,
                input_desc TEXT,
                output_desc TEXT,
                restrictions TEXT,
                ref_patterns TEXT
            );

            CREATE TABLE IF NOT EXISTS requirement_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                category TEXT DEFAULT 'original',
                sort_order INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE CASCADE
            );
        ''')
        conn.commit()
        conn.close()

    def get_all(self):
        conn = self._get_conn()
        rows = conn.execute('SELECT * FROM templates ORDER BY updated_at DESC').fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get(self, template_id):
        conn = self._get_conn()
        row = conn.execute('SELECT * FROM templates WHERE id = ?', (template_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def create(self, data):
        conn = self._get_conn()
        cur = conn.execute(
            '''INSERT INTO templates (name, type, project_name, tech_stack, work_files,
               goal, background, requirements, input_desc, output_desc, restrictions, ref_patterns)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (data.get('name', ''), data.get('type', 'new'), data.get('project_name', ''),
             data.get('tech_stack', ''), data.get('work_files', ''),
             data.get('goal', ''), data.get('background', ''), data.get('requirements', ''),
             data.get('input_desc', ''), data.get('output_desc', ''),
             data.get('restrictions', ''), data.get('ref_patterns', ''))
        )
        conn.commit()
        tid = cur.lastrowid
        conn.close()
        return tid

    def update(self, template_id, data):
        conn = self._get_conn()
        conn.execute(
            '''UPDATE templates SET name=?, type=?, project_name=?, tech_stack=?, work_files=?,
               goal=?, background=?, requirements=?, input_desc=?, output_desc=?,
               restrictions=?, ref_patterns=?, updated_at=datetime('now','localtime')
               WHERE id=?''',
            (data.get('name', ''), data.get('type', 'new'), data.get('project_name', ''),
             data.get('tech_stack', ''), data.get('work_files', ''),
             data.get('goal', ''), data.get('background', ''), data.get('requirements', ''),
             data.get('input_desc', ''), data.get('output_desc', ''),
             data.get('restrictions', ''), data.get('ref_patterns', ''), template_id)
        )
        conn.commit()
        conn.close()

    def delete(self, template_id):
        conn = self._get_conn()
        conn.execute('DELETE FROM requirement_items WHERE template_id = ?', (template_id,))
        conn.execute('DELETE FROM templates WHERE id = ?', (template_id,))
        conn.commit()
        conn.close()

    # --- requirement_items CRUD ---

    def get_requirements(self, template_id):
        conn = self._get_conn()
        rows = conn.execute(
            'SELECT * FROM requirement_items WHERE template_id = ? ORDER BY category, sort_order',
            (template_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def add_requirement(self, template_id, content, category='original'):
        conn = self._get_conn()
        max_order = conn.execute(
            'SELECT COALESCE(MAX(sort_order), -1) FROM requirement_items WHERE template_id = ?',
            (template_id,)
        ).fetchone()[0]
        conn.execute(
            'INSERT INTO requirement_items (template_id, content, category, sort_order) VALUES (?, ?, ?, ?)',
            (template_id, content, category, max_order + 1)
        )
        conn.execute(
            "UPDATE templates SET updated_at=datetime('now','localtime') WHERE id=?",
            (template_id,)
        )
        conn.commit()
        conn.close()

    def update_requirement(self, req_id, content, category=None):
        conn = self._get_conn()
        if category:
            conn.execute(
                'UPDATE requirement_items SET content=?, category=? WHERE id=?',
                (content, category, req_id)
            )
        else:
            conn.execute('UPDATE requirement_items SET content=? WHERE id=?', (content, req_id))
        conn.commit()
        conn.close()

    def delete_requirement(self, req_id):
        conn = self._get_conn()
        conn.execute('DELETE FROM requirement_items WHERE id=?', (req_id,))
        conn.commit()
        conn.close()

    def sync_requirements_from_text(self, template_id):
        """기존 requirements 텍스트 필드를 항목별로 마이그레이션"""
        t = self.get(template_id)
        if not t or not t.get('requirements'):
            return 0
        existing = self.get_requirements(template_id)
        if existing:
            return 0
        lines = [l.strip().lstrip('- ').strip() for l in t['requirements'].split('\n') if l.strip()]
        for i, line in enumerate(lines):
            if line:
                conn = self._get_conn()
                conn.execute(
                    'INSERT INTO requirement_items (template_id, content, category, sort_order) VALUES (?, ?, ?, ?)',
                    (template_id, line, 'original', i)
                )
                conn.commit()
                conn.close()
        return len(lines)

    def search(self, keyword):
        conn = self._get_conn()
        like = f'%{keyword}%'
        rows = conn.execute(
            '''SELECT * FROM templates
               WHERE name LIKE ? OR project_name LIKE ? OR tech_stack LIKE ? OR goal LIKE ?
               ORDER BY updated_at DESC''',
            (like, like, like, like)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def _build_requirements_text(self, template_id):
        items = self.get_requirements(template_id)
        if not items:
            t = self.get(template_id)
            return t.get('requirements', '') if t else ''
        categories = {}
        for item in items:
            cat = item['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(item['content'])
        parts = []
        cat_labels = {'original': '기존 요구사항', 'added': '추가 요구사항', 'modified': '수정 요구사항'}
        for cat in ['original', 'added', 'modified']:
            if cat in categories:
                if len(categories) > 1:
                    parts.append(f"### {cat_labels.get(cat, cat)}")
                for content in categories[cat]:
                    parts.append(f"- {content}")
        return '\n'.join(parts)

    def to_prompt(self, template_id):
        t = self.get(template_id)
        if not t:
            return None
        lines = [f"# {t['name']}"]
        if t['project_name']:
            lines.append(f"\n## 프로젝트명\n{t['project_name']}")
        if t['tech_stack']:
            lines.append(f"\n## 기술스택\n{t['tech_stack']}")
        if t['goal']:
            lines.append(f"\n## 목표\n{t['goal']}")
        if t['background']:
            lines.append(f"\n## 배경\n{t['background']}")
        req_text = self._build_requirements_text(template_id)
        if req_text:
            lines.append(f"\n## 요구사항\n{req_text}")
        if t['input_desc']:
            lines.append(f"\n## 입력\n{t['input_desc']}")
        if t['output_desc']:
            lines.append(f"\n## 산출물\n{t['output_desc']}")
        if t['restrictions']:
            lines.append(f"\n## 금지사항\n{t['restrictions']}")
        if t['ref_patterns']:
            lines.append(f"\n## 참고패턴\n{t['ref_patterns']}")
        if t['work_files']:
            lines.append(f"\n## 작업파일\n{t['work_files']}")
        return '\n'.join(lines)

    def to_claude_md(self, template_id):
        t = self.get(template_id)
        if not t:
            return None
        lines = [f"# {t['name']}", ""]
        if t['goal']:
            lines.append(f"이 프로젝트의 목표: {t['goal']}")
            lines.append("")
        if t['tech_stack']:
            lines.append(f"## 기술스택\n{t['tech_stack']}\n")
        req_text = self._build_requirements_text(template_id)
        if req_text:
            lines.append(f"## 요구사항\n{req_text}\n")
        if t['restrictions']:
            lines.append(f"## 금지사항\n{t['restrictions']}\n")
        if t['ref_patterns']:
            lines.append(f"## 참고패턴\n{t['ref_patterns']}\n")
        return '\n'.join(lines)

    def import_from_md(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        section_map = {
            '프로젝트명': 'project_name', '기술스택': 'tech_stack',
            '작업파일': 'work_files', '목표': 'goal', '배경': 'background',
            '요구사항': 'requirements', '입력': 'input_desc',
            '산출물': 'output_desc', '금지사항': 'restrictions',
            '참고패턴': 'ref_patterns'
        }
        data = {}
        current_key = None
        lines_buf = []
        for line in content.split('\n'):
            if line.startswith('# ') and not line.startswith('## '):
                data['name'] = line[2:].strip()
                continue
            if line.startswith('## '):
                if current_key:
                    data[current_key] = '\n'.join(lines_buf).strip()
                heading = line[3:].strip()
                current_key = section_map.get(heading)
                lines_buf = []
                continue
            if current_key is not None:
                lines_buf.append(line)
        if current_key:
            data[current_key] = '\n'.join(lines_buf).strip()
        if not data.get('name'):
            return None
        tid = self.create(data)
        if data.get('requirements'):
            cat_map = {'기존 요구사항': 'original', '추가 요구사항': 'added', '수정 요구사항': 'modified'}
            current_cat = 'original'
            for line in data['requirements'].split('\n'):
                stripped = line.strip()
                if stripped.startswith('### '):
                    heading = stripped[4:].strip()
                    current_cat = cat_map.get(heading, 'original')
                    continue
                content = stripped.lstrip('- ').strip()
                if content:
                    self.add_requirement(tid, content, current_cat)
        return tid
