"""
PDF 报告生成模块
为奖学金评审系统提供 PDF 格式的评审报告导出功能。
依赖: reportlab（可选，未安装时优雅降级）
"""

# pyright: reportMissingImports=false

import os
import logging
import importlib
from datetime import datetime

logger = logging.getLogger(__name__)

# ---- 尝试导入 reportlab ----
try:
    _pagesizes = importlib.import_module('reportlab.lib.pagesizes')
    _units = importlib.import_module('reportlab.lib.units')
    _styles = importlib.import_module('reportlab.lib.styles')
    _colors = importlib.import_module('reportlab.lib.colors')
    _enums = importlib.import_module('reportlab.lib.enums')
    _platypus = importlib.import_module('reportlab.platypus')
    _pdfbase = importlib.import_module('reportlab.pdfbase.pdfmetrics')
    _ttfonts = importlib.import_module('reportlab.pdfbase.ttfonts')

    A4 = _pagesizes.A4
    mm = _units.mm
    cm = _units.cm
    getSampleStyleSheet = _styles.getSampleStyleSheet
    ParagraphStyle = _styles.ParagraphStyle
    HexColor = _colors.HexColor
    black = _colors.black
    white = _colors.white
    grey = _colors.grey
    TA_CENTER = _enums.TA_CENTER
    TA_LEFT = _enums.TA_LEFT
    TA_RIGHT = _enums.TA_RIGHT
    SimpleDocTemplate = _platypus.SimpleDocTemplate
    Table = _platypus.Table
    TableStyle = _platypus.TableStyle
    Paragraph = _platypus.Paragraph
    Spacer = _platypus.Spacer
    PageBreak = _platypus.PageBreak
    KeepTogether = _platypus.KeepTogether
    pdfmetrics = _pdfbase
    TTFont = _ttfonts.TTFont

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# ---- 中文字体注册 ----
_FONT_REGISTERED = False
_FONT_NAME = None


def _register_chinese_font():
    """尝试注册中文字体，按优先级查找常见系统字体路径。"""
    global _FONT_REGISTERED, _FONT_NAME
    if _FONT_REGISTERED or not REPORTLAB_AVAILABLE:
        return _FONT_REGISTERED

    candidates = [
        # Windows
        ("C:/Windows/Fonts/simsun.ttc", "SimSun"),
        ("C:/Windows/Fonts/msyh.ttc", "MicrosoftYaHei"),
        ("C:/Windows/Fonts/simhei.ttf", "SimHei"),
        ("C:/Windows/Fonts/kaiu.ttf", "KaiTi"),
        # macOS
        ("/System/Library/Fonts/PingFang.ttc", "PingFang"),
        ("/System/Library/Fonts/STHeiti Light.ttc", "STHeiti"),
        ("/Library/Fonts/Arial Unicode.ttf", "ArialUnicode"),
        # Linux
        ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", "WenQuanYi"),
        ("/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf", "DroidSans"),
        ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "NotoSansCJK"),
    ]

    for path, name in candidates:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                _FONT_REGISTERED = True
                _FONT_NAME = name
                logger.info(f"中文字体已注册: {name} ({path})")
                return True
            except Exception:
                continue

    logger.warning("未找到系统中文字体，PDF 中文可能显示为方块")
    return False


def _get_font_name():
    """返回已注册的中文字体名，若未注册则返回 'Helvetica'。"""
    _register_chinese_font()
    if _FONT_REGISTERED and _FONT_NAME:
        return _FONT_NAME
    return 'Helvetica'


# ---- 样式常量 ----
if REPORTLAB_AVAILABLE:
    PRIMARY_COLOR = HexColor('#1a5276')
    SECONDARY_COLOR = HexColor('#2980b9')
    LIGHT_BG = HexColor('#f2f4f4')
    BORDER_COLOR = HexColor('#bdc3c7')
else:
    PRIMARY_COLOR = None
    SECONDARY_COLOR = None
    LIGHT_BG = None
    BORDER_COLOR = None


def _build_styles(font_name):
    """构建 reportlab 段落样式表。"""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        'ChineseTitle',
        parent=styles['Title'],
        fontName=font_name,
        fontSize=18,
        leading=24,
        alignment=TA_CENTER,
        spaceAfter=6 * mm,
    ))
    styles.add(ParagraphStyle(
        'ChineseHeading',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=14,
        leading=18,
        spaceBefore=5 * mm,
        spaceAfter=3 * mm,
        textColor=PRIMARY_COLOR,
    ))
    styles.add(ParagraphStyle(
        'ChineseBody',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        leading=15,
    ))
    styles.add(ParagraphStyle(
        'ChineseSmall',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=8,
        leading=11,
        textColor=grey,
    ))
    return styles


