"""Deterministic Stage9 artifact production from a locked formal archive."""
import argparse
import csv
import io
import subprocess
from pathlib import Path
from .stage9_input import ROOT, STAGE8_SHA, IDENTITY, audit_archive, digest, json_bytes, read_json, require
from .stage9_selection import AJ, BOUNDARY, KEYS, PROXY, consolidate, family_policy

INPUT = 'research_inputs/b6/'
OUTPUT = 'results/b6/stage9_freeze/'


def csv_bytes(rows):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader()
    for row in rows:
        writer.writerow({k: ('true' if v else 'false') if isinstance(v, bool) else
                         ('UNDEFINED' if v is None else v) for k, v in row.items()})
    return stream.getvalue().encode('utf-8')


def build(archive, source_spec):
    spec, audit, pool, evidence = audit_archive(archive, source_spec)
    require(spec == source_spec, 'complete source spec mismatch')
    rows, dispositions, final = consolidate(pool, evidence['CandidatePeriodRows'])
    family = family_policy()
    files = {
        INPUT + 'stage9_source_spec.json': json_bytes(spec),
        INPUT + 'stage9_family_consolidation.json': json_bytes(family),
        INPUT + 'stage9_final_candidates.json': json_bytes(final),
        OUTPUT + 'stage8_input_audit.json': json_bytes(audit),
        OUTPUT + 'stage8_formal_evidence.json': json_bytes(evidence),
        OUTPUT + 'gbpjpy_representative_selection.csv': csv_bytes(rows),
        OUTPUT + 'candidate_disposition.csv': csv_bytes(dispositions),
    }
    config = dict(schema='b6-stage9-config-v1', Stage8Identity=IDENTITY,
        FormalRuntimeSHA256=spec['FileSHA256'], FamilyPolicy='AUDJPY singleton + one GBPJPY family representative',
        EntryScope=family['EntryScope'], SelectionKeys=KEYS, RelativeLotMarginProxy=PROXY,
        AutoRetainedAUDJPY=AJ, FinalCandidateCount=2,
        FinalCandidateSHA256=digest(files[INPUT + 'stage9_final_candidates.json']),
        FamilySHA256=digest(files[INPUT + 'stage9_family_consolidation.json']),
        SourceAuditSHA256=digest(files[OUTPUT + 'stage8_input_audit.json']),
        SourceSpecSHA256=digest(files[INPUT + 'stage9_source_spec.json']),
        Stage10RequiredFinalCandidateSHA256=digest(files[INPUT + 'stage9_final_candidates.json']),
        PortfolioEnabled=False, LiveEnabled=False, StrategyNumberingEnabled=False, **BOUNDARY)
    files[INPUT + 'stage9_config.json'] = json_bytes(config)
    files[OUTPUT + 'stage9_summary.json'] = json_bytes(dict(
        State='COMPLETE_STAGE9_FINAL_CANDIDATE_FREEZE', FamilyConsolidationExecuted=True,
        FinalCandidateFreezeExecuted=True, FinalCandidateCount=2, FinalCandidateSHA256=config['FinalCandidateSHA256'],
        SelectedGBPJPY=rows[0]['CandidateID'], FamilyCount=2, GBPFamilyCount=8, GBPSelectionScopeCount=6,
        ResearchHistoryUnchanged=True, **BOUNDARY))
    return files


def write_artifacts(files, root=ROOT):
    for name, data in files.items():
        path = Path(root)/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def release_manifest(root=ROOT):
    root = Path(root)
    names = set(read_json((root/INPUT/'stage8_release_manifest.json').read_bytes()))
    names.add(INPUT + 'stage8_release_manifest.json')
    for pattern in ('research_inputs/b6/stage9*.json', 'results/b6/stage9_freeze/*',
                    'src/research/b6/stage9*.py', 'tests/test_b6_stage9*.py', 'docs/b6/stage9*.md'):
        names.update(p.relative_to(root).as_posix() for p in root.glob(pattern) if p.is_file())
    names.discard(INPUT + 'stage9_release_manifest.json')
    return {n: digest((root/n).read_bytes()) for n in sorted(names)}


def verify_release(expected_sha, root=ROOT):
    root = Path(root)
    require(len(expected_sha) == 40 and all(c in '0123456789abcdef' for c in expected_sha), 'exact release SHA required')
    require(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip() == expected_sha,
            'Stage9 checkout SHA mismatch')
    require(not subprocess.check_output(['git', 'status', '--porcelain'], cwd=root, text=True).strip(),
            'clean Stage9 checkout required')
    subprocess.run(['git', 'merge-base', '--is-ancestor', STAGE8_SHA, expected_sha], cwd=root, check=True)
    manifest = read_json((root/INPUT/'stage9_release_manifest.json').read_bytes())
    require(manifest == release_manifest(root), 'Stage9 release integrity mismatch')
    config = read_json((root/INPUT/'stage9_config.json').read_bytes())
    require(digest((root/INPUT/'stage9_final_candidates.json').read_bytes()) == config['FinalCandidateSHA256'],
            'Stage10 final candidate hard gate mismatch')
    return config


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', required=True)
    parser.add_argument('--output-root', type=Path, required=True)
    args = parser.parse_args()
    spec = read_json((ROOT/INPUT/'stage9_source_spec.json').read_bytes())
    write_artifacts(build(args.archive, spec), args.output_root)
