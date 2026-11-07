"""在原环境停止时校验完整状态目录副本，不输出文件内容。"""
from pathlib import Path
import hashlib
import json

source = Path('E:/Agent_project/Yuxi-main/Yuxi-main/docker/volumes')
target = Path('E:/Agent_project/Yuxi-main/ChuHai-agent/docker/volumes')
records = []
for original in sorted(source.rglob('*')):
    if not original.is_file():
        continue
    relative = original.relative_to(source)
    copied = target / relative
    if not copied.is_file():
        raise RuntimeError(f'Missing copied file: {relative}')
    def digest(path):
        with path.open('rb') as f:
            return hashlib.file_digest(f, 'sha256').hexdigest()
    sha = digest(original)
    if sha != digest(copied):
        raise RuntimeError(f'Copied bytes do not match: {relative}')
    records.append({'path': str(relative), 'bytes': original.stat().st_size, 'sha256': sha})
output = target.parents[1] / 'deployment/data_copy_verification.json'
output.write_text(json.dumps({'files': records, 'verified_file_count': len(records)}, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'Offline copy verified: {len(records)} files, {sum(r["bytes"] for r in records)} bytes')