def check_reportlab():
    """检查 reportlab 是否可用。"""
    return REPORTLAB_AVAILABLE


# ---- 个人评审报告 ----
def generate_student_report(file_path, student_info, df, statistics, capped_total,
                            project_types=None, reviewer_name=None):
    """
    生成单个学生的评审报告 PDF。

    参数:
        file_path: 输出 PDF 路径
        student_info: 学生信息字典 {学院, 姓名, 年级, 班级, 学号}
        df: pandas DataFrame，包含评审后的奖项数据
        statistics: {项目类型: 截断后得分}
        capped_total: 截断后总分
        project_types: 项目类型列表（用于排序）
        reviewer_name: 评审人姓名

    返回:
        dict: {'success': bool, 'message': str, 'file_path': str}
    """
    result = {'success': False, 'message': '', 'file_path': file_path}

    if not REPORTLAB_AVAILABLE:
        result['message'] = 'reportlab 未安装，无法生成 PDF。请运行: pip install reportlab'
        return result

    font_name = _get_font_name()
    styles = _build_styles(font_name)

    try:
        doc = SimpleDocTemplate(
            file_path, pagesize=A4,
            leftMargin=20 * mm, rightMargin=20 * mm,
            topMargin=15 * mm, bottomMargin=15 * mm,
        )
        story = []

        # ---- 标题 ----
        story.append(Paragraph("优秀学生奖学金加分项目评审报告", styles['ChineseTitle']))
        story.append(Spacer(1, 3 * mm))

        # ---- 学生基本信息表 ----
        info_data = [
            ['学院', student_info.get('学院', ''),
             '姓名', student_info.get('姓名', '')],
            ['年级', student_info.get('年级', ''),
             '班级', student_info.get('班级', '')],
            ['学号', student_info.get('学号', ''),
             '评审日期', datetime.now().strftime('%Y-%m-%d')],
        ]
        info_table = Table(info_data, colWidths=[50, 120, 100, 240])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (0, -1), LIGHT_BG),
            ('BACKGROUND', (2, 0), (2, -1), LIGHT_BG),
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 8 * mm))

        # ---- 奖项明细表 ----
        story.append(Paragraph("奖项评审明细", styles['ChineseHeading']))

        if df is not None and not df.empty:
            # 表头
            header = ['序号', '奖项名称', '获奖时间', '奖项等级', '项目类型', '评定等级', '认定情况', '加分', '备注']
            col_widths = [25, 110, 65, 55, 60, 55, 45, 30, 70]
            
            # 创建单元格样式（支持自动换行）
            cell_style = ParagraphStyle(
                'TableCell',
                fontName=font_name,
                fontSize=8,
                leading=10,
                wordWrap='CJK',
            )
            header_style = ParagraphStyle(
                'TableHeader',
                fontName=font_name,
                fontSize=8,
                leading=10,
                textColor=white,
                alignment=TA_CENTER,
            )
            
            table_data = [[
                Paragraph(col, header_style) for col in header
            ]]

            for i, (_, row) in enumerate(df.iterrows()):
                # 只取年月日（取前10个字符 'YYYY-MM-DD'）
                award_time = str(row.get('获奖时间', ''))[:10]
                row_data = [
                    Paragraph(str(i + 1), cell_style),
                    Paragraph(str(row.get('所获奖项名称', '')), cell_style),
                    Paragraph(award_time, cell_style),
                    Paragraph(str(row.get('奖项等级', '')), cell_style),
                    Paragraph(str(row.get('项目类型', '')), cell_style),
                    Paragraph(str(row.get('评定等级', '')), cell_style),
                    Paragraph(str(row.get('认定情况', '')), cell_style),
                    Paragraph(str(row.get('加分', '')), cell_style),
                    Paragraph(str(row.get('备注', '')), cell_style),
                ]
                table_data.append(row_data)

            tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
            tbl_style = [
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('ALIGN', (6, 0), (7, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.3, BORDER_COLOR),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (-1, -1), 3),
                ('RIGHTPADDING', (0, 0), (-1, -1), 3),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, LIGHT_BG]),
            ]
            tbl.setStyle(TableStyle(tbl_style))
            story.append(tbl)
        else:
            story.append(Paragraph("（无奖项数据）", styles['ChineseBody']))

        story.append(Spacer(1, 8 * mm))

        # ---- 统计汇总 ----
        story.append(Paragraph("分类统计汇总", styles['ChineseHeading']))

        stat_header = ['项目类型', '得分']
        stat_data = [stat_header]
        if project_types is None:
            project_types = list(statistics.keys()) if statistics else []
        for pt in project_types:
            stat_data.append([pt, str(statistics.get(pt, 0))])
        stat_data.append(['合计（截断后）', str(capped_total)])

        stat_tbl = Table(stat_data, colWidths=[120, 60])
        stat_tbl.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, 0), SECONDARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('BACKGROUND', (0, -1), (-1, -1), LIGHT_BG),
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(stat_tbl)

        # ---- 页脚 ----
        story.append(Spacer(1, 15 * mm))
        footer_text = f"评审人: {reviewer_name or '—'}　　导出时间: {datetime.now().strftime('%Y-%m-%d')}"
        story.append(Paragraph(footer_text, styles['ChineseSmall']))

        # 生成
        doc.build(story)
        result['success'] = True
        result['message'] = '个人评审报告 PDF 已生成'
        logger.info(f"个人报告 PDF 已生成: {file_path}")

    except Exception as e:
        result['message'] = f'PDF 生成失败: {str(e)}'
        logger.error(result['message'], exc_info=True)

    return result


