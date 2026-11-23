import sys
if __name__ == "__main__" and "--plot-rules" in sys.argv:
    sys.argv.remove("--plot-rules")
    def _run_rules():
        """Select Mrite plotting rules without loading the library into model context."""
        import argparse
        import gzip
        import hashlib
        import json
        import os
        from pathlib import Path, PurePosixPath
        import re
        import tempfile
        
        
        def safe_path(root, relative):
            parts = PurePosixPath(relative).parts
            if not parts or PurePosixPath(relative).is_absolute() or any(p in ('..', '.') or '\\' in p or ':' in p for p in parts):
                raise ValueError('Invalid rule path')
            cursor = root
            for part in parts:
                cursor = cursor / part
                if cursor.is_symlink():
                    raise ValueError('Rule paths cannot contain links')
            cursor.resolve().relative_to(root.resolve())
            return cursor
        
        
        def atomic_write(target, text):
            target.parent.mkdir(parents=True, exist_ok=True)
            fd, temporary = tempfile.mkstemp(dir=target.parent, suffix='.tmp')
            try:
                with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as stream:
                    stream.write(text)
                os.replace(temporary, target)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
        
        
        def split_values(values):
            return list(dict.fromkeys(x.strip() for value in (values or []) for x in value.split(',') if x.strip()))
        
        
        def rank(recipes, query, limit):
            query = query.strip().casefold()
            words = re.findall(r'[a-z0-9_]+|[\u4e00-\u9fff]+', query)
            ranked = []
            for row in recipes:
                text = ' '.join([row['id'], row['name'], row['description'], *row['keywords'], *row['chartTypes']]).casefold()
                score = 100 if query in (row['id'].casefold(), row['name'].casefold()) else 0
                for keyword in row['keywords'] + row['chartTypes']:
                    key = keyword.casefold()
                    if key and key in query:
                        score += 6 + min(len(key), 10)
                for word in words:
                    if word in text:
                        score += 5
                    elif len(word) > 2 and re.search(r'[\u4e00-\u9fff]', word):
                        score += sum(word[i:i + 2] in text for i in range(len(word) - 1))
                if score:
                    ranked.append((score, row))
            ranked.sort(key=lambda pair: (-pair[0], pair[1]['id']))
            return [{'id': row['id'], 'name': row['name'], 'chartTypes': row['chartTypes'],
                     'purpose': row['description'], 'score': score} for score, row in ranked[:limit]]
        
        
        def rule_body(text):
            text = text.replace('\r\n', '\n')
            return re.sub(r'^---\r?\n.*?\r?\n---\r?\n', '', text, count=1, flags=re.S).strip()
        
        
        def extract_rules(library, current, methods, include_common=True):
            sections = []
            if include_common and library.get('common'):
                sections.append('## 绘图通用要求\n\n' + rule_body(library['common']))
            for name in current['rules']:
                text = library['documents'][name]
                base = text.split('<!-- plot-methods -->', 1)[0]
                parts = [rule_body(base)]
                for identity in current.get('recipeIds', []):
                    row = methods[identity]
                    if row['file'] != name or not row.get('sectionId'):
                        continue
                    start = '<!-- plot-method:' + row['sectionId'] + ':start -->'
                    end = '<!-- plot-method:' + row['sectionId'] + ':end -->'
                    if start not in text or end not in text:
                        raise ValueError('Missing method section: ' + identity)
                    parts.append(rule_body(text.split(start, 1)[1].split(end, 1)[0]))
                sections.append('\n\n'.join(parts))
            return '\n\n---\n\n'.join(sections)
        
        
        def select(root, library, args):
            unified = library.get('unifiedStyle', False)
            aliases = library.get('styleAliases', {})
            style_arg = args.style
            color_arg = getattr(args, 'color', None)
            if unified:
                style_arg = color_arg or style_arg
                style_arg = aliases.get(style_arg, style_arg)
                color_arg = None
            recipes = {row['id']: row for row in library['catalog'].get('methods', library['catalog'].get('recipes', []))}
            recipe_ids = split_values(args.select)
            types = split_values(args.types)
            for identity in recipe_ids:
                if identity not in recipes:
                    raise ValueError('Unknown plot recipe: ' + identity)
            for identity in recipe_ids:
                types.extend(recipes[identity]['chartTypes'])
            types = list(dict.fromkeys(types))
            for kind in types:
                if kind not in library['catalog']['types']:
                    raise ValueError('Unknown chart type: ' + kind)
            files = []
            for kind in types:
                files.append(library['catalog']['types'][kind])
            for identity in recipe_ids:
                files.extend(recipes[identity]['familyRules'])
                files.append(recipes[identity]['file'])
            for value, group in [(style_arg, 'styles'), (color_arg, 'colors'), (args.output, 'outputs')]:
                if value:
                    if value not in library[group]:
                        raise ValueError('Unknown ' + group + ': ' + value)
                    files.append(library[group][value])
            files = list(dict.fromkeys(files))
            scope = args.target or args.question
            if not scope:
                raise ValueError('Provide --question or --target for a selection')
            if args.target:
                safe_path(root, args.target)
            state_file = safe_path(root, '.mrite/state/plot-rule-selection.json')
            try:
                state = json.loads(state_file.read_text(encoding='utf-8'))
            except (OSError, ValueError):
                state = {'version': 1, 'selections': {}}
            selections = state.setdefault('selections', {})
            previous = selections.get(scope, selections.get(args.question, {}))
            existing = args.target and safe_path(root, args.target).exists()
            current = dict(previous) if existing else {**library['configuration'], **previous}
            if unified:
                inherited = current.pop('chartColorScheme', None) or current.get('chartStyle')
                if inherited:
                    current['chartStyle'] = aliases.get(inherited, inherited)
            if args.target:
                relative = PurePosixPath(args.target).as_posix()
                record = safe_path(root, '.mrite/artifacts/' + hashlib.sha256(relative.encode('utf-8')).hexdigest() + '.json')
                try:
                    artifact = json.loads(record.read_text(encoding='utf-8'))
                except (OSError, ValueError):
                    artifact = {}
                prior_types = current.get('chartTypes')
                for name in ('chartTypes', 'imageGeneration') if unified else ('chartTypes', 'chartStyle', 'chartColorScheme', 'imageGeneration'):
                    if artifact.get(name):
                        current[name] = artifact[name]
                if unified:
                    inherited = artifact.get('chartColorScheme') or artifact.get('chartStyle')
                    if inherited:
                        current['chartStyle'] = aliases.get(inherited, inherited)
                if 'plotRecipes' in artifact:
                    current['recipeIds'] = artifact['plotRecipes']
                elif artifact.get('chartTypes') and artifact['chartTypes'] != prior_types:
                    current['recipeIds'] = []
            if args.select:
                current['recipeIds'] = recipe_ids
            elif args.types:
                current['recipeIds'] = []
            if args.types or args.select:
                current['chartTypes'] = types
            for name, value in [('chartStyle', style_arg), ('chartColorScheme', color_arg), ('imageGeneration', args.output)]:
                if value:
                    current[name] = value
            if getattr(args, 'purpose', None):
                current['purpose'] = args.purpose
            current['rules'] = files
            # Keep the last selected recipe/type when this turn only changes visual settings.
            if not args.select and not args.types:
                family_files = [library['catalog']['types'][kind] for kind in current.get('chartTypes', [])]
                method_files = [name for key in current.get('recipeIds', [])
                                for name in [*recipes[key]['familyRules'], recipes[key]['file']]]
                current['rules'] = list(dict.fromkeys(family_files + method_files + files))
            visual_fields = [('chartStyle', 'styles'), ('imageGeneration', 'outputs')]
            if not unified:
                visual_fields.append(('chartColorScheme', 'colors'))
            for field, group in visual_fields:
                value = current.get(field)
                if value and value in library[group]:
                    name = library[group][value]
                    if name not in current['rules']:
                        current['rules'].append(name)
            shared = None
            if library.get('shareCommonRules'):
                shared_files = [library[group][current[field]] for field, group in visual_fields
                                if current.get(field) in library[group]]
                shared_content = extract_rules(library, {**current, 'rules': shared_files, 'recipeIds': []}, recipes)
                shared = '.mrite/rules/selected-plots/shared-' + hashlib.sha256(shared_content.encode('utf-8')).hexdigest() + '.SKILL.md'
                atomic_write(safe_path(root, shared), '# 共享绘图规范（同一版本全题读一次）\n\n' + shared_content + '\n')
                content = extract_rules(library, {**current, 'rules': [name for name in current['rules'] if name not in shared_files]}, recipes, include_common=False)
            else:
                content = extract_rules(library, current, recipes)
            package = '.mrite/rules/selected-plots/' + hashlib.sha256(scope.encode('utf-8')).hexdigest() + '.SKILL.md'
            header = '# 本图已选绘图规则\n\n'
            header += '- 图：' + scope + '\n'
            header += '- 输出策略：' + current.get('purpose', '按求解计划中该图的结果与选图理由执行') + '\n'
            header += '- 图型：' + ', '.join(current.get('chartTypes', [])) + '\n'
            header += '- 画法：' + ', '.join(current.get('recipeIds', [])) + '\n'
            header += '- 预设风格：' + current.get('chartStyle', '沿用目标图当前风格') + '\n'
            if not unified:
                header += '- 预设色系：' + current.get('chartColorScheme', '沿用目标图当前颜色') + '\n'
            header += '- 图片类型：' + current.get('imageGeneration', '沿用目标图当前类型') + '\n\n'
            if shared:
                header += '共享绘图规范：' + shared + '。同一版本已读且仍在上下文中就不再读；切换风格、输出类型或压缩后缺失时补读。下方仅含本图图型与画法，不再读取源规则文件。\n\n'
            else:
                header += '以下已整合本图所需的通用要求、画法、绘图风格（颜色、纹理、点线与图元比例）和输出规范。编码只读取本文件；不再打开源图型文件中的其他画法。\n\n'
            atomic_write(safe_path(root, package), header + content + '\n')
            current['package'] = package
            selections[scope] = current
            atomic_write(state_file, json.dumps(state, ensure_ascii=False, indent=2))
            return {'scope': scope, **current, 'read': ([shared] if shared else []) + [package]}
        
        
        def main():
            parser = argparse.ArgumentParser(description=__doc__)
            parser.add_argument('--query')
            parser.add_argument('--limit', type=int, default=5, choices=range(1, 9))
            parser.add_argument('--select', action='append')
            parser.add_argument('--types', action='append')
            parser.add_argument('--question')
            parser.add_argument('--target', '--figure', dest='target')
            parser.add_argument('--purpose')
            parser.add_argument('--style', help='Select one complete plotting style, including texture and monochrome')
            parser.add_argument('--color', help=argparse.SUPPRESS)
            parser.add_argument('--output', choices=['editable', 'flat'])
            args = parser.parse_args()
            root = Path(__file__).resolve().parents[1]
            with gzip.open(root / '.mrite/rules/plot-library.json.gz', 'rt', encoding='utf-8') as stream:
                library = json.load(stream)
            if args.query:
                result = {'candidates': rank(library['catalog'].get('methods', library['catalog'].get('recipes', [])), args.query, args.limit),
                          'next': 'AI chooses a method for the planned result, then extracts one figure-specific rule package; no rule body has been loaded.'}
            else:
                result = select(root, library, args)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        
        
        if __name__ == '__main__':
            try:
                main()
            except (ValueError, KeyError, OSError) as error:
                raise SystemExit(str(error))
        
    _run_rules()
    raise SystemExit(0)

