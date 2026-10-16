"""Deterministic course retrieval. No embeddings, model calls or student-code execution."""
import re
from typing import Any
from app.knowledge.vector_store import LocalVectorStore, tokenize

# Course vocabulary expansion is shared by case and unit recall. These are
# algorithm/intent terms, never benchmark queries, labels or Case IDs.
FEATURES = {
    "newton": (r"newton|raphson|牛顿|切线法|切线方程|切线水平|f\(x\)\s*/\s*df\(x\)|fx\s*/\s*dfx", "牛顿法"),
    "bisection": (r"bisect|二分|折半|零点定理|根.*区间|括区间|f\(a\).*f\([bc]\)", "二分法"),
    "fixed": (r"fixed[ -]?point|不动点|简单迭代|压缩映射|lipschitz|g\s*\(\s*x\s*\)|g[′']|局部导数.*1|导数.*0\.[0-9]|φ|phi", "不动点迭代"),
    "initial": (r"initial|starting|start.*guess|初值|初始.*猜|起点|初猜|x_?0|x_\{0\}", "初值"),
    "multiple": (r"multiplic|multiple.*root|repeated.*root|double.*root|重根|重数|二重|三重|m.?重|f\(x\*\).*f[′']\(x\*\).*0", "重根"),
    "derivative": (r"derivative|slope|denominator|division|divide|zero.?division|导数|分母|除零|df\s*\(|f[′']", "导数"),
    "zero": (r"near.zero|zero.*derivative|derivative.*zero|zero.?division|导数.*(很小|为0|等于.?0|为零|阈值)|分母.*(小|0)|接近零|接近0|非常小|除零|水平切线|切线水平|derivative guard", "导数近零"),
    "residual": (r"residual|残差|函数值.*小|\|?f\(x\)\|?\s*[<≤]|f\(x_k\).*0|f\(x\).*1e-", "残差"),
    "error": (r"error|误差|精度|准确|真根|真实根", "误差"),
    "bound": (r"bound|priori|guarantee.*tolerance|how many|count|上界|界限|多少次|多少步|迭代次数|步数公式|区间.*长|初始.*L|迭代.*[nk]次", "误差上界"),
    "bracket": (r"bracket|endpoint|midpoint|sign|中点|端点|同号|异号|变号|区间|a=c|b=c|f\(a\).*f\(c\)", "端点区间"),
    "update": (r"update|changes|preserve|invariant|更新|保留|替换|缩小|哪半|仍.*包住|两端.*执行|a=c|b=c|同号.*处理|midpoint.*sign", "更新"),
    "condition": (r"condition|sufficient|assumption|continuity|continuous|前提|条件|连续|什么时候.*用|能否.*用|是否.*用|能用|初始化|保证.*根", "条件"),
    "contraction": (r"contract|lipschitz|压缩|自映射|映射.*区间|\|.*[gφ][′'].*\|.*[<≤].*1", "压缩映射"),
    "rearrange": (r"rearrang|rewrit|改写|构造|变形|格式选|迭代式.*选", "改写迭代"),
    "diverge": (r"diverg|oscillat|cycle|does not converge|发散|振荡|来回|周期|不收敛|不对|出错|交替|振幅增大|不趋于|[gφ][′'].*[>≥=].*1", "发散"),
    "derive": (r"deriv(e|ation)|taylor|tangent|linearization|推导|推得|推出来|怎么来|泰勒|切线|符号.*确定|subtract.*divided", "推导"),
    "order": (r"quadratic|linear convergence|convergence.*(order|rate)|estimate\s+p|收敛.*[阶速]|阶数|二次|平方|二阶|变慢|快慢|误差.*比|p.?值|估.*p|双对数", "收敛阶"),
    "numeric": (r"estimat|empirical|experiment|asymptotic|log\s*\(|误差表|数值|验证.*阶|渐近|估计.*阶|估计.*p|记录.*误差|误差比|双对数|浮点.*阶|序列.*阶", "数值验证"),
    "stop": (r"stop|terminat|max_?iter|tolerance|iteration cap|loop|break|while|exit|step size|步长|停机|停止|终止|跳出|死循环|超限|上限|容差|最大迭代|循环|未收敛状态", "停止准则"),
    "local": (r"local.*convergence|convergence.*theorem|局部.*(收敛|定理)|收敛邻域|充分接近|单根.*连续|二阶连续|初值.*邻域", "局部收敛定理"),
    "code": (r"python|code|program|implement|function|代码|程序|编程|实现|函数.*更新|def\s+|return\b", "代码"),
}
ALGORITHMS = {"newton", "bisection", "fixed"}
OUTSIDE = r"\bPDE\b|有限元|有限差分|热方程|Poisson|\bQR\b|矩阵特征|留数|residue theorem|围道|椭圆曲线|薛定谔|\bPPO\b|强化学习|神经网络|gradient descent|梯度下降|Romberg|复合梯形"
UNSUPPORTED = r"割线|弦截|secant|假位|false.position|Brent|Broyden|拟牛顿|阻尼因子|线搜索|复平面|complex.*basin|非线性方程组|Jacobian|雅可比|全部实根|所有实根"
STOP_WORDS = {"the", "a", "an", "of", "to", "and", "in", "is", "for", "how", "what", "why", "it", "with", "can", "i", "x", "f", "g", "n", "k"}


def features(text: str) -> set[str]:
    return {name for name, (pattern, _) in FEATURES.items() if re.search(pattern, text, re.I)}


def normalize(text: str) -> str:
    return text.lower() + " " + " ".join(FEATURES[key][1] for key in sorted(features(text)))


class CourseLexicalIndex(LocalVectorStore):
    def tokenize(self, text: str) -> list[str]:
        return [t for t in tokenize(text) if len(t) > 1 and t not in STOP_WORDS]

    def _split_text(self, text: str, chunk_size=256, overlap=50):
        # One metadata document per Case/unit: do not let chunk boundaries drop
        # an algorithm qualifier or duplicate matching terms across windows.
        return [{"text": text, "start": 0, "end": len(text)}] if text else []


def rank_documents(query: str, docs: list[dict[str, Any]]) -> list[tuple[str, float]]:
    index = CourseLexicalIndex()
    index.build_bm25_index(docs)
    return sorted(index.score_bm25(normalize(query)).items(), key=lambda row: (-row[1], row[0]))
