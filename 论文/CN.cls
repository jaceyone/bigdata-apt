\NeedsTeXFormat{LaTeX2e}[1995/12/01]
\ProvidesClass{CN}
              [2017/09/16 v2.6 Standard LaTeX Template for CUMCM]
%% Inital Code
\newif\if@mcm@bwprint\@mcm@bwprintfalse
% 默认中文；可用 [english]/[chinese] 或在导言区调用 \mritesetlanguage{en/zh}。
\newif\ifmriteenglish\mriteenglishfalse
\newcommand*{\mriteifenglish}[2]{\ifmriteenglish#1\else#2\fi}
% tokens definition
% 封面队伍信息
\newcommand\mcm@tokens@keywords{}
\newcommand*\mcm@tokens@tihao{}
\newcommand*\mcm@tokens@baominghao{}
\newcommand*\mcm@tokens@schoolname{}
\newcommand*\mcm@tokens@membera{}
\newcommand*\mcm@tokens@memberb{}
\newcommand*\mcm@tokens@memberc{}
\newcommand*\mcm@tokens@supervisor{}
\newcommand*\mcm@tokens@group{}
%% Declaration of Options
\DeclareOption{colorprint}{\@mcm@bwprintfalse}
\DeclareOption{bwprint}{\@mcm@bwprinttrue}
\DeclareOption{english}{\mriteenglishtrue}
\DeclareOption{chinese}{\mriteenglishfalse}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
%% Executing of Options
\ExecuteOptions{colorprint}
\ProcessOptions\relax
%% Loading Class
\LoadClass[a4paper,12pt]{article}
%% Loading Package
\RequirePackage{iftex}
\ifPDFTeX
  \RequirePackage[T1]{fontenc}
  \RequirePackage{mathptmx}
  \RequirePackage[fontset=none,scheme=plain]{ctex}
  \providecommand{\songti}{}
  \providecommand{\heiti}{}
  \providecommand{\kaishu}{}
  \renewcommand{\songti}{\rmfamily}
  \renewcommand{\heiti}{\sffamily}
  \renewcommand{\kaishu}{\itshape}
  \mriteenglishtrue
\else
  \RequirePackage{ctex}
\fi
% 页面布局
\RequirePackage{geometry}
% 数学宏包
\RequirePackage{amsmath}
\RequirePackage{amsfonts}
\RequirePackage{amssymb}
\RequirePackage{bm}
%\RequirePackage{titletoc}
% 设置颜色
\RequirePackage[dvipsnames]{xcolor}
% 插入图片
\RequirePackage{graphicx}
\RequirePackage{float}
% 表格
\RequirePackage{array}
%% 长表格
\RequirePackage{longtable}
%% booktabs 提供了\toprule 等命令.
\RequirePackage{booktabs,tabularx}
%% multirow 支持在表格中跨行
\RequirePackage{multirow}
%% makecell 提供封面信息表所需的加粗横线 \Xhline
\RequirePackage{makecell}

%% 双栏（multicols）环境
\RequirePackage{multicol}
%% 调整间隔, 让表格更好看些
\RequirePackage{bigstrut}
%% 在跨行表格中输入定界符
\RequirePackage{bigdelim}
% 保护脆落命令
\RequirePackage{cprotect}
% 设置代码环境
\RequirePackage{listings}
\RequirePackage{xcolor}
% 插入链接
\RequirePackage{url}
% 绘图的包
\RequirePackage{tikz}
\usetikzlibrary{arrows.meta}
\tikzset{
  box/.style={rectangle, draw, minimum width=3.2cm, minimum height=0.9cm, align=center},
  arrow/.style={thick, -{Stealth}}
}

% 字图与子标题
\RequirePackage{subcaption}
\RequirePackage[titles]{tocloft}
%\renewcommand{\cftdot}{$\cdot$}
%\renewcommand{\cftsecdotsep}{1.5}
\renewcommand{\cftsecdotsep}{4.5}
\setlength{\cftbeforesecskip}{7pt}
\setlength{\cftbeforesubsecskip}{3pt}
%\setlength{\cftbeforesubsecskip}{5pt}
\renewcommand{\cftsecfont}{\bfseries\zihao{-4}\song}
\renewcommand{\cftsecleader}{\cftdotfill{\cftsecdotsep}}
\renewcommand{\cftsecaftersnumb}{\hskip.4em}
%%目录
\RequirePackage{titlesec}
\RequirePackage{titletoc}
\renewcommand{\contentsname}{目录}
\titlecontents{section}[0em]{\songti\zihao{-4}}{\thecontentslabel\ }{}
{\hspace{.5em}\titlerule*[4pt]{$\cdot$}\contentspage}
\titlecontents{subsection}[2em]{\vspace{0.1\baselineskip}\songti\zihao{-4}}{\thecontentslabel\ }{}
{\hspace{.5em}\titlerule*[4pt]{$\cdot$}\contentspage}
\titlecontents{subsubsection}[4em]{\vspace{0.1\baselineskip}\songti\zihao{-4}}{\thecontentslabel\ }{}
{\hspace{.5em}\titlerule*[4pt]{$\cdot$}\contentspage}

\newcolumntype{Y}{>{\centering\arraybackslash}X}
\newcolumntype{C}{>{\centering\arraybackslash}X}
\newcolumntype{L}{>{\raggedright\arraybackslash}X}



\ifPDFTeX
  \newcommand{\yaheiconsola}{\ttfamily}
\else
  \RequirePackage{fontspec}
  \newfontfamily\yaheiconsola{Consolas}
  \setmonofont{Consolas}
\fi

\definecolor{codegreen}{rgb}{0,0.6,0}


\lstset
{
    tabsize=4,
    captionpos=b,
    numbers=left,                    
    numbersep=1em,                  
    sensitive=true,
    showtabs=false, 
    frame=shadowbox,
    breaklines=true,
    keepspaces=true,                 
    showspaces=false,                
    showstringspaces=false,
    breakatwhitespace=false,         
    basicstyle=\yaheiconsola,
    keywordstyle=\color{NavyBlue},
    commentstyle=\color{codegreen},
    numberstyle=\color{gray},
    stringstyle=\color{PineGreen!90!black},
    rulesepcolor=\color{red!20!green!20!blue!20}
}
% 首行缩进
\RequirePackage{indentfirst}
% 设置浮动体的标题
\RequirePackage{caption}
% 定制列表环境
\RequirePackage{enumitem}
% 下划线
\RequirePackage{ulem}
% 尺寸计算
\RequirePackage{calc}

\RequirePackage[titletoc,title]{appendix}

%\RequirePackage[title,toc,titletoc]{appendix}

\RequirePackage{etoolbox}
\newcommand*{\mritesetlanguage}[1]{%
  \ifstrequal{#1}{en}{\mriteenglishtrue}{%
    \ifstrequal{#1}{zh}{\mriteenglishfalse}{%
      \ClassError{CN}{Unsupported language: #1}{Use en or zh.}}}}
\newcommand*{\mriteheadingfont}{\mriteifenglish{\rmfamily}{\song}}
\AtBeginEnvironment{thebibliography}{%
    \phantomsection
    \addcontentsline{toc}{section}{\refname}
    }
% 超链接 hyperref 的设置
\RequirePackage{hyperref}
% 智能自动化交叉引用
\RequirePackage{cleveref}
%% Document Layout
% 页面布局
\geometry{top=25mm,bottom=25mm,left=25mm,right=25mm}
% 正文统一单倍行距。
\renewcommand*{\baselinestretch}{1}
% 修改tabular 环境, 设置表格中的行间距为正文行间距.
\let\mcm@oldtabular\tabular
\let\mcm@endoldtabular\endtabular
\renewenvironment{tabular}%
	{\bgroup%
	\renewcommand{\arraystretch}{1.38}%
	\mcm@oldtabular}%
	{\mcm@endoldtabular\egroup}
% 所有正文表格统一小五（9bp），在环境内部设置，结束后自动恢复正文字号。
% longtable 是各竞赛模板的正文表格入口；同时覆盖普通及定宽表格。
\AtBeginEnvironment{longtable}{\zihao{-5}}
\AtBeginEnvironment{tabular}{\zihao{-5}}
\AtBeginEnvironment{tabular*}{\zihao{-5}}
\AtBeginEnvironment{tabularx}{\zihao{-5}}
% 每行缩进两个汉字
\setlength\parindent{2em}



% 设置字体（替换宋体为思源宋体）
\ifPDFTeX
  \newcommand{\kai}{\itshape}
  \newcommand{\song}{\rmfamily}
  \newcommand{\mriteli}{\rmfamily}
\else
\setmainfont{Times New Roman}
\setsansfont{Arial}
\setCJKfamilyfont{kai}[AutoFakeBold]{simkai.ttf}
\newcommand*{\kai}{\CJKfamily{kai}}



\setCJKfamilyfont{song}[%
Path = ./fonts/,  % 注意最后的斜杠！
UprightFont = SourceHanSerifCN-Regular.otf,
BoldFont = SourceHanSerifCN-Bold.otf
]{SourceHanSerifCN}

\newcommand*{\song}{\CJKfamily{song}}
\renewcommand{\textbf}[1]{{\song\bfseries #1}}

% 随模板携带的隶书字体，供封面「题目」标签与摘要标题、关键词标签局部调用。
\setCJKfamilyfont{mriteli}[%
Path = ./fonts/,
UprightFont = SIMLI.TTF,
AutoFakeBold = 2
]{SIMLI}
\newcommand*{\mriteli}{\CJKfamily{mriteli}}

% 中文斜体用伪斜体（避免 ctex 默认跳到楷体）
\setCJKmainfont[Path=./fonts/, UprightFont=SourceHanSerifCN-Regular.otf, BoldFont=SourceHanSerifCN-Bold.otf, AutoFakeSlant=0.25]{SourceHanSerifCN}
\fi



\renewcommand\normalsize{%
	\@setfontsize\normalsize{12.05}{14.45}%
	\abovedisplayskip 12\p@ \@plus3\p@ \@minus7\p@
	\abovedisplayshortskip \z@ \@plus3\p@
	\belowdisplayshortskip 6.5\p@ \@plus3.5\p@ \@minus3\p@}

% ── 修复字号命令：ctex 把 \large 映射成≈正文字号，这里重定义为标准递进 ──
\renewcommand{\large}{\@setfontsize\large{14.4}{17.28}}
\renewcommand{\Large}{\@setfontsize\Large{17.28}{20.74}}
\renewcommand{\LARGE}{\@setfontsize\LARGE{20.74}{24.88}}
\renewcommand{\huge}{\@setfontsize\huge{24.88}{29.86}}
\renewcommand{\Huge}{\@setfontsize\Huge{29.86}{35.83}}
\renewcommand{\small}{\@setfontsize\small{11}{13.6}}
\renewcommand{\footnotesize}{\@setfontsize\footnotesize{10}{12}}
% 数学环境, 定理等设置
\newtheorem{definition}{\mcm@cap@definition}
\newtheorem{theorem}{\mcm@cap@theorem}
\newtheorem{lemma}{\mcm@cap@lemma}
\newtheorem{corollary}{\mcm@cap@corollary}
\newtheorem{assumption}{\mcm@cap@assumption}
\newtheorem{conjecture}{\mcm@cap@conjecture}
\newtheorem{axiom}{\mcm@cap@axiom}
\newtheorem{principle}{\mcm@cap@principle}
\newtheorem{problem}{\mcm@cap@problem}
\newtheorem{example}{\mcm@cap@example}
\newtheorem{proof}{\mcm@cap@proof}
\newtheorem{solution}{\mcm@cap@solution}

% 浮动环境设置
% 默认情况下, \LaTeX{} 要求每页的文字至少占据 20%,否则该页就只单独放置一个浮动环境,
% 而这通常不是我们想要的, 我们将这个要求降低到 5%.
 \renewcommand*{\textfraction}{0.05}
% 有时如果多个浮动环境连续放在一起, \LaTeX{}
% 会将它们分在几个不同页，即使它们可在同一页放
% 得下. 我们可以通过修改 |\topfraction| 和 |\bottomfraction| 分别设置顶端和底端的浮
% 动环境的最大比例.
 \renewcommand*{\topfraction}{0.9}
 \renewcommand*{\bottomfraction}{0.8}
% 有时\LaTeX{}会把一个浮动环境单独放在一页,
% 我们要求这个环境至少要占据 85% 才能单独放在一页.
% 注意:  |\floatpagefraction| 的数值必须小于 |\topfraction|.
 \renewcommand*{\floatpagefraction}{0.85}
% 关于图片 graphicx
 % 如果图片没有指定后缀, 依次按下列顺序搜索
\DeclareGraphicsExtensions{.pdf,.eps,.jpg,.png}
% 图表标题
\DeclareCaptionFont{song}{\songti}
\DeclareCaptionFont{minusfour}{\zihao{-4}}
\DeclareCaptionFont{minusfive}{\zihao{-5}}
\captionsetup[figure]{%
	format=hang,   % 标题从第二行开始都有缩进, 应该和 justification=raggedright 的效果一样.
	labelsep=quad, % 分隔符是一个空格
	font={song,minusfour,bf}, % 图的字体, 宋体小四
	position=bottom % position=bottom, 不代表标题放在下面, 标题仍放在你放\caption的位置.
}
\captionsetup[table]{%
	format=hang,   % 标题从第二行开始都有缩进, 应该和 justification=raggedright 的效果一样.
	labelsep=quad, % 分隔符是一个空格
	font={song,minusfive,bf}, % 表题统一宋体小五
	position=top % position=bottom, 不代表标题放在下面, 标题仍放在你放\caption的位置.
}
% 列表环境设置
\setlist{%
	topsep=0.3em, % 列表顶端的垂直空白
	partopsep=0pt, % 列表环境前面紧接着一个空白行时其顶端的额外垂直空白
	itemsep=0ex plus 0.1ex, % 列表项之间的额外垂直空白
	parsep=0pt, % 列表项内的段落之间的垂直空白
	leftmargin=1.5em, % 环境的左边界和列表之间的水平距离
	rightmargin=0em, % 环境的右边界和列表之间的水平距离
	labelsep=0.5em, % 包含标签的盒子与列表项的第一行文本之间的间隔
	labelwidth=2em % 包含标签的盒子的正常宽度；若实际宽度更宽，则使用实际宽度。
}

% 超链接
\hypersetup
{
    pdfstartview=FitH,
    CJKbookmarks=true,
    bookmarksnumbered=true,
    bookmarksopen=true,
    colorlinks, 
    pdfborder=001, 
    allcolors=black,
    breaklinks=true
}
% \if@mcm@bwprint
% \AtBeginDocument{\hypersetup{hidelinks}}
% \else\relax\fi
\pdfstringdefDisableCommands{%
	\def\cftdotfill{ }%
}

%%% crefformat settings
\crefformat{figure}{#2图~#1#3}
\crefrangeformat{figure}{图~(#3#1#4)\;\~{}\;(#5#2#6)}
\crefmultiformat{figure}{图~(#2#1#3)}{和~(#2#1#3)}{，(#2#1#3)}{和~(#2#1#3)}

\crefformat{table}{#2表#1#3}
\crefrangeformat{table}{表(#3#1#4)\;\~{}\;(#5#2#6)}
\crefmultiformat{table}{表~(#2#1#3)}{和~(#2#1#3)}{，(#2#1#3)}{和~(#2#1#3)}

\crefformat{equation}{#2~(#1#3)}
\crefrangeformat{equation}{~(#3#1#4)\;\~{}\;(#5#2#6)}
\crefmultiformat{equation}{~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\crefformat{definition}{#2\mcm@cap@definition~#1#3}
\crefrangeformat{definition}{\mcm@cap@definition~(#3#1#4)\;\~{}\;(#5#2#6)}
\crefmultiformat{definition}{\mcm@cap@definition~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\crefformat{theorem}{#2\mcm@cap@theorem~#1#3}
\crefrangeformat{theorem}{\mcm@cap@theorem~(#3#1#4)\;\~{}\;(#5#2#6)}
\crefmultiformat{theorem}{\mcm@cap@theorem~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\crefformat{lemma}{#2\mcm@cap@lemma~#1#3}
\crefrangeformat{lemma}{\mcm@cap@lemma~(#3#1#4)\;\~{}\;(#5#2#6)}
\crefmultiformat{lemma}{\mcm@cap@lemma~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\crefformat{corollary}{#2\mcm@cap@corollary~#1#3}
\crefrangeformat{corollary}{\mcm@cap@corollary~(#3#1#4)\;\~{}\;(#5#2#6)}
\crefmultiformat{corollary}{\mcm@cap@corollary~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\crefformat{assumption}{#2\mcm@cap@assumption~#1#3}
\crefrangeformat{assumption}{\mcm@cap@assumption~(#3#1#4)\;\~{}\;(#5#2#6)}
\crefmultiformat{assumption}{\mcm@cap@assumption~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\crefformat{conjecture}{#2\mcm@cap@conjecture~#1#3}
\crefrangeformat{conjecture}{\mcm@cap@conjecture~(#3#1#4)\;\~{}\;(#5#2#6)}
\crefmultiformat{conjecture}{\mcm@cap@conjecture~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\crefformat{axiom}{#2\mcm@cap@axiom~#1#3}
\crefrangeformat{axiom}{\mcm@cap@axiom~(#3#1#4)\;\~{}\;(#5#2#6)}
\crefmultiformat{axiom}{\mcm@cap@axiom~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\crefformat{principle}{#2\mcm@cap@principle~#1#3}
\crefrangeformat{principle}{\mcm@cap@principle~(#3#1#4)\;\~{}\;(#5#2#6)}
\crefmultiformat{principle}{\mcm@cap@principle~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\crefformat{problem}{#2\mcm@cap@problem~#1#3}
\crefrangeformat{problem}{\mcm@cap@problem~(#3#1#4)\;\~{}\;(#5#2#6)}
\crefmultiformat{problem}{\mcm@cap@problem~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\crefformat{example}{#2\mcm@cap@example~#1#3}
\crefrangeformat{example}{\mcm@cap@example~(#3#1#4)\;\~{}\;(#5#2#6)}
\crefmultiformat{example}{\mcm@cap@example~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\crefformat{proof}{#2\mcm@cap@proof~#1#3}
\crefrangeformat{proof}{\mcm@cap@proof~(#3#1#4)\;\~{}\;(#5#2#6)}
\crefmultiformat{proof}{\mcm@cap@proof~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\crefformat{solution}{#2\mcm@cap@solution~#1#3}
\crefrangeformat{solution}{\mcm@cap@solution~(#3#1#4)\;\~{}\;(#5#2#6)}
\crefmultiformat{solution}{\mcm@cap@solution~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}
%%% crefformat settings
\Crefformat{figure}{#2图~#1#3}
\Crefrangeformat{figure}{图~(#3#1#4)\;\~{}\;(#5#2#6)}
\Crefmultiformat{figure}{图~(#2#1#3)}{和~(#2#1#3)}{，(#2#1#3)}{和~(#2#1#3)}

\Crefformat{table}{#2表#1#3}
\Crefrangeformat{table}{表(#3#1#4)\;\~{}\;(#5#2#6)}
\Crefmultiformat{table}{表~(#2#1#3)}{和~(#2#1#3)}{，(#2#1#3)}{和~(#2#1#3)}

\Crefformat{equation}{#2~(#1#3)}
\Crefrangeformat{equation}{~(#3#1#4)\;\~{}\;(#5#2#6)}
\Crefmultiformat{equation}{~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\Crefformat{definition}{#2\mcm@cap@definition~#1#3}
\Crefrangeformat{definition}{\mcm@cap@definition~(#3#1#4)\;\~{}\;(#5#2#6)}
\Crefmultiformat{definition}{\mcm@cap@definition~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\Crefformat{theorem}{#2\mcm@cap@theorem~#1#3}
\Crefrangeformat{theorem}{\mcm@cap@theorem~(#3#1#4)\;\~{}\;(#5#2#6)}
\Crefmultiformat{theorem}{\mcm@cap@theorem~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\Crefformat{lemma}{#2\mcm@cap@lemma~#1#3}
\Crefrangeformat{lemma}{\mcm@cap@lemma~(#3#1#4)\;\~{}\;(#5#2#6)}
\Crefmultiformat{lemma}{\mcm@cap@lemma~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\Crefformat{corollary}{#2\mcm@cap@corollary~#1#3}
\Crefrangeformat{corollary}{\mcm@cap@corollary~(#3#1#4)\;\~{}\;(#5#2#6)}
\Crefmultiformat{corollary}{\mcm@cap@corollary~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\Crefformat{assumption}{#2\mcm@cap@assumption~#1#3}
\Crefrangeformat{assumption}{\mcm@cap@assumption~(#3#1#4)\;\~{}\;(#5#2#6)}
\Crefmultiformat{assumption}{\mcm@cap@assumption~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\Crefformat{conjecture}{#2\mcm@cap@conjecture~#1#3}
\Crefrangeformat{conjecture}{\mcm@cap@conjecture~(#3#1#4)\;\~{}\;(#5#2#6)}
\Crefmultiformat{conjecture}{\mcm@cap@conjecture~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\Crefformat{axiom}{#2\mcm@cap@axiom~#1#3}
\Crefrangeformat{axiom}{\mcm@cap@axiom~(#3#1#4)\;\~{}\;(#5#2#6)}
\Crefmultiformat{axiom}{\mcm@cap@axiom~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\Crefformat{principle}{#2\mcm@cap@principle~#1#3}
\Crefrangeformat{principle}{\mcm@cap@principle~(#3#1#4)\;\~{}\;(#5#2#6)}
\Crefmultiformat{principle}{\mcm@cap@principle~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\Crefformat{problem}{#2\mcm@cap@problem~#1#3}
\Crefrangeformat{problem}{\mcm@cap@problem~(#3#1#4)\;\~{}\;(#5#2#6)}
\Crefmultiformat{problem}{\mcm@cap@problem~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\Crefformat{example}{#2\mcm@cap@example~#1#3}
\Crefrangeformat{example}{\mcm@cap@example~(#3#1#4)\;\~{}\;(#5#2#6)}
\Crefmultiformat{example}{\mcm@cap@example~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\Crefformat{proof}{#2\mcm@cap@proof~#1#3}
\Crefrangeformat{proof}{\mcm@cap@proof~(#3#1#4)\;\~{}\;(#5#2#6)}
\Crefmultiformat{proof}{\mcm@cap@proof~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\Crefformat{solution}{#2\mcm@cap@solution~#1#3}
\Crefrangeformat{solution}{\mcm@cap@solution~(#3#1#4)\;\~{}\;(#5#2#6)}
\Crefmultiformat{solution}{\mcm@cap@solution~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%% Document Markup

% 华为杯文件夹型主文件使用的图片封面。
% 参数 1：赛事/合作方 Logo 图片；参数 2：赛事标题图片。
% 这里只补充封面能力，正文的字体、页边距、章节、摘要、图表等仍全部沿用 CN.cls。
\newcommand{\mriteHuaweiCover}[2]{%
  \clearpage
  \thispagestyle{empty}%
  \phantomsection
  \pdfbookmark[1]{\mriteifenglish{Cover}{封面}}{mrite-huawei-cover}%
  \begin{center}%
    \includegraphics[width=.92\textwidth]{#1}\par
    \vspace{1.35cm}%
    \includegraphics[width=.84\textwidth]{#2}\par
  \end{center}%
  \vspace{3.5em}%
  \begin{center}%
  \renewcommand\arraystretch{1.5}%
  \begin{tabularx}{.88\textwidth}{lX}
    \zihao{-2}\bfseries \mriteifenglish{School}{学\qquad 校} & \zihao{-2}\bfseries\mcm@tokens@schoolname\\
    \Xhline{1.2pt}
    \zihao{-2}\bfseries \mriteifenglish{Team No.}{参赛队号} & \zihao{-2}\bfseries\mcm@tokens@baominghao\\
    \Xhline{1.2pt}
    \multirow{3}{*}{\zihao{-2}\bfseries \mriteifenglish{Members}{队员姓名}} & \zihao{-2}\bfseries 1.\ \mcm@tokens@membera\hfill\null\\
    \cline{2-2}
      & \zihao{-2}\bfseries 2.\ \mcm@tokens@memberb\hfill\null\\
    \cline{2-2}
      & \zihao{-2}\bfseries 3.\ \mcm@tokens@memberc\hfill\null\\
    \Xhline{1.2pt}
  \end{tabularx}%
  \end{center}%
  \clearpage
  \thispagestyle{plain}%
  \setcounter{page}{1}%
  \phantomsection
  \pdfbookmark[1]{\mriteifenglish{Title}{标题}}{mrite-huawei-title}%
  \begin{center}%
    \includegraphics[width=.72\textwidth]{#2}\par
    \vspace{.75cm}%
    \begin{tabularx}{.95\textwidth}{@{}lX@{}}
      {\zihao{-2}\mriteifenglish{\rmfamily Title:}{\mriteli 题\quad 目：}} & \hfill\zihao{3}\mriteifenglish{\rmfamily}{\heiti}\bfseries \@title\hfill\null\\
      \cline{2-2}
    \end{tabularx}%
  \end{center}%
  \vspace{.3cm}%
}

% 生成封面, 使用\maketitle
\renewcommand{\maketitle}{\par
	\begingroup
      \newpage
      \global\@topnum\z@   % Prevents figures from going at top of page.
      \@maketitle
    \endgroup
  \global\let\thanks\relax
  \global\let\maketitle\relax
  \global\let\@maketitle\relax
  \global\let\@thanks\@empty
  \global\let\@author\@empty
  \global\let\@date\@empty
  \global\let\@title\@empty
  \global\let\title\relax
  \global\let\author\relax
  \global\let\date\relax
  \global\let\and\relax
}
\def\@maketitle{%
  \newpage
  \setcounter{page}{1}%
  {\centering \zihao{3}\bfseries \@title\par}%
  \vskip1ex
}

% 中文标题名称设置
\renewcommand\contentsname{\mcm@cap@contentsname}
\renewcommand\listfigurename{\mcm@cap@listfigurename}
\renewcommand\listtablename{\mcm@cap@listtablename}
\renewcommand\refname{\mcm@cap@refname}
\renewcommand\indexname{\mcm@cap@indexname}
\renewcommand\figurename{\mcm@cap@figurename}
\renewcommand\tablename{\mcm@cap@tablename}
\renewcommand\appendixname{\mcm@cap@appendixname}
\renewcommand\abstractname{\mcm@cap@abstractname}

% 中文标题格式设置
% 目录深度
\setcounter{secnumdepth}{3}
% 节标题格式, 居中, 使用\chinese命令修改计数器
\def\@seccntformat#1{\csname the#1\endcsname\ }
\renewcommand\thesection{\mriteifenglish{\arabic{section}}{\chinese{section}、}}
\renewcommand\thesubsection{\arabic{section}.\arabic{subsection}}
\renewcommand\thesubsubsection{\thesubsection.\arabic{subsubsection}}
\renewcommand\section{\@startsection{section}{1}{\z@}%
	{-3.5ex \@plus -1ex \@minus -.2ex}%
	{2.3ex \@plus.2ex}%
	{\mriteifenglish{\raggedright}{\centering}\normalfont\Large\bfseries\mriteheadingfont}}
\renewcommand\subsection{\@startsection{subsection}{2}{\z@}%
	{-3.25ex\@plus -1ex \@minus -.2ex}%
	{1.5ex \@plus .2ex}%
	{\normalfont\large\bfseries\mriteheadingfont}}

\renewcommand\subsubsection{\@startsection{subsubsection}{3}{\z@}%
	{-3.25ex\@plus -1ex \@minus -.2ex}%
	{1.5ex \@plus .2ex}%
	{\normalfont\normalsize\bfseries\mriteheadingfont}}


\renewcommand\paragraph{\@startsection{paragraph}{4}{\z@}%
	{3.25ex \@plus1ex \@minus.2ex}%
	{-1em}%
	{\normalfont\normalsize\bfseries\song}}  % 添加 \song

\renewcommand\subparagraph{\@startsection{subparagraph}{5}{\parindent}%
	{3.25ex \@plus1ex \@minus .2ex}%
	{-1em}%
	{\normalfont\normalsize\bfseries\song}}  % 添加 \song


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Define new environment and command
%% 摘要两个字设置为 4 号.
%% 定义摘要环境
% 字体钩子默认保持原模板样式；摘要变体可在局部分组内重定义。
\newcommand*{\mriteabstracttitlefont}{\bfseries}
\newcommand*{\mritekeywordslabelfont}{\songti\bfseries}
\renewenvironment{abstract}{%
\if@twocolumn
		\section*{\abstractname}%
	\else
	 \begin{center}%
	{\zihao{4}\mriteifenglish{\rmfamily\bfseries}{\mriteabstracttitlefont} \abstractname}%
	 \end{center}%
 	 \quotation
	\fi}
	{\if@twocolumn\else\endquotation\newpage\fi}
\renewenvironment{quotation}
	{\list{}{\listparindent 2em%
	 \itemindent \listparindent
	 \rightmargin\z@
	 \leftmargin\z@
	 \parsep \z@ \@plus\p@}%
	\item\relax}
	{\endlist}

\newcommand\keywords[1]{%
	\renewcommand{\mcm@tokens@keywords}{#1}
	\par
	\vskip1ex
	{\noindent\zihao{-4}\mriteifenglish{\rmfamily\bfseries}{\mritekeywordslabelfont}\mcm@cap@keywordsname\mriteifenglish{:}{：}}~{\mcm@tokens@keywords}
	}
% 定义附录

% \renewcommand{\setthesection}{\appendixname\Alph{section}}
% \renewcommand\appendix{\par
	% \setcounter{section}{0}%
	 % \setcounter{subsection}{0}%
	% \gdef\thesection{\appendixname\@Alph\c@section}}
% 重定义参考文献环境
\renewenvironment{thebibliography}[1]
     {\section*{\refname}%
      \@mkboth{\MakeUppercase\refname}{\MakeUppercase\refname}%
      \list{\@biblabel{\@arabic\c@enumiv}}%
           {\settowidth\labelwidth{\@biblabel{#1}}%
            \leftmargin\labelwidth
            \advance\leftmargin\labelsep
            \@openbib@code
            \usecounter{enumiv}%
            \let\p@enumiv\@empty
            \renewcommand\theenumiv{\@arabic\c@enumiv}}%
      \sloppy
      \clubpenalty4000
      \@clubpenalty \clubpenalty
      \widowpenalty4000%
      \sfcode`\.\@m}
     {\def\@noitemerr
       {\@latex@warning{Empty `thebibliography' environment}}%
      \endlist}

\newcommand*\tihao[1]{%
	\renewcommand{\mcm@tokens@tihao}{#1}}
\newcommand*\baominghao[1]{%
	\renewcommand{\mcm@tokens@baominghao}{#1}}
\newcommand*\schoolname[1]{%
	\renewcommand{\mcm@tokens@schoolname}{#1}}
\newcommand*\membera[1]{%
	\renewcommand{\mcm@tokens@membera}{#1}}
\newcommand*\memberb[1]{%
	\renewcommand{\mcm@tokens@memberb}{#1}}
\newcommand*\memberc[1]{%
	\renewcommand{\mcm@tokens@memberc}{#1}}
\newcommand*\supervisor[1]{%
	\renewcommand{\mcm@tokens@supervisor}{#1}}
\newcommand*\group[1]{%
	\renewcommand{\mcm@tokens@group}{#1}}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%% Initialization
 %%%数学定理相关的常量
\newcommand*{\mcm@cap@definition}{\mriteifenglish{Definition}{定义}}
\newcommand*{\mcm@cap@theorem}{\mriteifenglish{Theorem}{定理}}
\newcommand*{\mcm@cap@lemma}{\mriteifenglish{Lemma}{引理}}
\newcommand*{\mcm@cap@corollary}{\mriteifenglish{Corollary}{推论}}
\newcommand*{\mcm@cap@assumption}{\mriteifenglish{Assumption}{假设}}
\newcommand*{\mcm@cap@conjecture}{\mriteifenglish{Conjecture}{猜想}}
\newcommand*{\mcm@cap@axiom}{\mriteifenglish{Axiom}{公理}}
\newcommand*{\mcm@cap@principle}{\mriteifenglish{Principle}{定律}}
\newcommand*{\mcm@cap@problem}{\mriteifenglish{Problem}{问题}}
\newcommand*{\mcm@cap@example}{\mriteifenglish{Example}{例}}
\newcommand*{\mcm@cap@proof}{\mriteifenglish{Proof}{证明}}
\newcommand*{\mcm@cap@solution}{\mriteifenglish{Solution}{解}}
 %%%  中文标题名称
\newcommand*{\mcm@cap@contentsname}{\mriteifenglish{Contents}{目录}}
\newcommand*{\mcm@cap@listfigurename}{\mriteifenglish{List of Figures}{插图清单}}
\newcommand*{\mcm@cap@listtablename}{\mriteifenglish{List of Tables}{附表清单}}
\newcommand*{\mcm@cap@refname}{\mriteifenglish{References}{参考文献}}
\newcommand*{\mcm@cap@indexname}{\mriteifenglish{Index}{索引}}
\newcommand*{\mcm@cap@figurename}{\mriteifenglish{Figure}{图}}
\newcommand*{\mcm@cap@tablename}{\mriteifenglish{Table}{表}}
\newcommand*{\mcm@cap@appendixname}{\mriteifenglish{Appendix}{附录}}
\newcommand*{\mcm@cap@abstractname}{\mriteifenglish{Abstract}{摘要}}
 %%%  中文关键字
% \newcommand*{\mcm@cap@keywordsname}{\mriteifenglish{Keywords}{关键词}}
\newcommand*{\mcm@cap@keywordsname}{\mriteifenglish{Keywords}{关键词}}
%设置目录格式
% 节的目录格式
% \titlecontents{section}[0pt]{\vspace{2mm}\bfseries}
% {\thecontentslabel\hskip.5em}{}{\titlerule*[0.5pc]{.}\contentspage}
% % 小节的目录格式
% \titlecontents{subsection}[30pt]{\songti}
% {\thecontentslabel\hskip.5em}{}{\titlerule*[0.5pc]{.}\contentspage}
% \titlecontents{subsubsection}[55pt]{\songti}
% {\thecontentslabel\hskip.5em}{}{\titlerule*[0.5pc]{.}\contentspage}

% 上标文献
\newcommand{\upcite}[1]{\textsuperscript{\textsuperscript{\cite{#1}}}}
\newcommand{\supercite}[1]{\textsuperscript{\textsuperscript{\cite{#1}}}}


% 统一英文单项、区间、多项及句首引用；## 保留给 cleveref 的链接参数。
\newcommand*{\mcm@englishref}[3]{%
  \crefname{#1}{#2}{#3}%
  \Crefname{#1}{#2}{#3}%
  \crefformat{#1}{##2#2~##1##3}%
  \Crefformat{#1}{##2#2~##1##3}%
  \crefrangeformat{#1}{#3~##3##1##4--##5##2##6}%
  \Crefrangeformat{#1}{#3~##3##1##4--##5##2##6}%
  \crefmultiformat{#1}{#3~##2##1##3}{ and~##2##1##3}{, ##2##1##3}{, and~##2##1##3}%
  \Crefmultiformat{#1}{#3~##2##1##3}{ and~##2##1##3}{, ##2##1##3}{, and~##2##1##3}%
}

% 在 ctex 完成初始化后应用英文排版，兼容原有摘要变体的局部字体设置。
\AtBeginDocument{%
  \ifmriteenglish
    \setlength\parindent{1.5em}%
    \captionsetup[figure]{font={rm,minusfour,bf},labelsep=colon}%
    \captionsetup[table]{font={rm,minusfive,bf},labelsep=colon}%
    \renewcommand\lstlistingname{Listing}%
    \renewcommand\lstlistlistingname{List of Listings}%
    \renewcommand\contentsname{\mcm@cap@contentsname}%
    \renewcommand\listfigurename{\mcm@cap@listfigurename}%
    \renewcommand\listtablename{\mcm@cap@listtablename}%
    \renewcommand\refname{\mcm@cap@refname}%
    \renewcommand\indexname{\mcm@cap@indexname}%
    \renewcommand\figurename{\mcm@cap@figurename}%
    \renewcommand\tablename{\mcm@cap@tablename}%
    \renewcommand\appendixname{\mcm@cap@appendixname}%
    \renewcommand\abstractname{\mcm@cap@abstractname}%
    \mcm@englishref{figure}{Figure}{Figures}%
    \mcm@englishref{table}{Table}{Tables}%
    \mcm@englishref{equation}{Equation}{Equations}%
    \mcm@englishref{section}{Section}{Sections}%
    \mcm@englishref{subsection}{Section}{Sections}%
    \mcm@englishref{subsubsection}{Section}{Sections}%
    \mcm@englishref{appendix}{Appendix}{Appendices}%
    \mcm@englishref{definition}{Definition}{Definitions}%
    \mcm@englishref{theorem}{Theorem}{Theorems}%
    \mcm@englishref{lemma}{Lemma}{Lemmas}%
    \mcm@englishref{corollary}{Corollary}{Corollaries}%
    \mcm@englishref{assumption}{Assumption}{Assumptions}%
    \mcm@englishref{conjecture}{Conjecture}{Conjectures}%
    \mcm@englishref{axiom}{Axiom}{Axioms}%
    \mcm@englishref{principle}{Principle}{Principles}%
    \mcm@englishref{problem}{Problem}{Problems}%
    \mcm@englishref{example}{Example}{Examples}%
    \mcm@englishref{proof}{Proof}{Proofs}%
    \mcm@englishref{solution}{Solution}{Solutions}%
    \crefformat{equation}{#2Equation~(#1)#3}%
    \Crefformat{equation}{#2Equation~(#1)#3}%
  \fi
}
\endinput