# 公共代码模板：求解/_common.py（系统自动播种，每个任务只写一次，不要覆写覆盖函数）
import sys, os
# 独立绘图/制表入口放在问题目录下的子目录，产物仍统一写回该问题。
_script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
if not _script_dir:
    _script_dir = os.getcwd()
BASE_DIR = _script_dir
_problem_candidate = _script_dir
for _ in range(8):
    _problem_parent = os.path.dirname(_problem_candidate)
    if (os.path.isfile(os.path.join(_problem_candidate, '产物清单.json')) or
            (os.path.basename(_problem_candidate).startswith('问题') and
             os.path.basename(_problem_parent) == '求解')):
        BASE_DIR = _problem_candidate
        break
    if _problem_parent == _problem_candidate:
        break
    _problem_candidate = _problem_parent

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as _fm
import warnings, logging
warnings.filterwarnings('ignore')
logging.getLogger('matplotlib').setLevel(logging.ERROR)  # 抑制findfont警告
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)  # 抑制字体管理器警告

# ★ 统一绘图类导入中枢：一次性提供常用 matplotlib 类/子模块，
#   使脚本只写 `from _common import *` 即可直接用，无需各自重复 import（防止遗漏导致 NameError）。
import matplotlib.ticker as mticker
import scipy.stats as stats
from matplotlib.patches import (Rectangle, FancyBboxPatch, FancyArrowPatch, FancyArrow,
                                Circle, RegularPolygon, Ellipse, Wedge, Polygon, Arrow, Arc)
from matplotlib.collections import PatchCollection, LineCollection, PolyCollection
from matplotlib.path import Path as _MplPath
from matplotlib.spines import Spine
try:
    from matplotlib.projections.polar import PolarAxes
    from matplotlib.projections import register_projection
    from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset
except Exception:
    pass

# 字体：仅首次运行时重建缓存（marker 防止每次都全量扫描字体拖慢）
def _find_font_dir():
    starts = [BASE_DIR, os.getcwd()]
    for start in starts:
        d = start
        for _ in range(6):
            # 运行脚本在 求解/问题X，字体随论文模板装配到工作区 论文/fonts；
            # 同时兼容开发目录/自定义模板把 fonts 放在当前层的情况。
            candidates = [
                os.path.join(d, 'fonts'),
                os.path.join(d, '论文', 'fonts'),
                os.path.join(d, 'rules-library', 'paper', 'system', 'fonts'),
            ]
            for candidate in candidates:
                if os.path.isdir(candidate) and os.path.isfile(os.path.join(candidate, 'SourceHanSerifCN-Regular.otf')):
                    return candidate
            parent = os.path.dirname(d)
            if parent == d: break
            d = parent
    return None
_SOLVE_DIR = os.path.dirname(os.path.abspath(__file__))
# 公共文件固定在求解根目录，定位不受 python -c 或脚本层级影响。
SOLVE_DIR = _SOLVE_DIR
_FONT_MARKER = os.path.join(_SOLVE_DIR, '_fonts_ready')
if not os.path.exists(_FONT_MARKER):
    try:
        import glob as _glb
        for _fc in _glb.glob(os.path.join(matplotlib.get_cachedir(), 'font*')):
            try: os.remove(_fc)
            except: pass
        _fm._load_fontmanager(try_read_cache=False)
        open(_FONT_MARKER, 'w').close()
    except Exception:
        pass
_FONT_DIR = _find_font_dir()
_ZH_FONT_PATH = None
if _FONT_DIR:
    for _f in ['SourceHanSerifCN-Regular.otf', 'SourceHanSerifCN-Bold.otf']:
        _p = os.path.join(_FONT_DIR, _f)
        if os.path.exists(_p): _fm.fontManager.addfont(_p)
    _candidate_zh = os.path.join(_FONT_DIR, 'SourceHanSerifCN-Regular.otf')
    if os.path.exists(_candidate_zh): _ZH_FONT_PATH = _candidate_zh
_SYS_FONT = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
for _f in ['times.ttf', 'timesbd.ttf', 'timesi.ttf', 'simsun.ttc']:
    _p = os.path.join(_SYS_FONT, _f)
    if os.path.exists(_p): _fm.fontManager.addfont(_p)
# 中文字体必须排在首位；Times New Roman 不含中文字形，放首位会让部分 legend
# 在独立字体解析路径里显示方框。英文/数字仍可在单独文本上显式指定 Times New Roman。
plt.rcParams['font.family'] = ['Source Han Serif CN', 'SimSun', 'Microsoft YaHei', 'Times New Roman', 'serif']
plt.rcParams['font.weight'] = 'normal'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 400
plt.rcParams['hatch.linewidth'] = 1.0
plt.rcParams['savefig.bbox'] = 'tight'
plt.rcParams['pdf.fonttype'] = 42
# 保留 SVG 中的真实文字节点，供 Mrite 图片编辑器直接改字与拖动图层。
plt.rcParams['svg.fonttype'] = 'none'
ZH_FONT = _fm.FontProperties(fname=_ZH_FONT_PATH) if _ZH_FONT_PATH else _fm.FontProperties(family=['SimSun', 'Microsoft YaHei'])

# ★ 兼容层：monkey-patch 旧 API，防止 agent 用 plt.cm.get_cmap() 报错
if not hasattr(matplotlib.cm, 'get_cmap'):
    matplotlib.cm.get_cmap = lambda name, n=None: plt.colormaps[name].resampled(n) if n else plt.colormaps[name]
try:
    from mpl_toolkits.mplot3d import Axes3D as _Axes3D
except ImportError:
    pass
