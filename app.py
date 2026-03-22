import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from database import TemplateDB

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'template-manager-secret-key')
db = TemplateDB()


@app.route('/')
def index():
    keyword = request.args.get('q', '')
    if keyword:
        templates = db.search(keyword)
    else:
        templates = db.get_all()
    stats = {
        'total': len(db.get_all()),
        'new': len([t for t in db.get_all() if t['type'] == 'new']),
    }
    return render_template('index.html', templates=templates, keyword=keyword, stats=stats)


@app.route('/template/new')
def template_new():
    return render_template('form.html', template=None)


@app.route('/template/<int:tid>')
def template_detail(tid):
    t = db.get(tid)
    if not t:
        flash('템플릿을 찾을 수 없습니다.', 'error')
        return redirect(url_for('index'))
    prompt_text = db.to_prompt(tid)
    claude_md = db.to_claude_md(tid)
    return render_template('detail.html', template=t, prompt_text=prompt_text, claude_md=claude_md)


@app.route('/template/<int:tid>/edit')
def template_edit(tid):
    t = db.get(tid)
    if not t:
        flash('템플릿을 찾을 수 없습니다.', 'error')
        return redirect(url_for('index'))
    return render_template('form.html', template=t)


@app.route('/api/template', methods=['POST'])
def api_create():
    data = request.json or request.form.to_dict()
    tid = db.create(data)
    if request.is_json:
        return jsonify({'id': tid, 'message': '템플릿이 생성되었습니다.'})
    flash('템플릿이 생성되었습니다.', 'success')
    return redirect(url_for('template_detail', tid=tid))


@app.route('/api/template/<int:tid>', methods=['PUT', 'POST'])
def api_update(tid):
    data = request.json or request.form.to_dict()
    db.update(tid, data)
    if request.is_json:
        return jsonify({'message': '템플릿이 수정되었습니다.'})
    flash('템플릿이 수정되었습니다.', 'success')
    return redirect(url_for('template_detail', tid=tid))


@app.route('/api/template/<int:tid>/delete', methods=['POST', 'DELETE'])
def api_delete(tid):
    db.delete(tid)
    if request.is_json:
        return jsonify({'message': '템플릿이 삭제되었습니다.'})
    flash('템플릿이 삭제되었습니다.', 'success')
    return redirect(url_for('index'))


@app.route('/api/template/<int:tid>/prompt')
def api_prompt(tid):
    text = db.to_prompt(tid)
    if not text:
        return jsonify({'error': '템플릿을 찾을 수 없습니다.'}), 404
    return jsonify({'prompt': text})


@app.route('/api/template/<int:tid>/claude-md')
def api_claude_md(tid):
    text = db.to_claude_md(tid)
    if not text:
        return jsonify({'error': '템플릿을 찾을 수 없습니다.'}), 404
    return jsonify({'claude_md': text})


@app.route('/api/import-excel', methods=['POST'])
def api_import_excel():
    if 'file' not in request.files:
        flash('파일을 선택해주세요.', 'error')
        return redirect(url_for('index'))
    f = request.files['file']
    if not f.filename.endswith('.xlsx'):
        flash('.xlsx 파일만 업로드할 수 있습니다.', 'error')
        return redirect(url_for('index'))
    tmp_path = os.path.join(os.path.dirname(__file__), 'tmp_upload.xlsx')
    f.save(tmp_path)
    try:
        count = db.import_from_excel(tmp_path)
        flash(f'{count}개 템플릿을 가져왔습니다.', 'success')
    except Exception as e:
        flash(f'가져오기 실패: {str(e)}', 'error')
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, port=5001)
