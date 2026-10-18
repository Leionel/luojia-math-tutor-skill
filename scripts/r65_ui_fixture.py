"""R6.5 browser fixture: existing runners, synthetic owned source, no model network."""
import argparse
from contextlib import asynccontextmanager
from pathlib import Path
from r61_ui_fixture import create_app


def create_fixture(directory):
    from app.api import routes_uploads
    from app.main_deps import get_repository
    app=create_app(directory)
    # Reuse the R6.4 phase adapter. Fixed advice JSON is not a routing response.
    from r64_r5_capture import routing_fixture
    original_lifespan=app.router.lifespan_context
    @asynccontextmanager
    async def lifespan(instance):
        with routing_fixture([]):
            async with original_lifespan(instance) as state:yield state
    app.router.lifespan_context=lifespan
    app.include_router(routes_uploads.router)
    repo=app.dependency_overrides[get_repository]()
    if not any(d['filename']=='R65合成学习资料.md' for d in repo.list_documents('demo-user')):
        repo.insert_document('R65合成学习资料.md','demo-user',
            '# Newton 的局部条件\n\n本段是浏览器验收合成资料，未经独立数学审核。\n'
            'Newton 局部收敛的条件不能自动推广到所有初值。请结合题目核对函数、根附近条件与初值。\n')
    if not any(d['filename']=='R65长公式资料.md' for d in repo.list_documents('demo-user')):
        formula='+'.join(rf'\frac{{x^{{{k}}}}}{{{k}}}' for k in range(1,21))
        repo.insert_document('R65长公式资料.md','demo-user',
            '# 布局检查合成资料\n\n此表达式仅检查长公式显示，不是教师审核材料。\n\n$$'+formula+'$$\n')
    return app


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--data-dir',type=Path,required=True);parser.add_argument('--port',type=int,default=8161)
    args=parser.parse_args()
    import uvicorn
    uvicorn.run(create_fixture(args.data_dir),host='127.0.0.1',port=args.port)