def _scene_exporter():
    """Export a compact, browser-renderable scene for Matplotlib 3D figures.
    
    This module is bundled into the shared ``求解/_common.py`` for new tasks.  Task scripts keep calling
    ``save_fig`` / ``save_dual`` exactly as before; only the shared save helper
    uses this exporter when a real 3D axes is present.
    """
    
    import json
    import math
    import os
    
    import numpy as np
    from matplotlib import colors as _mcolors
    
    
    SCENE_VERSION = 1
    MAX_LINE_POINTS = 5000
    MAX_SCATTER_POINTS = 3500
    MAX_SEGMENTS = 2500
    MAX_FACES = 1800
    MAX_FACE_VERTICES = 80
    
    
    def _number(value, default=0.0):
        try:
            value = float(value)
            return value if math.isfinite(value) else float(default)
        except Exception:
            return float(default)
    
    
    def _triples(xs, ys=None, zs=None):
        if ys is None and zs is None:
            try:
                arr = np.asarray(xs, dtype=float)
                if arr.ndim != 2 or arr.shape[1] < 3:
                    return []
                arr = arr[:, :3]
            except Exception:
                return []
        else:
            try:
                arr = np.column_stack((np.asarray(xs, dtype=float),
                                       np.asarray(ys, dtype=float),
                                       np.asarray(zs, dtype=float)))
            except Exception:
                return []
        good = np.isfinite(arr).all(axis=1)
        arr = arr[good]
        return [[round(float(row[0]), 8), round(float(row[1]), 8), round(float(row[2]), 8)] for row in arr]
    
    
    def _sample(items, maximum):
        items = list(items or [])
        if len(items) <= maximum:
            return items
        indexes = np.linspace(0, len(items) - 1, maximum, dtype=int)
        return [items[int(index)] for index in indexes]
    
    
    def _rgba(value, fallback='#3b82f6'):
        try:
            r, g, b, a = _mcolors.to_rgba(value)
            return _mcolors.to_hex((r, g, b), keep_alpha=False), round(float(a), 4)
        except Exception:
            return fallback, 1.0
    
    
    def _first_color(values, fallback='#3b82f6'):
        try:
            if values is not None and len(values):
                return _rgba(values[0], fallback)
        except Exception:
            pass
        return fallback, 1.0
    
    
    def _safe_text(value):
        try:
            return str(value or '')[:300]
        except Exception:
            return ''
    
    
    def _extract_lines(ax):
        output = []
        for line in getattr(ax, 'lines', []):
            if not hasattr(line, 'get_data_3d') or not line.get_visible():
                continue
            try:
                xs, ys, zs = line.get_data_3d()
                points = _sample(_triples(xs, ys, zs), MAX_LINE_POINTS)
                if len(points) < 2:
                    continue
                color, opacity = _rgba(line.get_color())
                output.append({
                    'type': 'line', 'points': points, 'stroke': color,
                    'opacity': opacity * _number(line.get_alpha(), 1.0) if line.get_alpha() is not None else opacity,
                    'width': max(0.4, min(12.0, _number(line.get_linewidth(), 1.2))),
                })
            except Exception:
                continue
        return output
    
    
    def _extract_collections(ax):
        output = []
        for collection in getattr(ax, 'collections', []):
            if not collection.get_visible():
                continue
            alpha = collection.get_alpha()
            alpha = 1.0 if alpha is None else max(0.0, min(1.0, _number(alpha, 1.0)))
    
            # Path3DCollection (scatter) keeps its original coordinates here.
            offsets = getattr(collection, '_offsets3d', None)
            if offsets is not None:
                try:
                    raw = np.column_stack((np.asarray(offsets[0], dtype=float), np.asarray(offsets[1], dtype=float), np.asarray(offsets[2], dtype=float)))
                    indexes = np.flatnonzero(np.isfinite(raw).all(axis=1))
                    if len(indexes) > MAX_SCATTER_POINTS:
                        indexes = indexes[np.linspace(0, len(indexes) - 1, MAX_SCATTER_POINTS, dtype=int)]
                    points = [[round(float(v), 8) for v in raw[index]] for index in indexes]
                    if not points:
                        continue
                    facecolors = collection.get_facecolors()
                    color, opacity = _first_color(facecolors)
                    colors = []
                    if facecolors is not None and len(facecolors) > 1:
                        for index in indexes:
                            item_color, item_opacity = _rgba(facecolors[int(index) % len(facecolors)])
                            colors.append([item_color, round(item_opacity * alpha, 4)])
                    sizes = getattr(collection, '_sizes3d', collection.get_sizes())
                    size = math.sqrt(max(1.0, _number(np.median(sizes), 25.0))) if len(sizes) else 5.0
                    item = {
                        'type': 'points', 'points': points, 'color': color,
                        'opacity': round(opacity * alpha, 4),
                        'size': max(1.5, min(18.0, size * 0.55)),
                    }
                    if colors:
                        item['colors'] = colors
                    ids = getattr(collection, '_mrite_point_ids', None)
                    identity = getattr(collection, '_mrite_series_id', None)
                    if identity is None and collection.get_gid() is not None:
                        identity = 'gid:' + str(collection.get_gid())
                    label = collection.get_label()
                    if identity is None and label and not str(label).startswith('_'):
                        identity = 'label:' + str(label)
                    if ids is not None and len(ids) == len(raw) and identity is not None:
                        import hashlib
                        series = 'series:' + hashlib.sha256(str(identity).encode('utf-8')).hexdigest()[:24]
                        encoded = [json.dumps(ids[int(index)].item() if hasattr(ids[int(index)], 'item') else ids[int(index)], ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False) for index in indexes]
                        if len(set(encoded)) == len(encoded):
                            item['seriesId'] = series
                            item['pointIds'] = [series + ':point:' + hashlib.sha256(value.encode('utf-8')).hexdigest()[:24] for value in encoded]
                            item['pointSizes'] = [_number(sizes[int(index) % len(sizes)], 25.0) for index in indexes] if len(sizes) else []
                    output.append(item)
                except Exception:
                    pass
                continue
    
            # Line3DCollection, including wireframes and contour segments.
            segments = getattr(collection, '_segments3d', None)
            if segments is not None:
                try:
                    clean_segments = []
                    for segment in _sample(segments, MAX_SEGMENTS):
                        points = _sample(_triples(segment), MAX_FACE_VERTICES)
                        if len(points) >= 2:
                            clean_segments.append(points)
                    if clean_segments:
                        color, opacity = _first_color(collection.get_colors())
                        widths = collection.get_linewidths()
                        output.append({
                            'type': 'segments', 'segments': clean_segments,
                            'stroke': color, 'opacity': round(opacity * alpha, 4),
                            'width': max(0.35, min(10.0, _number(widths[0], 0.8) if len(widths) else 0.8)),
                        })
                except Exception:
                    pass
                continue
    
            # Poly3DCollection (surface, trisurf, bar3d) stores vertices in one
            # matrix plus slices.  This is private Matplotlib state, so extraction
            # is deliberately defensive and never affects PNG/SVG saving.
            vector = getattr(collection, '_vec', None)
            slices = getattr(collection, '_segslices', None)
            packed_faces = getattr(collection, '_faces', None)
            if (vector is None or slices is None) and packed_faces is None:
                continue
            try:
                facecolors = collection.get_facecolors()
                edgecolors = collection.get_edgecolors()
                edge, edge_opacity = _first_color(edgecolors, '#52525b')
                faces = []
                if packed_faces is not None:
                    packed_faces = np.asarray(packed_faces, dtype=float)
                    if packed_faces.ndim != 3 or packed_faces.shape[2] < 3:
                        continue
                    chosen_faces = _sample(list(enumerate(packed_faces)), MAX_FACES)
                else:
                    vector = np.asarray(vector, dtype=float)
                    if vector.ndim != 2 or vector.shape[0] < 3:
                        continue
                    chosen_faces = [(source_index, vector[:3, vertex_slice].T)
                                    for source_index, vertex_slice in _sample(list(enumerate(slices)), MAX_FACES)]
                for source_index, raw_face in chosen_faces:
                    points = _sample(_triples(raw_face), MAX_FACE_VERTICES)
                    if len(points) < 3:
                        continue
                    if facecolors is not None and len(facecolors):
                        fill, opacity = _rgba(facecolors[source_index % len(facecolors)])
                    else:
                        fill, opacity = '#60a5fa', 0.85
                    faces.append({
                        'points': points, 'fill': fill,
                        'opacity': round(opacity * alpha, 4),
                    })
                if faces:
                    widths = collection.get_linewidths()
                    output.append({
                        'type': 'polygons', 'faces': faces, 'edge': edge,
                        'edgeOpacity': round(edge_opacity * alpha, 4),
                        'width': max(0.0, min(5.0, _number(widths[0], 0.25) if len(widths) else 0.25)),
                    })
            except Exception:
                continue
        return output
    
    
    def _axis_scene(ax):
        limits = []
        for getter in (ax.get_xlim3d, ax.get_ylim3d, ax.get_zlim3d):
            low, high = getter()
            low, high = _number(low), _number(high, 1.0)
            if low == high:
                high = low + 1.0
            limits.append([low, high])
        position = getattr(ax, 'get_position', lambda: None)()
        bounds = list(position.bounds) if position is not None else [0.1, 0.1, 0.8, 0.8]
        return {
            'limits': limits,
            'position': [round(_number(value), 6) for value in bounds],
            'labels': {
                'x': _safe_text(ax.get_xlabel()),
                'y': _safe_text(ax.get_ylabel()),
                'z': _safe_text(ax.get_zlabel()),
                'title': _safe_text(ax.get_title()),
            },
            'primitives': _extract_lines(ax) + _extract_collections(ax),
        }
    
    
    def build_scene(fig):
        axes = [ax for ax in getattr(fig, 'axes', []) if getattr(ax, 'name', '') == '3d']
        if not axes:
            return None
        width = max(480, min(2400, int(round(_number(fig.get_figwidth(), 10.0) * 120))))
        height = max(360, min(1800, int(round(_number(fig.get_figheight(), 7.0) * 120))))
        first = axes[0]
        return {
            'version': SCENE_VERSION,
            'kind': 'matplotlib-3d',
            'canvas': {'width': width, 'height': height},
            'view': {
                'azimuth': round(_number(getattr(first, 'azim', -60.0), -60.0), 4),
                'elevation': round(_number(getattr(first, 'elev', 30.0), 30.0), 4),
                'roll': round(_number(getattr(first, 'roll', 0.0), 0.0), 4),
                'zoom': 1.0,
            },
            'axes': [_axis_scene(ax) for ax in axes],
        }
    
    
    def save_editable_3d(fig, target_path):
        """Write a sidecar scene when ``fig`` contains 3D axes; remove stale data otherwise."""
        scene = build_scene(fig)
        if scene is None:
            try:
                if os.path.isfile(target_path):
                    os.remove(target_path)
            except Exception:
                pass
            return False
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        temp_path = target_path + '.tmp'
        with open(temp_path, 'w', encoding='utf-8') as handle:
            json.dump(scene, handle, ensure_ascii=False, separators=(',', ':'))
        os.replace(temp_path, target_path)
        return True
    
    return save_editable_3d
_save_editable_3d = _scene_exporter()

FIG_DIR = os.path.join(BASE_DIR, '图片')
def _workspace_layout_v2():
    import json
    cursor = BASE_DIR
    for _ in range(12):
        try:
            with open(os.path.join(cursor, '.mrite', 'project.json'), encoding='utf-8') as marker:
                if json.load(marker).get('workspaceLayoutVersion') == 2:
                    return True
        except (OSError, ValueError, AttributeError):
            pass
        parent = os.path.dirname(cursor)
        if parent == cursor:
            break
        cursor = parent
    return False

_LAYOUT_V2 = _workspace_layout_v2()
try:
    import json as _json
    _PROJECT_ROOT = os.path.dirname(_SOLVE_DIR)
    with open(os.path.join(_PROJECT_ROOT, '.mrite', 'project.json'), encoding='utf-8') as _marker:
        _SOLVE_VERSION = int(_json.load(_marker).get('solveLayoutVersion', 0))
    _SIMPLE_SOLVE = _SOLVE_VERSION >= 3
except (OSError, ValueError, AttributeError):
    _SOLVE_VERSION = 0
    _SIMPLE_SOLVE = False
_COMPACT_SOLVE = _SOLVE_VERSION >= 4
if _COMPACT_SOLVE:
    FIG_DIR = os.path.join(BASE_DIR, '结果')
CACHE_DIR = os.path.join(BASE_DIR, '临时产物' if _COMPACT_SOLVE else '中间产物')
EDITABLE_FIG_DIR = os.path.join(BASE_DIR, '图稿') if _LAYOUT_V2 and not _SIMPLE_SOLVE else os.path.join(FIG_DIR, '.mrite-edit')
OUT_DIR = FIG_DIR if _COMPACT_SOLVE else os.path.join(BASE_DIR, '表格') if _LAYOUT_V2 else os.path.join(BASE_DIR, '结果')
if BASE_DIR not in (_PROJECT_ROOT, _SOLVE_DIR):
    os.makedirs(FIG_DIR, exist_ok=True)
    os.makedirs(EDITABLE_FIG_DIR, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)


if _SIMPLE_SOLVE and BASE_DIR not in (_PROJECT_ROOT, _SOLVE_DIR):
    for _folder in (['代码', '结果', '临时产物'] if _COMPACT_SOLVE else ['绘图代码', '图片', '表格', '中间产物', '临时数据']):
        os.makedirs(os.path.join(BASE_DIR, _folder), exist_ok=True)

def resolve_input(source_id, relative_path='', anchor=None):
    """Return a registered original file or directory without copying it."""
    import json
    from pathlib import Path
    if str(relative_path).startswith('source-') and not str(source_id).startswith('source-'):
        source_id, relative_path, anchor = relative_path, anchor or '', source_id
    project = Path(_PROJECT_ROOT)
    if anchor:
        start = Path(anchor).resolve()
        for candidate in (start, *start.parents):
            if (candidate / '.mrite/inputs.json').is_file():
                project = candidate
                break
    registry = json.loads((project / '.mrite/inputs.json').read_text(encoding='utf-8-sig'))
    local = json.loads((project / '.mrite/inputs.local.json').read_text(encoding='utf-8-sig'))
    source = next((row for row in registry.get('sources', []) if row.get('id') == source_id), None)
    binding = local.get('bindings', {}).get(source_id)
    if not source or not isinstance(binding, dict):
        raise FileNotFoundError('未定位输入来源：' + str(source_id))
    relative = Path(str(relative_path).replace(chr(92), '/'))
    if relative.is_absolute() or relative.drive or '..' in relative.parts:
        raise ValueError('输入成员必须是来源内相对路径')
    archive = source.get('kind') == 'archive'
    deferred = archive and (source.get('deferredArchive') or source.get('role') == 'data')
    value = binding.get('cachePath') if archive and not deferred else binding.get('realPath') or binding.get('path')
    if not isinstance(value, str) or not value:
        raise FileNotFoundError('未定位输入来源：' + str(source_id))
    base = Path(value)
    base = (base if base.is_absolute() else project / base).resolve()
    if source.get('kind') == 'file' or deferred:
        if str(relative_path) not in ('', source.get('name'), base.name):
            raise ValueError('文件或压缩包来源请直接读取原件')
        target = base
    else:
        target = (base / relative).resolve()
        if not target.is_relative_to(base):
            raise ValueError('输入成员越出来源目录')
    if not target.exists():
        raise FileNotFoundError(str(target))
    return target

