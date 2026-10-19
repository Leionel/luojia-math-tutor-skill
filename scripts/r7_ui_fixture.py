"""R7 browser seed layered on the existing offline R6.5 fixture."""
import argparse
from pathlib import Path
from r65_ui_fixture import create_fixture


def create_r7_fixture(directory):
    app = create_fixture(directory)
    from app.main_deps import get_learning_workspace
    from app.tutor.explorations import Explorations, Create, EditGraph, PersonalGraph, Execute, Revise
    workspace = app.dependency_overrides[get_learning_workspace]()
    service = Explorations(workspace)
    owner, identity = 'demo-user', 'r7-browser-history'
    try:
        service.get(owner, identity)
    except KeyError:
        service.create(owner, Create(request_id=identity, title='R7 私人初值判断', claim='Newton任意初值都收敛'))
        graph = PersonalGraph(nodes=[{'id': 'a', 'label': '初值'}, {'id': 'b', 'label': 'Newton收敛'}],
            edges=[{'id': 'edge', 'source': 'a', 'target': 'b', 'relation': 'implies',
                    'reason': '我曾把一次轨迹推广为任意初值'}])
        service.update(owner, identity, 'graph', EditGraph(request_id='graph', expected_revision=1, graph=graph))
        service.update(owner, identity, 'run', Execute(request_id='run', expected_revision=2,
            tasks=[dict(domain='root_finding', method='newton', function='x^3-2*x+2', initial_value=0, limit=6)],
            prediction='原先猜会收敛', metrics=['residual'], confirmed=True))
        service.update(owner, identity, 'revise', Revise(request_id='revise', expected_revision=3,
            claim='Newton并非任意初值都收敛', reason='初值0的参考计算在0与1间循环'))
    return app


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    import uvicorn
    uvicorn.run(create_r7_fixture(args.data_dir), host='127.0.0.1', port=args.port)