# ---- 批量汇总报告 ----
def generate_batch_summary_report(file_path, all_students_data, project_types=None,
                                  reviewer_name=None):
    """
    生成批量汇总 PDF 报告，包含所有学生的总分排名表。

    参数:
        file_path: 输出 PDF 路径
        all_students_data: [(学生姓名, 学院, 班级, 学号, 统计字典, 截断总分), ...]
        project_types: 项目类型列表
        reviewer_name: 评审人

    返回:
        dict: {'success': bool, 'message': str, 'file_path': str}
    """
    result = {'success': False, 'message': '', 'file_path': file_path}

    if not REPORTLAB_AVAILABLE:
        result['message'] = 'reportlab 未安装，无法生成 PDF。请运行: pip install reportlab'
        return result

    font_name = _get_font_name()
    styles = _build_styles(font_name)

    try:
        doc = SimpleDocTemplate(
            file_path, pagesize=A4,
            leftMargin=15 * mm, rightMargin=15 * mm,
            topMargin=15 * mm, bottomMargin=15 * mm,
        )
        story = []

        # 标题
        story.append(Paragraph("奖学金评审批量汇总报告", styles['ChineseTitle']))
        story.append(Paragraph(
            f"导出时间: {datetime.now().strftime('%Y-%m-%d')}　　"
            f"评审人: {reviewer_name or '—'}　　"
            f"总人数: {len(all_students_data)}",
            styles['ChineseSmall']
        ))
        story.append(Spacer(1, 6 * mm))

        if not all_students_data:
            story.append(Paragraph("（无学生数据）", styles['ChineseBody']))
        else:
            # 按总分降序排列
            ranked = sorted(all_students_data, key=lambda x: x[5], reverse=True)

            if project_types is None:
                project_types = []
                for item in ranked:
                    for pt in item[4].keys():
                        if pt not in project_types:
                            project_types.append(pt)

            # 构建表格
            header = ['排名', '姓名', '学院', '班级', '学号'] + project_types + ['总分']
            table_data = [header]

            for rank, item in enumerate(ranked, 1):
                name, college, cls, sid, stats, capped = item
                row = [str(rank), name, college, cls, sid]
                for pt in project_types:
                    row.append(str(stats.get(pt, 0)))
                row.append(str(capped))
                table_data.append(row)

            # 列宽
            n_types = len(project_types)
            type_col_width = max(35, int((A4[0] - 50 - 30 - 60 - 50 - 50 - 60 - 20 * n_types) / n_types))
            col_widths = [25, 55, 65, 50, 75] + [type_col_width] * n_types + [35]

            tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
            tbl_style = [
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 7.5),
                ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('ALIGN', (-1, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.3, BORDER_COLOR),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('LEFTPADDING', (0, 0), (-1, -1), 3),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, LIGHT_BG]),
            ]
            # 第一名高亮
            if len(table_data) > 1:
                tbl_style.append(('BACKGROUND', (0, 1), (-1, 1), HexColor('#fff9c4')))
            tbl.setStyle(TableStyle(tbl_style))
            story.append(tbl)

        doc.build(story)
        result['success'] = True
        result['message'] = f'批量汇总报告 PDF 已生成（{len(all_students_data)} 人）'
        logger.info(f"批量汇总 PDF 已生成: {file_path}")

    except Exception as e:
        result['message'] = f'PDF 生成失败: {str(e)}'
        logger.error(result['message'], exc_info=True)

    return result