_DATA_INPUTS = None

def register_data_inputs(*files):
    """Declare only the project cache files actually read by this figure."""
    from pathlib import Path
    global _DATA_INPUTS
    values = files[0] if len(files) == 1 and isinstance(files[0], (list, tuple, set)) else files
    root = Path(_PROJECT_ROOT).resolve()
    selected = []
    for value in values:
        file = Path(value).resolve()
        if not file.is_file() or root not in file.parents:
            raise ValueError('绘图数据依赖必须是项目内存在的缓存文件：' + str(value))
        selected.append(file)
    _DATA_INPUTS = list(dict.fromkeys(selected))

def record_checks(checks):
    """Persist actual boolean calculation checks; a failed check stops this calculation."""
    import json, hashlib, tempfile, os, sys
    from pathlib import Path
    root, script = Path(_PROJECT_ROOT).resolve(), Path(sys.argv[0]).resolve()
    if root not in script.parents or not isinstance(checks, dict) or not checks:
        raise ValueError('计算检查需要项目内的脚本和非空布尔条件字典')
    if any(type(value).__name__ not in ('bool', 'bool_') for value in checks.values()):
        raise ValueError('计算检查条件必须是实际计算得到的布尔值')
    parts = script.relative_to(root).parts
    if len(parts) < 3 or parts[0] != '求解' or not parts[1].startswith('问题'):
        raise ValueError('计算检查入口必须位于对应的求解/问题目录')
    question = parts[1]
    try: revision = json.loads((root / '.mrite/inputs.json').read_text(encoding='utf-8')).get('revision', '')
    except (OSError, ValueError): revision = ''
    record = {'version': 1, 'inputRevision': revision, 'sourceRevision': hashlib.sha256(script.read_bytes()).hexdigest(),
              'checks': {str(name): bool(value) for name, value in checks.items()}}
    directory = root / '.mrite/results'
    directory.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=str(directory), suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle: json.dump(record, handle, ensure_ascii=False)
        os.replace(temporary, directory / (question + '.json'))
    finally:
        if os.path.exists(temporary): os.unlink(temporary)
    failed = [name for name, passed in record['checks'].items() if not passed]
    if failed: raise ValueError('计算检查未通过：' + '、'.join(failed))
    return record

