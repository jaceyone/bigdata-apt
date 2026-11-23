"""Compile a v2 paper into an isolated directory, then publish a verified PDF."""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid


def check_language(pdf, language):
    """Reject a missing/unreadable manuscript or prose dominated by the wrong language."""
    try:
        import pymupdf as fitz
    except ImportError:
        import fitz
    chinese = english = han_total = 0
    finished = False
    with fitz.open(pdf) as document:
        for page in document:
            lines = []
            sizes = {}
            for block in page.get_text('dict', sort=True)['blocks']:
                for line in block.get('lines', []):
                    spans = [span for span in line['spans'] if span['text'].strip()]
                    if not spans:
                        continue
                    # PDFLaTeX may emit spaces as separate spans; retain them.
                    text = ''.join(span['text'] for span in line['spans']).strip()
                    for span in spans:
                        size = round(span['size'] * 2) / 2
                        sizes[size] = sizes.get(size, 0) + len(span['text'])
                    lines.append((text, spans))
            body_size = max(sizes, key=sizes.get) if sizes else 0
            for index, (line, spans) in enumerate(lines):
                # Bibliographic originals and source code are allowed to keep their language.
                if re.fullmatch(r'(?:\d+[.\s]+)?(?:参考文献|References|Bibliography|附录(?:\s*[A-Z一二三四五六七八九十])?|Appendix(?:\s+[A-Z])?|Appendices)', line, re.I):
                    if index + 1 < len(lines) and re.fullmatch(r'\s*\d+\s*', lines[index + 1][0]):
                        continue  # A contents entry with a separate page number.
                    finished = True
                    break
                # The contest's fixed English headings are allowed in a Chinese paper.
                # Do not count bold/large heading lines as authored body prose.
                if len(line) < 180 and (all(span.get('flags', 0) & 16 for span in spans) or all(span['size'] > body_size * 1.12 for span in spans)):
                    continue
                han = len(re.findall(r'[\u3400-\u9fff]', line))
                words = re.findall(r"[A-Za-z][A-Za-z'-]+", line)
                if han >= 6 and han >= len(words):
                    chinese += 1
                    han_total += han
                elif len(words) >= 5 and sum(map(len, words)) >= 24:
                    english += 1
            if finished:
                break
    if not chinese and not english:
        raise RuntimeError('论文缺少可核对语言的正文文本，请补充正文或检查 PDF 文本层后再交付')
    # An English manuscript may contain a few Chinese names or notes; engine
    # compatibility must not turn those into a requirement to rewrite the text.
    valid = (han_total >= 20 and chinese >= english) if language == 'zh' else (english > 0 and chinese <= english * 0.25)
    if not valid:
        name = '中文' if language == 'zh' else '英文'
        raise RuntimeError('论文正文语言不符合本任务选择的' + name + '写作（中文正文行 ' + str(chinese) + '，英文正文行 ' + str(english) + '）；请按所选语言完成正文后重新编译，当前成果不能标记完成')
    return {'version': 1, 'valid': True, 'language': language, 'chineseLines': chinese, 'englishLines': english}


CODE_THEMES = {
    'color': {},
    'mono': {'keywordstyle': r'\bfseries', 'commentstyle': r'\itshape', 'stringstyle': ''},
    'large': {'basicstyle': r'\normalsize\ttfamily'},
    'serif': {'basicstyle': r'\small\rmfamily', 'keywordstyle': r'\bfseries',
              'commentstyle': r'\color{black!65}\itshape', 'stringstyle': r'\color{black!80}'},
    'compact': {'basicstyle': r'\footnotesize\ttfamily'},
    'minimal': {'basicstyle': r'\footnotesize\sffamily', 'frame': 'none', 'numbers': 'none',
                'keywordstyle': r'\color{black!65}\bfseries', 'commentstyle': r'\color{black!55}',
                'stringstyle': r'\color{black!65}'},
    'shadow': {'frame': 'shadowbox'},
    'dark': {'basicstyle': r'\small\ttfamily\color{white}', 'backgroundcolor': r'\color{black!90}',
             'keywordstyle': r'\color{cyan!80!white}\bfseries', 'commentstyle': r'\color{white!65!black}',
             'stringstyle': r'\color{orange!80!white}', 'numberstyle': r'\scriptsize\color{black!65}'},
    'noline': {'numbers': 'none'},
}