def _record_source(name, kind='image', chart_types=None, chart_style=None, chart_color_scheme=None, plot_recipe=None):
    if not _SIMPLE_SOLVE:
        return
    import json, hashlib, tempfile
    from pathlib import Path
    root = Path(_PROJECT_ROOT).resolve()
    script = Path(sys.argv[0]).resolve()
    output = Path(FIG_DIR if kind == 'image' else OUT_DIR) / (name + '.png' if kind == 'image' else name)
    output = output.resolve()
    outputs = [output]
    if kind == 'image':
        svg = Path(EDITABLE_FIG_DIR) / (name + '.svg')
        if svg.is_file(): outputs.append(svg.resolve())
    relative = output.relative_to(root).as_posix()
    record = {'version': 4, 'kind': kind, 'script': script.relative_to(root).as_posix(),
              'outputs': [p.relative_to(root).as_posix() for p in outputs],
              'cacheInputs': [p.resolve().relative_to(root).as_posix() for p in (_DATA_INPUTS if _DATA_INPUTS is not None else Path(CACHE_DIR).rglob('*')) if p.is_file() and not p.is_symlink()]}
    record['dependencyMode'] = 'explicit' if _DATA_INPUTS is not None else 'legacy-directory'
    record['sourceRevision'] = hashlib.sha256(script.read_bytes()).hexdigest()
    record['questionId'] = script.relative_to(root).parts[1] if script.relative_to(root).parts[0] == '求解' else ''
    try: record['inputRevision'] = json.loads((root / '.mrite/inputs.json').read_text(encoding='utf-8')).get('revision', '')
    except (OSError, ValueError): record['inputRevision'] = ''
    record['cacheRevisions'] = {name: {'size': (root / name).stat().st_size, 'mtimeNs': str((root / name).stat().st_mtime_ns)} for name in record['cacheInputs']}
    directory = root / '.mrite' / 'artifacts'
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / (hashlib.sha256(relative.encode('utf-8')).hexdigest() + '.json')
    # Tags describe this figure, not the project's default configuration.
    try:
        previous = json.loads(target.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        previous = {}
    if kind == 'image':
        if chart_types is None:
            chart_types = previous.get('chartTypes', [])
        if isinstance(chart_types, str):
            chart_types = [chart_types]
        record['imageGeneration'] = 'editable'
        record['chartTypes'] = list(dict.fromkeys(str(value).strip() for value in chart_types if str(value).strip()))
        recipe_ids = previous.get('plotRecipes', []) if plot_recipe is None else plot_recipe
        if plot_recipe is None and record['chartTypes'] != previous.get('chartTypes', []):
            recipe_ids = []
        if isinstance(recipe_ids, str):
            recipe_ids = [recipe_ids]
        record['plotRecipes'] = list(dict.fromkeys(str(value).strip() for value in recipe_ids if str(value).strip()))
        selected_style = chart_color_scheme if chart_color_scheme is not None else chart_style
        if selected_style is None:
            selected_style = previous.get('chartColorScheme') or previous.get('chartStyle', '')
        if not selected_style:
            try:
                configuration = json.loads((root / '.mrite/state/solve-configuration.json').read_text(encoding='utf-8'))
                selected_style = configuration.get('plotStyle') or configuration.get('colorScheme', '')
            except (OSError, ValueError):
                selected_style = ''
        try:
            aliases = json.loads((root / '.mrite/state/plot-style-aliases.json').read_text(encoding='utf-8'))
        except (OSError, ValueError):
            aliases = {}
        record['chartStyle'] = aliases.get(str(selected_style).strip(), str(selected_style).strip())
    fd, temporary = tempfile.mkstemp(dir=str(directory), suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream: json.dump(record, stream, ensure_ascii=False)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)

# ★ 数据目录：脚本在 求解/问题X/ 下，数据在工作区根的 数据/ 下，需要往上两级
DATA_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', '..', '数据'))

def despine(ax):
    """只保留左侧和底侧边框，移除上侧和右侧"""
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

def register_point_ids(collection, point_ids, series_id=None):
    """给散点登记业务身份。ID 必须唯一；重排/增删数据后编辑仍按 ID 对应。"""
    import json
    values = list(point_ids)
    if len(values) != len(collection.get_offsets()):
        raise ValueError('point_ids 数量必须与散点数据行数一致')
    encoded = [json.dumps(value.item() if hasattr(value, 'item') else value,
                          ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
               for value in values]
    if len(set(encoded)) != len(encoded):
        raise ValueError('point_ids 必须唯一，不能用重复身份保存逐点编辑')
    collection._mrite_point_ids = values
    if series_id is not None:
        collection._mrite_series_id = str(series_id)
    return collection

def scatter_editable(ax, x, y, point_ids=None, series_id=None, **kwargs):
    """普通 ax.scatter 的可编辑版本；建议 point_ids 使用源数据主键。"""
    collection = ax.scatter(x, y, **kwargs)
    if series_id is not None:
        collection._mrite_series_id = str(series_id)
    if point_ids is not None:
        register_point_ids(collection, point_ids, series_id)
    return collection

def _save_editable_svg(fig, target):
    """保存真实文字和矢量对象；原生像素图仍为图片，不能伪装成可拆分数据。"""
    import html, json, re, tempfile, hashlib, uuid
    import xml.etree.ElementTree as ET
    from matplotlib.text import Text

    artists = fig.findobj()
    reserved = {str(item.get_gid()) for item in artists if item.get_gid() is not None}
    changes, elements, seen, point_collections = [], [], set(), []
    generation_id = uuid.uuid4().hex
    stable_keys = set()
    stable_sources = {}

    def tag(item, key, role, kind, axes=None):
        if id(item) in seen:
            return
        seen.add(id(item))
        original = item.get_gid()
        if original is None:
            candidate, suffix = key, 1
            while candidate in reserved:
                suffix += 1
                candidate = key + '_' + str(suffix)
            item.set_gid(candidate)
            changes.append((item, original))
            reserved.add(candidate)
        label = item.get_text() if isinstance(item, Text) else item.get_label()
        label = str(label or '')
        element = {'id': str(item.get_gid()), 'role': role, 'kind': kind,
                   'label': label if label and not label.startswith('_') else kind}
        if axes:
            element['axes'] = axes
        explicit = getattr(item, '_mrite_series_id', None)
        identity_source = 'explicit'
        if explicit is None and original is not None:
            explicit = 'gid:' + str(original)
        if explicit is None and role == 'series' and label and not label.startswith('_'):
            explicit = 'label:' + label
            identity_source = 'label'
        if explicit is not None and role == 'series':
            semantic = 'series:' + hashlib.sha256(str(explicit).encode('utf-8')).hexdigest()[:24]
            if semantic in stable_keys:
                if identity_source != 'label' or stable_sources.get(semantic) != 'label':
                    raise ValueError('可编辑图的 series_id/gid 必须唯一：' + str(explicit))
                # 多子图常有重复图例名。名称有歧义就降级为本代身份，不能妨碍正常出图。
                for previous in elements:
                    if previous.get('semanticId') == semantic:
                        previous.update(semanticId='generation:' + generation_id + ':' + previous['id'], stable=False)
                element.update(semanticId='generation:' + generation_id + ':' + element['id'], stable=False)
            else:
                stable_keys.add(semantic)
                stable_sources[semantic] = identity_source
                element.update(semanticId=semantic, stable=True)
        else:
            element.update(semanticId='generation:' + generation_id + ':' + str(item.get_gid()), stable=False)
        if role == 'series' and kind == 'scatter':
            point_collections.append((item, element))
        elements.append(element)

    rasterized, raster_zorders = [], []
    temporary = None
    try:
        tag(fig.patch, 'patch_mrite_background', 'background', 'canvas')
        for number, ax in enumerate(fig.axes, 1):
            tag(ax, 'axes_' + str(number), 'axes', 'subplot')
            axes_id = str(ax.get_gid())
            tag(ax.patch, 'patch_mrite_a%d_background' % number, 'background', 'plot', axes_id)
            for index, line in enumerate(ax.lines, 1):
                tag(line, 'line2d_mrite_a%d_%d' % (number, index), 'series', 'line', axes_id)
            for index, collection in enumerate(ax.collections, 1):
                name = type(collection).__name__
                kind = {'PathCollection': 'scatter', 'Path3DCollection': 'scatter', 'QuadMesh': 'mesh',
                        'LineCollection': 'segments', 'PolyCollection': 'area'}.get(name, 'collection')
                tag(collection, '%s_mrite_a%d_%d' % (name, number, index), 'series', kind, axes_id)
            bar_patches = {id(patch) for container in ax.containers
                           for patch in getattr(container, 'patches', [])}
            for index, patch in enumerate(ax.patches, 1):
                tag(patch, 'patch_mrite_a%d_%d' % (number, index), 'series',
                    'bar' if id(patch) in bar_patches else 'shape', axes_id)
            for index, image in enumerate(ax.images, 1):
                tag(image, 'image_mrite_a%d_%d' % (number, index), 'series', 'image', axes_id)
            legend = ax.get_legend()
            if legend is not None:
                tag(legend, 'legend_mrite_a%d' % number, 'legend', 'legend', axes_id)
            for index, text in enumerate(ax.findobj(match=Text), 1):
                tag(text, 'text_mrite_a%d_%d' % (number, index), 'text', 'text', axes_id)
            old_zorder = ax.get_rasterization_zorder()
            if old_zorder is not None:
                raster_zorders.append((ax, old_zorder))
                ax.set_rasterization_zorder(None)
        for index, legend in enumerate(fig.legends, 1):
            tag(legend, 'legend_mrite_fig_%d' % index, 'legend', 'legend')
        for index, text in enumerate(fig.findobj(match=Text), 1):
            tag(text, 'text_mrite_fig_%d' % index, 'text', 'text')
        # rasterized=True 的曲线、散点、网格仍有完整数据，SVG 应保留它们的矢量结构。
        # imshow/照片本来就是像素，关闭该开关也不会将其变成可拆分矢量。
        for item in fig.findobj():
            if item.get_rasterized():
                rasterized.append(item)
                item.set_rasterized(False)
        # 不受绘图脚本之后重新设置全局 rcParams 的影响，也不泄漏本次设置。
        # 临时文件不使用 .svg 后缀，避免图片监听器把尚未完成的源图当成正式文件。
        descriptor, temporary = tempfile.mkstemp(prefix='.mrite-svg-', suffix='.tmp',
                                                 dir=os.path.dirname(os.path.abspath(target)))
        os.close(descriptor)
        with matplotlib.rc_context({'svg.fonttype': 'none', 'svg.image_inline': True}):
            fig.savefig(temporary, format='svg', bbox_inches='tight', facecolor='white')
        with open(temporary, 'r', encoding='utf-8') as source:
            svg = source.read()
        ns = 'http://www.w3.org/2000/svg'
        ET.register_namespace('', ns)
        ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
        root = ET.fromstring(svg)
        by_id = {node.get('id'): node for node in root.iter() if node.get('id')}
        def annotate(node, element):
            for key in ('role', 'kind', 'label', 'axes'):
                if key in element:
                    node.set('data-mrite-' + key, str(element[key]))
            node.set('data-mrite-semantic-id', element['semanticId'])
            element['baseTransform'] = node.get('transform', '')
            element['baseStyle'] = node.get('style', '')
        for element in elements:
            node = by_id.get(element['id'])
            if node is not None:
                annotate(node, element)
        for collection, series in point_collections:
            group = by_id.get(series['id'])
            if group is None:
                continue
            leaves = []
            def visit(parent):
                for node in parent:
                    name = node.tag.rsplit('}', 1)[-1]
                    if name in ('defs', 'clipPath', 'mask', 'pattern'):
                        continue
                    if name in ('use', 'path', 'circle', 'ellipse'):
                        leaves.append(node)
                    else:
                        visit(node)
            visit(group)
            offsets = np.ma.asarray(collection.get_offsets())
            mask = np.ma.getmaskarray(offsets)
            valid = [i for i in range(len(offsets)) if not np.any(mask[i]) and
                     np.all(np.isfinite(np.asarray(offsets[i], dtype=float)))]
            order = getattr(collection, '_z_markers_idx', None)
            if order is not None and hasattr(collection, '_offsets3d'):
                try:
                    order = list(np.asarray(order, dtype=int))
                    if len(order) == len(valid) and set(order) == set(range(len(valid))):
                        valid = [valid[i] for i in order]
                except (TypeError, ValueError):
                    pass
            ids = getattr(collection, '_mrite_point_ids', None)
            sizes = getattr(collection, '_sizes3d', collection.get_sizes())
            # 只有一对一对应的真实可见点才建立业务身份，不猜测后端被过滤点的序号。
            safe = len(leaves) == len(valid)
            for index, node in enumerate(leaves):
                row = valid[index] if safe else None
                key = ids[row] if ids is not None and row is not None and row < len(ids) else None
                stable = bool(safe and ids is not None and series['stable'])
                encoded = json.dumps(key.item() if hasattr(key, 'item') else key,
                                     ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
                identity = (series['semanticId'] + ':point:' + hashlib.sha256(encoded.encode('utf-8')).hexdigest()[:24]
                            if stable else 'generation:' + generation_id + ':point:' + series['id'] + ':' + str(index))
                node_id = 'mrite_point_' + hashlib.sha256(identity.encode('utf-8')).hexdigest()[:24]
                node.set('id', node_id)
                node.set('data-mrite-point-id', identity)
                node.set('data-mrite-series-id', series['semanticId'])
                point = {'id': node_id, 'semanticId': identity, 'stable': stable,
                         'role': 'point', 'kind': 'scatter-point', 'label': str(key) if stable else '散点',
                         'axes': series.get('axes'), 'seriesId': series['semanticId']}
                if row is not None:
                    point['point'] = {'key': key.item() if hasattr(key, 'item') else key,
                                      'x': float(offsets[row, 0]), 'y': float(offsets[row, 1]),
                                      'size': float(sizes[row % len(sizes)]) if len(sizes) else 1.0}
                annotate(node, point)
                elements.append(point)
        # 保存点的原始几何中心，重绘后大小/旋转继续围绕新位置，避免以旧中心拉偏数据点。
        parents = {child: parent for parent in root.iter() for child in parent}
        all_nodes = {node.get('id'): node for node in root.iter() if node.get('id')}
        def transform_matrix(value):
            result = np.eye(3)
            for operation, body in re.findall(r'([A-Za-z]+)\s*\(([^)]*)\)', value or ''):
                values = [float(v) for v in re.findall(r'[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?', body)]
                matrix = np.eye(3)
                if operation == 'matrix' and len(values) == 6:
                    a,b,c,d,e,f = values
                    matrix = np.array([[a,c,e],[b,d,f],[0,0,1]])
                elif operation == 'translate' and values:
                    matrix[:2,2] = [values[0], values[1] if len(values)>1 else 0]
                elif operation == 'scale' and values:
                    matrix[0,0],matrix[1,1] = values[0],values[1] if len(values)>1 else values[0]
                elif operation == 'rotate' and values:
                    angle = np.deg2rad(values[0]);cs,sn = np.cos(angle),np.sin(angle)
                    matrix[:2,:2] = [[cs,-sn],[sn,cs]]
                    if len(values) == 3:
                        center = np.asarray(values[1:3]);matrix[:2,2] = center - matrix[:2,:2] @ center
                result = result @ matrix
            return result
        def path_bounds(node):
            if node.tag.rsplit('}',1)[-1] == 'use':
                target_id = node.get('{http://www.w3.org/1999/xlink}href',node.get('href',''))
                target = all_nodes.get(target_id.lstrip('#'))
                bounds = path_bounds(target) if target is not None else None
                if bounds is not None:
                    bounds = bounds + np.asarray([float(node.get('x',0)),float(node.get('y',0)),float(node.get('x',0)),float(node.get('y',0))])
                return bounds
            if node.tag.rsplit('}',1)[-1] != 'path':
                return None
            tokens = re.findall(r'[A-Za-z]|[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?',node.get('d',''))
            vertices,codes,command,position = [],[],None,0
            while position < len(tokens):
                if tokens[position].isalpha():
                    command=tokens[position];position+=1
                if command in ('z','Z'):
                    vertices.append(vertices[0]);codes.append(_MplPath.CLOSEPOLY);command=None;continue
                counts = {'M':2,'L':2,'C':6,'Q':4}
                if command not in counts:
                    return None
                count=counts[command]
                values=list(map(float,tokens[position:position+count]));position+=count
                for i in range(0,count,2):
                    vertices.append(values[i:i+2]);codes.append({'M':_MplPath.MOVETO,'L':_MplPath.LINETO,'C':_MplPath.CURVE4,'Q':_MplPath.CURVE3}[command])
                if command=='M':command='L'
            if not vertices:return None
            extents=_MplPath(vertices,codes).get_extents()
            return np.asarray([extents.x0,extents.y0,extents.x1,extents.y1])
        for element in elements:
            if element.get('role') != 'point':continue
            node=all_nodes.get(element['id'])
            if node is None:continue
            bounds=path_bounds(node)
            chain=[];cursor=node
            while cursor is not root and cursor is not None:
                chain.insert(0,cursor);cursor=parents.get(cursor)
            matrix=np.eye(3)
            for ancestor in chain:matrix=matrix @ transform_matrix(ancestor.get('transform',''))
            element['baseRootMatrix']=[float(matrix[0,0]),float(matrix[1,0]),float(matrix[0,1]),float(matrix[1,1]),float(matrix[0,2]),float(matrix[1,2])]
            if bounds is not None:
                corners=np.asarray([[bounds[0],bounds[1],1],[bounds[2],bounds[1],1],[bounds[0],bounds[3],1],[bounds[2],bounds[3],1]]) @ matrix.T
                left,top=corners[:,:2].min(axis=0);right,bottom=corners[:,:2].max(axis=0)
                element['baseBounds']={'x':float(left),'y':float(top),'width':float(right-left),'height':float(bottom-top)}
        present_ids = {node.get('id') for node in root.iter() if node.get('id')}
        elements = [element for element in elements if element['id'] in present_ids]
        document = {'format': 'mrite-editable-svg', 'version': 2, 'generationId': generation_id,
                    'source': 'matplotlib', 'elements': elements, 'edits': {}}
        metadata = ET.Element('{%s}metadata' % ns, {'id': 'mrite-editable-document'})
        metadata.text = json.dumps(document, ensure_ascii=False, separators=(',', ':'))
        root.insert(0, metadata)
        root.set('data-mrite-document-version', '2')
        svg = ET.tostring(root, encoding='unicode')
        with open(temporary, 'w', encoding='utf-8') as output:
            output.write(svg)
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except OSError:
                pass
        for item in rasterized:
            item.set_rasterized(True)
        for ax, old_zorder in raster_zorders:
            ax.set_rasterization_zorder(old_zorder)
        for item, original in reversed(changes):
            item.set_gid(original)

def save_fig(fig, name_cn, dpi=400, *, chart_types=None, chart_style=None, chart_color_scheme=None, plot_recipe=None):
    """保存论文用 PNG、可编辑 SVG，并为三维图自动保留视角数据。"""
    os.makedirs(FIG_DIR, exist_ok=True)
    os.makedirs(EDITABLE_FIG_DIR, exist_ok=True)
    path = os.path.join(FIG_DIR, name_cn + '.png')
    fig.savefig(path, dpi=dpi, bbox_inches='tight', facecolor='white')
    _save_editable_svg(fig, os.path.join(EDITABLE_FIG_DIR, name_cn + '.svg'))
    if _save_editable_3d:
        try: _save_editable_3d(fig, os.path.join(EDITABLE_FIG_DIR, name_cn + '.3d.json'))
        except Exception: pass
    _record_source(name_cn, chart_types=chart_types, chart_style=chart_style, chart_color_scheme=chart_color_scheme, plot_recipe=plot_recipe)
    plt.close(fig)
    print(f'  已保存: {name_cn}.png（含可编辑图层）')

def save_dual(fig, name_cn, dpi=400, bw=False, *, chart_types=None, chart_style=None, chart_color_scheme=None, plot_recipe=None):
    """保存图片（默认 400dpi 高清）。绘图规则只输出全彩，默认不再生成黑白版（bw=False，仅保存彩色）。
    如需临时验证黑白效果可手动传 bw=True，但最终产出图一律不得黑白。"""
    os.makedirs(FIG_DIR, exist_ok=True)
    os.makedirs(EDITABLE_FIG_DIR, exist_ok=True)
    from PIL import Image, ImageOps
    color_path = os.path.join(FIG_DIR, name_cn + '.png')
    fig.savefig(color_path, dpi=dpi, bbox_inches='tight', facecolor='white')
    _save_editable_svg(fig, os.path.join(EDITABLE_FIG_DIR, name_cn + '.svg'))
    if _save_editable_3d:
        try: _save_editable_3d(fig, os.path.join(EDITABLE_FIG_DIR, name_cn + '.3d.json'))
        except Exception: pass
    print(f'  已保存: {name_cn}.png（含可编辑图层）')
    if bw:
        bw_path = os.path.join(FIG_DIR, name_cn + '_bw.png')
        try:
            img = Image.open(color_path)
            img_gray = ImageOps.grayscale(img)
            img_gray.save(bw_path)
            img.close()
        except Exception:
            fig.savefig(bw_path, dpi=dpi, bbox_inches='tight', facecolor='white')
        print(f'  已保存: {name_cn}_bw.png')
        print(f'  ★ 双版本完成: {name_cn}')
    _record_source(name_cn, chart_types=chart_types, chart_style=chart_style, chart_color_scheme=chart_color_scheme, plot_recipe=plot_recipe)
    plt.close(fig)

def save_csv(df, name_cn):
    os.makedirs(OUT_DIR, exist_ok=True)
    df.to_csv(OUT_DIR + '/' + name_cn, index=False, encoding='utf-8-sig')
    _record_source(name_cn, 'table')

def top_legend(fig, axes=None, fontsize=9, **kwargs):
    """顶部单行图例；图例较宽时自动扩宽画布，让下方子图随画布均匀分散。"""
    if axes is None:
        axes = fig.axes
    elif not isinstance(axes, (list, tuple, np.ndarray)):
        axes = [axes]
    handles, labels, seen = [], [], set()
    for ax in np.asarray(axes, dtype=object).ravel():
        hs, ls = ax.get_legend_handles_labels()
        for h, label in zip(hs, ls):
            if label and label not in seen and not str(label).startswith('_'):
                handles.append(h); labels.append(label); seen.add(label)
        old = ax.get_legend()
        if old is not None: old.remove()
    handles = kwargs.pop("handles", handles)
    labels = kwargs.pop("labels", labels)
    if not handles:
        return None
    subplot_top = kwargs.pop('subplot_top', None)
    auto_expand = kwargs.pop('auto_expand', True)
    legend_pad_inches = kwargs.pop('legend_pad_inches', 0.60)
    subplot_gap_inches = kwargs.pop('subplot_gap_inches', 0.18)
    wspace = kwargs.pop('wspace', 0.24)
    legend_prop = ZH_FONT.copy()
    legend_prop.set_size(fontsize)
    options = dict(loc='upper center', bbox_to_anchor=(0.5, 0.995),
                   ncol=len(labels), frameon=False, prop=legend_prop)
    options.update(kwargs)
    legend = fig.legend(handles=handles, labels=labels, **options)

    # 先测量单行图例的真实尺寸。若它比当前画布可用宽度更宽，就扩大整张图；
    # axes 使用归一化坐标，会随画布一起横向展开，因此下方多个子图也会自然分散。
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    legend_box = legend.get_window_extent(renderer=renderer)
    legend_width = legend_box.width / fig.dpi
    legend_height = legend_box.height / fig.dpi
    fig_width, fig_height = fig.get_size_inches()
    if auto_expand:
        target_width = max(fig_width, legend_width + legend_pad_inches)
        if target_width > fig_width + 0.05:
            fig.set_size_inches(target_width, fig_height, forward=True)
            fig.canvas.draw()

    # 图例少时不额外拉宽；顶部只留一行图例实际所需高度，避免大块空白。
    if subplot_top is None:
        subplot_top = min(0.91, 1.0 - (legend_height + subplot_gap_inches) / fig_height)
        subplot_top = max(0.72, subplot_top)
    fig.subplots_adjust(top=subplot_top, wspace=wspace)
    return legend

def label_subplots_below(fig, axes, labels, fontsize=10, gap=0.012, **kwargs):
    """把 a/b/c + 名称紧贴各子图下方，并避开刻度与轴标签。应在 top_legend 之后调用。"""
    if not isinstance(axes, (list, tuple, np.ndarray)):
        axes = [axes]
    axes = list(np.asarray(axes, dtype=object).ravel())
    labels = list(labels)
    if len(labels) != len(axes):
        raise ValueError(f'子图标签数({len(labels)})必须等于子图数({len(axes)})')
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    artists = []
    for ax, label in zip(axes, labels):
        # y 取包含刻度/轴标签在内的 tight bbox 下边界；x 对齐数据区中心。
        tight = ax.get_tightbbox(renderer).transformed(fig.transFigure.inverted())
        pos = ax.get_position()
        artists.append(fig.text((pos.x0 + pos.x1) / 2.0, tight.y0 - gap, str(label),
                                ha='center', va='top', fontsize=fontsize,
                                fontweight='bold', fontproperties=ZH_FONT, **kwargs))
    return artists

def shared_path(name):
    """跨问题共享中间文件的统一路径（存到 求解/ 根，供各问题脚本互相读取）。
    例：问题一存 shared_path('预处理数据.csv')，问题二用 pd.read_csv(shared_path('预处理数据.csv')) 读取。"""
    return os.path.join(SOLVE_DIR, name)

def is_ax_empty(ax):
    """检测坐标轴是否无数据（空图）"""
    return (len(ax.lines) == 0 and len(ax.collections) == 0
            and len(ax.patches) == 0 and len(ax.images) == 0)

def is_flat_line(x, y):
    """折线是否为直线（完全无变化→不画）：所有y相同或所有x相同"""
    if x is None or y is None or len(x) < 2 or len(y) < 2:
        return False
    y_arr = np.asarray(y, dtype=float)
    x_arr = np.asarray(x, dtype=float)
    y_flat = np.allclose(y_arr, y_arr[0])
    x_flat = np.allclose(x_arr, x_arr[0])
    return y_flat or x_flat

def validate_subplots(nrows, ncols, chart_types=None):
    """兼容旧绘图接口，仅检查行列为正整数。"""
    if any(not isinstance(v, (int, np.integer)) or v <= 0 for v in (nrows, ncols)):
        return '子图行列必须为正整数'
    return None


def get_color_scheme(scheme=None, n=None):
    """Return the shared preset colors; pass a figure's explicit scheme on redraw."""
    import json
    from pathlib import Path
    root = Path(_PROJECT_ROOT)
    if scheme is None:
        with open(root / '.mrite/state/solve-configuration.json', encoding='utf-8') as stream:
            configuration = json.load(stream)
            scheme = configuration.get('plotStyle') or configuration.get('colorScheme', 'modelviz')
    with open(root / '.mrite/state/chart-color-schemes.json', encoding='utf-8') as stream:
        catalog = json.load(stream)
    colors = catalog[scheme]
    if n is None:
        return list(colors)
    if isinstance(n, bool) or int(n) != n or n < 0:
        raise ValueError('color count must be a nonnegative integer')
    return [colors[i % len(colors)] for i in range(int(n))]


def get_plot_style(scheme=None):
    """Return the selected complete visual profile, with a legacy-workspace fallback."""
    import json
    from pathlib import Path
    root = Path(_PROJECT_ROOT)
    if scheme is None:
        with open(root / '.mrite/state/solve-configuration.json', encoding='utf-8') as stream:
            configuration = json.load(stream)
            scheme = configuration.get('plotStyle') or configuration.get('colorScheme', 'modelviz')
    try:
        with open(root / '.mrite/state/chart-style-profiles.json', encoding='utf-8') as stream:
            return json.load(stream)[scheme]
    except (FileNotFoundError, KeyError):
        colors = get_color_scheme(scheme)
        return {'key': scheme, 'colors': colors, 'fillColors': list(colors), 'stackColors': list(colors),
                'encoding': 'color', 'hatches': [''] * len(colors),
                'markers': ['o', 's', '^', 'D', 'v', 'P'],
                'lineStyles': ['-', '--', '-.', ':', '--', '-.'],
                'lineWidth': 1.5, 'edgeWidth': .65, 'barWidth': .36,
                'openMarkers': False, 'grid': True, 'hatchWidth': 1.0}


def get_bar_facecolors(colors, profile=None, scheme=None, elevation=27, azimuth=-55):
    """Apply directional diffuse/specular lighting in bar3d's documented six-face order."""
    import numpy as np
    from matplotlib.colors import to_rgba_array
    if profile is None:
        profile = get_plot_style(scheme)
    light = profile.get('lighting', {})
    normals = np.array([[0, 0, -1], [0, 0, 1], [0, -1, 0], [0, 1, 0], [-1, 0, 0], [1, 0, 0]], dtype=float)
    key = np.asarray(light.get('keyDirection', [-.15, .30, .94]), dtype=float)
    fill = np.asarray(light.get('fillDirection', [1, -.65, .45]), dtype=float)
    key = key / np.linalg.norm(key)
    fill = fill / np.linalg.norm(fill)
    elevation, azimuth = np.radians([elevation, azimuth])
    view = np.array([np.cos(elevation)*np.cos(azimuth), np.cos(elevation)*np.sin(azimuth), np.sin(elevation)])
    half = key + view
    half = half / np.linalg.norm(half)
    intensity = light.get('ambient', .80) + light.get('keyDiffuse', .20)*np.maximum(normals @ key, 0) + light.get('fillDiffuse', .16)*np.maximum(normals @ fill, 0)
    highlight = light.get('specular', .35)*np.maximum(normals @ half, 0)**light.get('shininess', 12)
    rgba = to_rgba_array(colors)
    rgb = np.clip(rgba[:, None, :3]*intensity[None, :, None], 0, 1)
    rgb = rgb + highlight[None, :, None]*(1-rgb)
    alpha = np.broadcast_to(rgba[:, None, 3:], (len(rgba), 6, 1))
    return np.concatenate([np.clip(rgb, 0, 1), alpha], axis=2).reshape(-1, 4)


def style_3d_axes(ax, elev=30, azim=-55, ortho=False):
    """Use the same thin gray-blue frame and secondary grid as the comparison gallery."""
    ax.view_init(elev, azim)
    if ortho:
        ax.set_proj_type('ortho')
    ax.set_box_aspect((1, 1, .8))
    ax.tick_params(labelsize=8, pad=0)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.fill = False
        axis.pane.set_edgecolor('#B6BEC7')
        axis.pane.set_linewidth(.45)
        axis.line.set_color('#425466')
        axis.line.set_linewidth(.6)
        axis._axinfo['grid'].update(color=(.65, .69, .73, .6), linewidth=.4)
    return ax


def draw_mesh_surface(ax, x, y, z, cmap, norm=None, profile=None, mesh_count=13):
    """Draw a regular numerical field as a smooth color surface plus a sparse structural mesh."""
    import numpy as np
    from matplotlib.colors import Normalize, LightSource
    x, y, z = (np.asarray(value) for value in (x, y, z))
    if x.ndim == y.ndim == 1:
        x, y = np.meshgrid(x, y)
    if x.shape != y.shape or x.shape != z.shape or z.ndim != 2:
        raise ValueError('X, Y and Z must describe the same rectangular grid')
    if np.any(np.diff(x[0]) <= 0) or np.any(np.diff(y[:, 0]) <= 0):
        raise ValueError('Regular-grid coordinates must be increasing')
    if not np.allclose(x, x[0][None, :]) or not np.allclose(y, y[:, 0][:, None]):
        raise ValueError('Use the native triangulated surface API for an irregular grid')
    profile = profile or {}
    norm = norm if norm is not None else Normalize(z.min(), z.max())
    fx = np.unique(np.r_[x[0], np.linspace(x.min(), x.max(), 100)])
    fy = np.unique(np.r_[y[:, 0], np.linspace(y.min(), y.max(), 100)])
    along_x = np.array([np.interp(fx, x[0], row) for row in z])
    zz = np.array([np.interp(fy, y[:, 0], column) for column in along_x.T]).T
    xx, yy = np.meshgrid(fx, fy)
    surface = ax.plot_surface(xx, yy, zz, facecolors=cmap(norm(zz)), edgecolor='none',
                              linewidth=0, antialiased=False,
                              shade=profile.get('surfaceShading', True),
                              lightsource=LightSource(azdeg=315, altdeg=55),
                              rcount=len(fy), ccount=len(fx))
    surface.set_cmap(cmap)
    surface.set_norm(norm)
    ax.plot_wireframe(x, y, z, rcount=mesh_count, ccount=mesh_count,
                      color='#425466', linewidth=.4, alpha=.9)
    for bx, by, bz in ((x[0], y[0], z[0]), (x[-1], y[-1], z[-1]),
                      (x[:, 0], y[:, 0], z[:, 0]), (x[:, -1], y[:, -1], z[:, -1])):
        ax.plot(bx, by, bz, color='#364655', linewidth=.55)
    return surface


def save_preview_svg(fig, target, **savefig_kwargs):
    """Save a seam-free native screen preview without changing editable-series identity."""
    import os
    import xml.etree.ElementTree as ET
    import matplotlib
    from matplotlib.collections import Collection
    from matplotlib.colors import to_rgb, to_hex
    target = os.fspath(target)
    os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
    changed, seamfree, raster_axes = [], set(), []
    try:
        for ax in fig.axes:
            previous = ax.get_rasterization_zorder()
            if previous is not None:
                raster_axes.append((ax, previous))
                ax.set_rasterization_zorder(None)
        for index, artist in enumerate(fig.findobj()):
            gid, rasterized = artist.get_gid(), artist.get_rasterized()
            changed.append((artist, gid, rasterized))
            if rasterized:
                artist.set_rasterized(False)
            if isinstance(artist, Collection) and len(artist.get_facecolors()) and not len(artist.get_edgecolors()):
                key = 'mrite-preview-fill-' + str(index)
                seamfree.add(key)
                artist.set_gid(key)
        with matplotlib.rc_context({'svg.fonttype': 'path'}):
            options = {'bbox_inches': 'tight', 'facecolor': 'white', **savefig_kwargs}
            fig.savefig(target, format='svg', **options)
        tree = ET.parse(target)
        ns = {'s': 'http://www.w3.org/2000/svg'}
        for group in tree.getroot().findall('.//s:g', ns):
            if group.get('id') not in seamfree:
                continue
            for path in group.findall('.//s:path', ns):
                style = dict(item.strip().split(':', 1) for item in path.get('style', '').split(';') if ':' in item)
                style = {key: value.strip() for key, value in style.items()}
                fill = style.get('fill', '')
                if not fill.startswith('#'):
                    continue
                alpha = float(style.get('fill-opacity', '1'))
                fill = to_hex([alpha * channel + 1 - alpha for channel in to_rgb(fill)])
                style.update({'fill': fill, 'fill-opacity': '1', 'stroke': fill,
                              'stroke-opacity': '1', 'stroke-width': '0.3',
                              'stroke-linejoin': 'round', 'shape-rendering': 'crispEdges'})
                path.set('style', '; '.join(key + ': ' + value for key, value in style.items()))
        ET.register_namespace('', ns['s'])
        ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
        tree.write(target, encoding='utf-8', xml_declaration=True)
    finally:
        for artist, gid, rasterized in changed:
            artist.set_gid(gid)
            if rasterized:
                artist.set_rasterized(rasterized)
        for ax, previous in raster_axes:
            ax.set_rasterization_zorder(previous)
    return target


def draw_height_gradient_bars(ax, x, y, z, dx, dy, dz, cmap, norm, profile=None, bands=192):
    """Draw square gradient columns back-to-front with crisp, correctly hidden visible rims."""
    import numpy as np
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection
    profile=profile or {}
    arrays=np.broadcast_arrays(*[np.asarray(v,dtype=float) for v in (x,y,z,dx,dy,dz)])
    rows=list(zip(*[a.ravel() for a in arrays]));angle=np.radians(ax.azim)
    view=np.array([np.cos(angle),np.sin(angle)])
    visible=[5 if view[0]>=0 else 4,3 if view[1]>=0 else 2]
    order=sorted(range(len(rows)),key=lambda i:np.dot([rows[i][0]+rows[i][3]/2,rows[i][1]+rows[i][4]/2],view))
    ax.computed_zorder=False;parts=[];frames=[]
    for rank,index in enumerate(order):
        x0,y0,z0,width,depth,height=rows[index];x1,y1,z1=x0+width,y0+depth,z0+height
        levels=np.linspace(z0,z1,max(2,int(bands))+1)
        shade=get_bar_facecolors(cmap(norm((levels[:-1]+levels[1:])/2)),profile=profile).reshape(-1,6,4)
        vertices=[];colors=[]
        for j,(a,b) in enumerate(zip(levels[:-1],levels[1:])):
            faces={2:[(x0,y0,a),(x1,y0,a),(x1,y0,b),(x0,y0,b)],
                   3:[(x0,y1,a),(x1,y1,a),(x1,y1,b),(x0,y1,b)],
                   4:[(x0,y0,a),(x0,y1,a),(x0,y1,b),(x0,y0,b)],
                   5:[(x1,y0,a),(x1,y1,a),(x1,y1,b),(x1,y0,b)]}
            for face in visible:vertices.append(faces[face]);colors.append(shade[j,face])
        vertices.append([(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)])
        colors.append(get_bar_facecolors(cmap(norm([z1])),profile=profile).reshape(-1,6,4)[0,1])
        body=Poly3DCollection(vertices,facecolors=colors,edgecolors='none',linewidths=0,antialiased=False,zsort='average')
        body.set_zorder(2+2*rank);body._mrite_bar_index=index;ax.add_collection3d(body);parts.append(body)
        lower=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0)]
        upper=[(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
        side_edges={2:(0,1),3:(3,2),4:(0,3),5:(1,2)}
        corners=set(k for face in visible for k in side_edges[face])
        edges=[[lower[k],upper[k]] for k in sorted(corners)]
        edges.extend([[upper[k],upper[(k+1)%4]] for k in range(4)])
        edges.extend([[lower[a],lower[b]] for face in visible for a,b in [side_edges[face]]])
        rim=Line3DCollection(edges,colors='#364655',linewidths=profile.get('barEdgeWidth3d',.55),antialiaseds=True)
        rim.set_zorder(2+2*rank+.2);rim._mrite_bar_index=index;ax.add_collection3d(rim);frames.append(rim)
    ax.auto_scale_xyz(np.r_[arrays[0].ravel(),(arrays[0]+arrays[3]).ravel()],
                      np.r_[arrays[1].ravel(),(arrays[1]+arrays[4]).ravel()],
                      np.r_[arrays[2].ravel(),(arrays[2]+arrays[5]).ravel()])
    spanx=np.ptp(ax.get_xlim());spany=np.ptp(ax.get_ylim());ax.set_box_aspect((spanx,spany,.8*max(spanx,spany)))
    parts[0]._mrite_bar_parts=parts;parts[0]._mrite_bar_frames=frames
    return parts[0]


def apply_plot_material(ax, profile):
    """Apply the selected style's face opacity while keeping fine, opaque boundaries."""
    opacity = profile.get('opacity')
    if not opacity:
        return ax
    import numpy as np
    from matplotlib import colors as mc
    from matplotlib.collections import PathCollection, PolyCollection
    from matplotlib.patches import FancyArrowPatch, PathPatch
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    for patch in ax.patches:
        if isinstance(patch, FancyArrowPatch):
            color = mc.to_rgba(patch.get_edgecolor())
            patch.set_alpha(None);patch.set_color((*color[:3], min(color[3], opacity['link'])))
            continue
        face = mc.to_rgba(patch.get_facecolor())
        if not face[3] or min(face[:3])>.985:
            continue
        codes=patch.get_path().codes
        is_link=isinstance(patch,PathPatch) and codes is not None and np.isin(codes,[3,4]).any()
        target = opacity['link'] if is_link else opacity['fill']
        alpha = min(face[3], target)
        patch.set_alpha(None);patch.set_facecolor((*face[:3],alpha))
        if alpha>.35 and patch.get_linewidth()>0:
            patch.set_edgecolor((0,0,0,1));patch.set_linewidth(profile['edgeWidth'])

    for artist in ax.collections:
        if isinstance(artist, Poly3DCollection):
            if not getattr(artist,'_mrite_clear_material_applied',False):
                # Composite lightly against the white canvas to keep 3D facets free of sorting seams.
                if artist.get_array() is not None:
                    cmap=artist.get_cmap();rgba=cmap(np.linspace(0,1,cmap.N));rgba[:,:3]=opacity['surface']*rgba[:,:3]+1-opacity['surface'];rgba[:,3]=1
                    artist.set_cmap(mc.ListedColormap(rgba,name=cmap.name+'_mrite_surface_clear'))
                else:
                    rgba=np.asarray(artist._facecolor3d).copy();black=np.max(rgba[:,:3],axis=1)<.01;rgba[~black,:3]=opacity['surface']*rgba[~black,:3]+1-opacity['surface'];rgba[:,3]=1
                    artist.set_facecolor(rgba)
                artist.set_alpha(None);artist._mrite_clear_material_applied=True
            continue
        is_point = isinstance(artist, PathCollection)
        values = artist.get_array()
        if not is_point and not isinstance(artist, PolyCollection) and values is None:
            continue
        faces = np.asarray(artist.get_facecolors())
        if not len(faces):
            continue
        target = opacity['scatter'] if is_point else opacity['heatmap'] if values is not None else opacity['fill']
        original = artist.get_alpha()
        if original is not None:
            target = min(target,float(np.min(original)))
        if values is not None:
            if is_point:
                cmap=artist.get_cmap()
                if not cmap.name.endswith('_mrite_clear'):
                    rgba=cmap(np.linspace(0,1,cmap.N));rgba[:,3]=np.minimum(rgba[:,3],target)
                    artist.set_alpha(None);artist.set_cmap(mc.ListedColormap(rgba,name=cmap.name+'_mrite_clear'))
                    artist.set_edgecolor((0,0,0,1))
            else:
                artist.set_alpha(target)
            continue
        faces=faces.copy();faces[:,3]=np.minimum(faces[:,3],target)
        artist.set_alpha(None);artist.set_facecolor(faces)
        if is_point or target>.35 and len(artist.get_edgecolors()):
            artist.set_edgecolor((0,0,0,1))

    for line in ax.lines:
        color=mc.to_rgba(line.get_color())
        if np.ptp(color[:3])<.06:
            continue
        previous=line.get_alpha();line.set_alpha(None);line.set_color((*color[:3],min(color[3],opacity['line'],previous if previous is not None else 1)))
        if line.get_marker() not in [None,'None','',' ']:
            face=line.get_markerfacecolor()
            if isinstance(face,str) and face=='auto':face=color
            face=mc.to_rgba(face)
            if face[3] and min(face[:3])<.985:line.set_markerfacecolor((*face[:3],min(face[3],opacity['scatter'])))
            line.set_markeredgecolor('black')
    return ax


def get_color_map(scheme=None, kind='sequential'):
    """Get the selected scheme's scalar mapping; kind reflects the variable's meaning."""
    import json
    from pathlib import Path
    from matplotlib.colors import LinearSegmentedColormap
    if kind not in ('sequential', 'diverging', 'cyclic'):
        raise ValueError('kind must be sequential, diverging or cyclic')
    if scheme is None:
        with open(Path(_PROJECT_ROOT) / '.mrite/state/solve-configuration.json', encoding='utf-8') as stream:
            configuration = json.load(stream)
            scheme = configuration.get('plotStyle') or configuration.get('colorScheme', 'modelviz')
    with open(Path(_PROJECT_ROOT) / '.mrite/state/chart-color-maps.json', encoding='utf-8') as stream:
        colors = json.load(stream)[scheme][kind]
    return plt.colormaps[colors] if isinstance(colors, str) else LinearSegmentedColormap.from_list(scheme + '_' + kind, colors, N=1024)


def get_correlation_scale(scheme=None):
    """Return a continuous correlation map centered at zero over [-1, 1]."""
    from matplotlib.colors import TwoSlopeNorm
    return get_color_map(scheme, 'diverging'), TwoSlopeNorm(vmin=-1, vcenter=0, vmax=1)


def get_colors(cmap_name, n):
    """安全获取colormap的n个颜色（替代plt.cm.get_cmap，已废弃会报错）。"""
    cmap = plt.colormaps[cmap_name].resampled(n)
    return [cmap(i) for i in range(n)]

def safe_cmap(cmap_name):
    """安全获取colormap对象（不带resampled）。"""
    return plt.colormaps[cmap_name]

def safe_boxplot(ax, data, labels, **kwargs):
    """安全的boxplot（替代ax.boxplot(labels=...)，labels参数已废弃会报错）。
    内部强制 patch_artist=True，使 boxes 为 Patch 对象，AI 可直接用 bp['boxes'][i].set_facecolor(...) 填色；
    否则 boxes 是 Line2D，set_facecolor 会抛 AttributeError。"""
    kwargs.setdefault('patch_artist', True)
    bp = ax.boxplot(data, **kwargs)
    ax.set_xticklabels(labels, fontsize=11)
    return bp

def safe_heatmap(ax, data, row_labels=None, col_labels=None, cmap=None,
                 linewidth=0.3, edgecolor='black', fontsize=11,
                 annotate=True, fmt=None, nan_text='—',
                 textcolors=('black', 'white'), **kwargs):
    """
    强制带黑色细边框且逐格标数值的热力图（替代裸 imshow/heatmap 的纯色块）。
    用 pcolormesh 绘制，每个格子边线统一为黑色细框（edgecolor=black, linewidth=linewidth），
    避免"色块连成一片"的观感。NaN 单元格填白色。默认 vmin/vmax 取数据范围。
    用法：
        safe_heatmap(ax, corr.values, row_labels=corr.index, col_labels=corr.columns,
                     cmap=selected_cmap, fmt='.2f')
    返回 pcolormesh 的 QuadMesh（可用其 .set_clim 调色标范围）。
    """
    data = np.asarray(data, dtype=float)
    rows, cols = data.shape
    # Use the selected continuous coefficient scale for an unambiguous correlation matrix.
    # Explicit caller mappings and non-correlation matrices keep their own scale.
    if (cmap is None and not any(name in kwargs for name in ('norm', 'vmin', 'vmax'))
            and rows == cols and np.allclose(np.diag(data), 1)
            and np.allclose(data, data.T, equal_nan=True)):
        finite = data[np.isfinite(data)]
        if finite.size and finite.min() >= -1-1e-9 and finite.max() <= 1+1e-9:
            try:
                cmap, kwargs['norm'] = get_correlation_scale()
            except (OSError, KeyError):
                pass  # Older workspaces may not contain the shared color snapshot.
    if cmap is None:
        cmap = plt.rcParams.get('image.cmap')
    cmap_obj = plt.colormaps[cmap].copy() if isinstance(cmap, str) else cmap.copy()
    cmap_obj.set_bad(color='white')             # NaN 为白，避免黑洞
    mesh = ax.pcolormesh(np.ma.masked_invalid(data), cmap=cmap_obj,
                         edgecolors=edgecolor, linewidth=linewidth, **kwargs)
    if row_labels is not None:
        ax.set_yticks(np.arange(rows) + 0.5)
        ax.set_yticklabels(list(row_labels), fontsize=fontsize)
    if col_labels is not None:
        ax.set_xticks(np.arange(cols) + 0.5)
        ax.set_xticklabels(list(col_labels), rotation=45, ha='right',
                           rotation_mode='anchor', fontsize=fontsize)
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    ax.set_aspect('auto')
    if annotate:
        finite = data[np.isfinite(data)]
        integer_like = finite.size > 0 and np.allclose(finite, np.round(finite))
        absmax = float(np.max(np.abs(finite))) if finite.size else 0.0

        def _format_value(value):
            if fmt is None:
                if integer_like:
                    return f'{value:.0f}'
                if absmax <= 2:
                    return f'{value:.2f}'
                if absmax < 100:
                    return f'{value:.1f}'
                return f'{value:.0f}'
            if callable(fmt):
                return str(fmt(value))
            spec = str(fmt)
            return spec.format(value) if '{' in spec else format(value, spec)

        for i in range(rows):
            for j in range(cols):
                value = data[i, j]
                if np.isfinite(value):
                    rgba = cmap_obj(mesh.norm(value))
                    luminance = 0.2126 * rgba[0] + 0.7152 * rgba[1] + 0.0722 * rgba[2]
                    color = textcolors[0] if luminance >= 0.58 else textcolors[1]
                    label = _format_value(value)
                else:
                    color = textcolors[0]
                    label = nan_text
                ax.text(j + 0.5, i + 0.5, label, ha='center', va='center',
                        fontsize=fontsize, color=color, fontproperties=ZH_FONT)
    return mesh

def png_wh(png_path):
    """读取PNG实际宽高（字节，读16-24字节IHDR）"""
    import struct
    with open(png_path, 'rb') as f:
        f.read(16)
        w, h = struct.unpack('>II', f.read(8))
    return w, h

def latex_includegraphics(png_path, caption, label, pair=False, float_pos='ht'):
    r"""
    按高宽比生成匹配档位的 \includegraphics LaTeX 片段（直接粘论文）。
    pair=True：同一张figure里两张并排minipage，给半宽。float_pos默认'ht'，禁止'H'锁死。
    """
    if float_pos.upper() == 'H':
        raise ValueError("float_pos禁止'H'强制定位，默认用'ht'允许浮动")
    w, h = png_wh(png_path)
    aspect = h / w
    if pair:
        width = '0.48\\textwidth'
    elif aspect >= 0.9:
        width = '0.60\\textwidth'
    elif aspect >= 0.6:
        width = '0.65\\textwidth'
    else:
        width = '0.70\\textwidth'
    rel = png_path.replace('\\', '/')
    return (
        f"\\begin{{figure}}[{float_pos}]\n"
        f"  \\centering\n"
        f"  \\includegraphics[width={width}]{{{rel}}}\n"
        f"  \\caption{{{caption}}}\n"
        f"  \\label{{fig:{label}}}\n"
        f"\\end{{figure}}"
    )

# ★ 数据清洗辅助（避免 "--" 等非数值导致 min/max/idxmax 报错）
def numeric_clean(s, default=None):
    """将列安全转为数值：非数值元素→NaN；default 不为 None 时用 default 填充NaN。
    用法：df['评分'] = numeric_clean(df['评分'])   # 先转数值（NaN保留）
          df['评分'] = numeric_clean(df['评分'], default=0.0)   # 转数值并填0"""
    s = pd.to_numeric(s, errors='coerce')
    if default is not None:
        s = s.fillna(default)
    return s

def safe_idxmax(s, default_idx=None):
    """安全的 idxmax：空序列/全NA 返回 default_idx，否则返回最大值索引。"""
    s = pd.to_numeric(s, errors='coerce')
    s = s.dropna()
    if s.empty:
        return default_idx
    return s.idxmax()

def safe_idxmin(s, default_idx=None):
    """安全的 idxmin：空序列/全NA 返回 default_idx，否则返回最小值索引。"""
    s = pd.to_numeric(s, errors='coerce')
    s = s.dropna()
    if s.empty:
        return default_idx
    return s.idxmin()

def has_na(df):
    """检测DataFrame是否含NaN/空值（用于空值防线）。"""
    return bool(df.isna().any().any())