def code_theme_prelude(theme):
    if theme == 'document':
        return ''
    options = {
        'basicstyle': r'\small\ttfamily', 'keywordstyle': r'\color{blue!60!black}\bfseries',
        'commentstyle': r'\color{green!35!black}', 'stringstyle': r'\color{teal!75!black}',
        'numberstyle': r'\scriptsize\color{black!55}', 'rulecolor': r'\color{black!25}',
        'rulesepcolor': r'\color{black!18}', 'identifierstyle': '', 'backgroundcolor': '',
        'frame': 'single', 'numbers': 'left',
        **CODE_THEMES[theme],
    }
    settings = ','.join(key + '={' + value + '}' for key, value in options.items())
    # Listings has already read each external listing's local options at this hook.
    # Override only presentation, leaving its language, caption, line range and path intact.
    return (r'\AddToHook{begindocument/before}{\IfPackageLoadedTF{listings}{\RequirePackage{xcolor}'
            r'\AddToHook{cmd/lst@InputListing/before}{\lstset{' + settings + '}}}{}}')


def digest(file):
    h = hashlib.sha256()
    with open(file, 'rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def atomic_copy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(target.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        shutil.copy2(source, temp)
        os.replace(temp, target)
    finally:
        temp.unlink(missing_ok=True)


@contextmanager
def compiler_output_path(output):
    """Windows TeX's putenv cannot accept a Unicode output directory."""
    if os.name != 'nt' or str(output).isascii():
        yield output
        return
    import ctypes
    from ctypes import wintypes
    get_short = ctypes.WinDLL('kernel32', use_last_error=True).GetShortPathNameW
    get_short.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
    get_short.restype = wintypes.DWORD
    buffer = ctypes.create_unicode_buffer(32768)
    length = get_short(str(output), buffer, len(buffer))
    if 0 < length < len(buffer) and buffer.value.isascii():
        yield Path(buffer.value)
        return
    # Volumes with 8.3 names disabled still need an ASCII path. A temporary
    # junction keeps all actual build products inside the project's output dir.
    import _winapi
    alias_root = Path(os.environ.get('PROGRAMDATA', 'C:/ProgramData')) / 'Mrite' / 'tex-output'
    alias_root.mkdir(parents=True, exist_ok=True)
    if not str(alias_root).isascii():
        raise RuntimeError('无法创建 ASCII 编译目录别名：' + str(alias_root))
    alias = alias_root / uuid.uuid4().hex
    _winapi.CreateJunction(str(output), str(alias))
    try:
        yield alias
    finally:
        # rmdir removes the junction itself, never its target or build products.
        alias.rmdir()


def cache_directory(root, tex, binary, fast, code_theme):
    identity = [tex.relative_to(root).as_posix(), str(Path(binary).resolve()), Path(binary).stat().st_mtime_ns, fast]
    if code_theme != 'document':
        identity.append(code_theme)
    key = hashlib.sha256(json.dumps(identity).encode()).hexdigest()[:24]
    return root / '.mrite' / 'state' / 'latex-cache' / key


def copy_auxiliary(source, target):
    extensions = {'.aux', '.toc', '.out', '.lof', '.lot', '.nav', '.snm'}
    for current, dirs, files in os.walk(source):
        dirs[:] = [name for name in dirs if not (Path(current) / name).is_symlink()]
        for name in files:
            file = Path(current) / name
            if file.suffix.lower() in extensions and file.is_file() and not file.is_symlink():
                try:
                    atomic_copy(file, target / file.relative_to(source))
                except OSError:
                    # Auxiliary data is optional and must never block a build.
                    pass


def rebuild_format(binary, output):
    engine = Path(binary).stem.lower()
    if engine not in ('xelatex', 'pdflatex'):
        return None
    work = output / ('format-' + uuid.uuid4().hex)
    work.mkdir()
    result = subprocess.run([binary, '-ini', '-jobname=' + engine, '-progname=' + engine, '-etex', engine + '.ini'],
                            cwd=work, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
    generated = work / (engine + '.fmt')
    if result.returncode or not generated.is_file():
        raise RuntimeError(engine + ' 格式缓存重建失败：\n' + result.stdout.decode('utf-8', errors='replace')[-3000:])
    writable = os.environ.get('TEXMFVAR')
    if writable:
        kind = 'xetex' if engine == 'xelatex' else 'pdftex'
        cached = Path(writable) / 'web2c' / kind / generated.name
        try:
            cached.parent.mkdir(parents=True, exist_ok=True)
            atomic_copy(generated, cached)
        except OSError:
            pass  # The current compile can use its own rebuilt format.
    return {**os.environ, 'TEXFORMATS': str(work) + os.pathsep + os.environ.get('TEXFORMATS', '')}


def language_engine_fallback(engine, error):
    name = Path(str(engine)).stem.lower()
    if name == 'pdflatex':
        if re.search(r'(?:inputenc|LaTeX)\s+Error:\s*Unicode character|Unicode character[^\n]*(?:U\+[0-9A-F]+|not set up)', error, re.I):
            return {'version': 1, 'automatic': True, 'from': name, 'to': 'xelatex', 'reason': 'unicode'}
        if re.search(r'(?:requires?|must use|(?:can )?only be used (?:with|under)|only works? (?:with|under))\s+(?:(?:either|the)\s+)?(?:XeTeX|XeLaTeX)|(?:XeTeX|XeLaTeX)\s+(?:engine\s+)?(?:is\s+)?required|CTeX fontset[\s\S]{0,100}unavailable in current mode', error, re.I):
            return {'version': 1, 'automatic': True, 'from': name, 'to': 'xelatex', 'reason': 'requires-xetex'}
    if name == 'xelatex' and re.search(r'(?:requires?|must use|(?:can )?only be used (?:with|under)|only works? (?:with|under))\s+(?:the\s+)?(?:pdfTeX|pdfLaTeX)|(?:pdfTeX|pdfLaTeX)\s+(?:engine\s+)?(?:is\s+)?required', error, re.I):
        return {'version': 1, 'automatic': True, 'from': name, 'to': 'pdflatex', 'reason': 'requires-pdftex'}
    return None


def alternate_engine(engine, name):
    binary = Path(str(engine))
    sibling = binary.with_name(name + binary.suffix)
    return str(sibling) if sibling.is_file() else shutil.which(name)


def previous_engine_fallback(root, source, engine):
    for file in (compatibility_file(root, source), root / '.mrite/state/paper-build.json'):
        try:
            record = json.loads(file.read_text(encoding='utf-8-sig'))
            fallback = record.get('engineFallback', {})
            allowed = {('pdflatex', 'xelatex', 'unicode'), ('pdflatex', 'xelatex', 'requires-xetex'), ('xelatex', 'pdflatex', 'requires-pdftex')}
            if (record.get('tex') == source.relative_to(root).as_posix() and record.get('engine') == Path(str(engine)).stem.lower() == fallback.get('to') and
                    fallback.get('version') == 1 and fallback.get('automatic') is True and
                    (fallback.get('from'), fallback.get('to'), fallback.get('reason')) in allowed):
                return fallback
        except (OSError, ValueError, TypeError, AttributeError):
            pass
    return None


def compatibility_file(root, source):
    identity = hashlib.sha256(source.relative_to(root).as_posix().encode('utf-8')).hexdigest()
    return root / '.mrite/cache/engine-compatibility' / (identity + '.json')


def remember_engine_fallback(root, source, result):
    if not result.get('engineFallback'):
        return result
    try:
        file = compatibility_file(root, source)
        file.parent.mkdir(parents=True, exist_ok=True)
        temporary = file.with_suffix('.' + uuid.uuid4().hex + '.tmp')
        temporary.write_text(json.dumps({'tex': source.relative_to(root).as_posix(), 'engine': result['engine'], 'engineFallback': result['engineFallback']}), encoding='utf-8')
        os.replace(temporary, file)
        result['compatibilitySaved'] = True
    except OSError:
        result['compatibilitySaved'] = False
    return result


def cjk_compatibility_prelude(tex):
    if (tex.parent / 'fonts/SourceHanSerifCN-Regular.otf').is_file():
        font = r'\setCJKmainfont[Path=fonts/]{SourceHanSerifCN-Regular.otf}'
    else:
        font = r'\IfFontExistsTF{SimSun}{\setCJKmainfont{SimSun}}{\IfFontExistsTF{Microsoft YaHei}{\setCJKmainfont{Microsoft YaHei}}{\setCJKmainfont{FandolSong-Regular}}}'
    # Load only when the document did not configure xeCJK itself. Keep source
    # files, custom package options and font choices untouched.
    return r'\AddToHook{env/document/before}{\IfPackageLoadedTF{xeCJK}{}{\RequirePackage{xeCJK}' + font + '}}'


def run_engine(tex, binary, output, single_pass, fast, code_theme, cjk_compatibility=False):
    is_latexmk = Path(binary).stem.lower() == 'latexmk'
    prelude = (r'\PassOptionsToPackage{draft}{graphicx}' if fast else '') + code_theme_prelude(code_theme)
    if cjk_compatibility:
        prelude += cjk_compatibility_prelude(tex)
    if prelude and is_latexmk:
        raise RuntimeError('快速编译或切换代码主题时请选择 XeLaTeX 或 PDFLaTeX')
    logs = []
    with compiler_output_path(output) as compiler_output:
        args = [binary] + (['-xelatex'] if is_latexmk else []) + [
            '-recorder', '-synctex=1', '-interaction=nonstopmode', '-halt-on-error',
            '-output-directory=' + str(compiler_output)]
        if prelude:
            args.extend(['-jobname=' + tex.stem, prelude + r'\input{"' + tex.name + '"}'])
        else:
            args.append(tex.name)
        engine_env = None
        for _ in range(1 if fast or single_pass or is_latexmk else 2):
            result = subprocess.run(args, cwd=tex.parent, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600, env=engine_env)
            log = result.stdout.decode('utf-8', errors='replace')
            if result.returncode and engine_env is None and ('Fatal format file error' in log or 'made by different executable version' in log):
                engine_env = rebuild_format(binary, compiler_output)
                if engine_env:
                    logs.append(log)
                    result = subprocess.run(args, cwd=tex.parent, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600, env=engine_env)
                    log = result.stdout.decode('utf-8', errors='replace')
            logs.append(log)
            (output / 'build.log').write_text('\n'.join(logs), encoding='utf-8')
            if result.returncode:
                raise RuntimeError(log[-4000:] or 'LaTeX 编译失败')
    generated = output / (tex.stem + '.pdf')
    if not generated.is_file():
        raise RuntimeError('编译未生成PDF')
    with generated.open('rb') as stream:
        header = stream.read(5)
        stream.seek(max(0, generated.stat().st_size - 4096))
        tail = stream.read()
    if header != b'%PDF-' or b'%%EOF' not in tail:
        raise RuntimeError('编译产生不完整PDF，保留原有PDF')
    return generated


def publish_pdf(generated, target):
    atomic_copy(generated, target)
    synctex = generated.with_suffix('.synctex.gz')
    if synctex.is_file():
        atomic_copy(synctex, target.with_suffix('.synctex.gz'))


def _build(tex, root, engine, single_pass, fast, cache, code_theme, fallback=None):
    if not tex.is_file() or root / '论文' not in tex.parents:
        raise RuntimeError('论文源文件不存在或路径不在论文目录内')
    binary = str(engine) if Path(engine).is_file() else shutil.which(engine)
    if not binary:
        raise RuntimeError('找不到 LaTeX 编译引擎')
    auxiliary = cache_directory(root, tex, binary, fast, code_theme) if cache else None
    if fast:
        preview_dir = tex.parent / '临时' / '快速编译'
        preview_dir.mkdir(parents=True, exist_ok=True)
        target = preview_dir / (tex.stem + '.pdf')
        with tempfile.TemporaryDirectory(prefix='run-', dir=preview_dir) as directory:
            output = Path(directory)
            if auxiliary is not None:
                copy_auxiliary(auxiliary, output)
            generated = run_engine(tex, binary, output, single_pass, fast, code_theme, bool(fallback and fallback['to'] == 'xelatex'))
            publish_pdf(generated, target)
            if auxiliary is not None:
                copy_auxiliary(output, auxiliary)
        return {'success': True, 'pdfPath': str(target), 'draft': True, 'engine': Path(binary).stem.lower(), **({'engineFallback': fallback} if fallback else {})}

    paper = tex.parent
    output = root / '论文' / '临时' / '编译' / (tex.stem + '-' + uuid.uuid4().hex[:10])
    output.mkdir(parents=True)
    excluded = {'测试', '临时', '临时数据', '中间产物', '临时产物', '中间数据', '.mrite', '__pycache__'}
    initial = {}
    for current, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in excluded and not d.startswith('.')]
        for name in files:
            file = Path(current) / name
            if file != tex.with_suffix('.pdf'):
                initial[str(file.resolve())] = digest(file)
    for pointer in (root / '求解').glob('问题*/中间数据/当前版本.json'):
        initial[str(pointer.resolve())] = digest(pointer)
    if auxiliary is not None:
        copy_auxiliary(auxiliary, output)
    generated = run_engine(tex, binary, output, single_pass, fast, code_theme, bool(fallback and fallback['to'] == 'xelatex'))
    language_check = None
    language_file = root / '.mrite/state/writing-language.json'
    if tex == root / '论文/论文.tex' and language_file.is_file():
        language = json.loads(language_file.read_text(encoding='utf-8-sig')).get('language')
        if language in ('zh', 'en'):
            language_check = check_language(generated, language)
    recorder = output / (tex.stem + '.fls')
    if not recorder.is_file():
        raise RuntimeError('缺少编译依赖记录，保留原有PDF')
    dependencies = {tex}
    for line in recorder.read_text(encoding='utf-8', errors='replace').splitlines():
        if not line.startswith('INPUT '):
            continue
        file = Path(line[6:].strip().strip('"'))
        file = (file if file.is_absolute() else paper / file).resolve()
        if root in file.parents and file.is_file() and not any(part in excluded for part in file.relative_to(root).parts):
            dependencies.add(file)
    for file in list(dependencies):
        parts = file.relative_to(root).parts
        if len(parts) >= 3 and parts[0] == '求解' and parts[1].startswith('问题'):
            pointer = root / '求解' / parts[1] / '中间数据' / '当前版本.json'
            if pointer.is_file():
                dependencies.add(pointer)
    recorded = []
    for file in sorted(dependencies):
        value = digest(file)
        before = initial.get(str(file))
        if before is None or before != value:
            raise RuntimeError('编译期间源文件发生变化，请重新编译：' + str(file.relative_to(root)))
        recorded.append({'path': file.relative_to(root).as_posix(), 'sha256': value})
    target = tex.with_suffix('.pdf')
    record = {'version': 2, 'engine': Path(binary).stem.lower(), 'tex': tex.relative_to(root).as_posix(), 'pdf': target.relative_to(root).as_posix(),
              'pdfHash': digest(generated), 'dependencies': recorded, 'compiledAt': time.time()}
    if language_check is not None:
        record['languageCheck'] = language_check
    if fallback:
        record['engineFallback'] = fallback
    publish_pdf(generated, target)
    record_path = root / '.mrite' / 'state' / 'paper-build.json'
    record_path.parent.mkdir(parents=True, exist_ok=True)
    temp = record_path.with_suffix('.json.tmp')
    temp.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(temp, record_path)
    if auxiliary is not None:
        copy_auxiliary(output, auxiliary)
    return {'success': True, 'pdfPath': str(target), 'engine': record['engine'], **({'engineFallback': fallback} if fallback else {})}


def build(tex, engine=None, single_pass=False, fast=False, cache=False, legacy_workspace=None, code_theme='document'):
    source = Path(tex).resolve()
    root = Path(legacy_workspace).resolve() if legacy_workspace else next((p for p in source.parents if (p / '.mrite' / 'project.json').is_file()), None)
    if not legacy_workspace and (root is None or json.loads((root / '.mrite' / 'project.json').read_text(encoding='utf-8-sig')).get('workspaceLayoutVersion') != 2):
        raise RuntimeError('此编译入口仅用于新版工作空间')
    if engine is None:
        try:
            language = json.loads((root / '.mrite' / 'state' / 'writing-language.json').read_text(encoding='utf-8-sig'))['language']
        except (OSError, ValueError, KeyError, TypeError):
            language = 'zh'
        engine = 'pdflatex' if language == 'en' else 'xelatex'
    def compile_with_fallback():
        try:
            inherited = previous_engine_fallback(root, source, engine)
            result = _build(source, root, engine, single_pass, fast, cache, code_theme, inherited)
            return remember_engine_fallback(root, source, result)
        except RuntimeError as original:
            fallback = language_engine_fallback(engine, str(original))
            if not fallback:
                raise
            alternate = alternate_engine(engine, fallback['to'])
            if not alternate:
                raise RuntimeError(str(original) + '\n未找到可用的 ' + fallback['to']) from original
            try:
                result = _build(source, root, alternate, single_pass, fast, cache, code_theme, fallback)
                return remember_engine_fallback(root, source, result)
            except Exception as retry:
                raise RuntimeError(str(original) + '\n自动兼容编译未成功：\n' + str(retry)) from retry
    if fast:
        return compile_with_fallback()
    attempt = {'status': 'running', 'texPath': str(source), 'startedAt': int(time.time() * 1000)}
    def save(**updates):
        if root is None:
            return
        record = root / '.mrite' / 'state' / 'paper-build-attempt.json'
        record.parent.mkdir(parents=True, exist_ok=True)
        temporary = record.with_name(record.name + '.' + uuid.uuid4().hex + '.tmp')
        temporary.write_text(json.dumps(dict(attempt, **updates), ensure_ascii=False), encoding='utf-8')
        os.replace(temporary, record)
    save()
    try:
        result = compile_with_fallback()
        save(status='success', finishedAt=int(time.time() * 1000), error='', engine=result['engine'], **({'engineFallback': result['engineFallback']} if result.get('engineFallback') else {}))
        return result
    except Exception as error:
        save(status='failed', finishedAt=int(time.time() * 1000), error=str(error)[-4000:])
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tex', default=str(Path(__file__).parent / '论文.tex'))
    parser.add_argument('--engine')
    parser.add_argument('--single-pass', action='store_true')
    parser.add_argument('--fast', action='store_true')
    parser.add_argument('--cache', action='store_true')
    parser.add_argument('--legacy-workspace')
    parser.add_argument('--code-theme', choices=('document', *CODE_THEMES), default='document')
    parser.add_argument('--check-language', metavar='PDF')
    parser.add_argument('--language', choices=('zh', 'en'), default='zh')
    args = parser.parse_args()
    try:
        result = check_language(args.check_language, args.language) if args.check_language else build(args.tex, args.engine, args.single_pass, args.fast, args.cache, args.legacy_workspace, args.code_theme)
        print(json.dumps(result, ensure_ascii=False))
    except Exception as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
