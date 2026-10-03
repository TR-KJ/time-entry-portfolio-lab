"""Read-only Stage8 archive audit. No price loader, replay or metric recomputation."""
import csv
import gzip
import hashlib
import io
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STAGE8_SHA = '68d84078c2edc3108c0e3d6ca78d64d9b3d91ab5'
CONFIG_SHA = 'addcaab2c618df492bd73d7ae2d83d626d8c9513420c939da5f98625bd4704c7'
POOL_SHA = 'dfe25f015da9532535fb9aae3e580e59835f68cf6f9c0e2b0fc6b4a215ec6d68'
ELIGIBILITY_SHA = '7e62f0ca36a8160233a7f037c08f1c084cab49f418688718559afefa30adf852'
AJ = 'B6-AUDJPY-L-W0-E0950-H1440'
GBP = tuple('B6-GBPJPY-L-W0-' + s for s in (
    'E0835-H1415', 'E0835-H1325', 'E0765-H1440', 'E0870-H1290',
    'E0835-H1370', 'E0800-H1360', 'E0795-H1405', 'E0800-H1440'))
OUTSIDE = (GBP[2], GBP[3])
SCOPE = tuple(c for c in GBP if c not in OUTSIDE)
PERIODS = ('Discovery', 'Validation', 'Monitor', 'FullAvailable')
EXPECTED = dict(State='COMPLETE_STAGE8_OVERLAP_CORRELATION_ONLY',
    SourceCandidateCount=17, DeploymentIneligible=8, DeploymentEligible=9,
    EligibleAUDJPY=1, EligibleGBPJPY=8, PairCount=36, PeriodCount=4,
    PairwiseRows=144, CandidatePeriodRows=36, OverlapCorrelationExecuted=True,
    FamilyConsolidationExecuted=False, PortfolioExecuted=False, LiveChanged=False,
    NoRanking=True, NoSelection=True, NoRetuning=True, Strategy29PlusAssigned=False)
IDENTITY = dict(code_sha=STAGE8_SHA, config_sha256=CONFIG_SHA,
                eligibility_sha256=ELIGIBILITY_SHA, candidate_pool_sha256=POOL_SHA)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                       allow_nan=False) + '\n').encode('utf-8')


def read_json(data):
    def invalid(value):
        raise ValueError('non-finite JSON: ' + value)
    return json.loads(data, parse_constant=invalid)


def csv_rows(data, compressed=False):
    if compressed:
        data = gzip.decompress(data)
    return list(csv.DictReader(io.StringIO(data.decode('utf-8'))))


def validate_families(pool):
    points = pool['Candidates']
    ids = [p['CandidateID'] for p in points]
    require(pool['CandidateCount'] == 9 and len(ids) == len(set(ids)) == 9,
            'nine unique Stage8 candidates required')
    require([p['CandidateID'] for p in points if p['Symbol'] == 'AUDJPY'] == [AJ],
            'exact AUDJPY singleton required')
    require(tuple(p['CandidateID'] for p in points if p['Symbol'] == 'GBPJPY') == GBP,
            'exact GBP family and Stage8 relative order required')
    require(set(ids) == {AJ, *GBP}, 'candidate identity mismatch')
    scope = [p for p in points if p['Symbol'] == 'GBPJPY'
             and '13:00' <= p['FinalEntryJST'] < '14:00']
    require(tuple(p['CandidateID'] for p in scope) == SCOPE, 'exact 13h scope required')
    require(sorted(p['FinalEntryJST'] for p in scope) ==
            ['13:13', '13:22', '13:22', '13:50', '13:57', '13:58'], 'scope times mismatch')
    by_id = {p['CandidateID']: p for p in points}
    require(by_id[AJ]['FinalEntryJST'] == '15:50', 'singleton entry mismatch')
    require(by_id[OUTSIDE[0]]['FinalEntryJST'] == '12:45' and
            by_id[OUTSIDE[1]]['FinalEntryJST'] == '14:29' and
            by_id[OUTSIDE[1]]['SL'] == 20, 'outside-scope conditions mismatch')
    for p in points:
        require(p['FormalValidationStatus'] == 'PASS' and p['MonitorState'] == 'OBSERVED'
                and p['DeploymentReviewEligibility'] == 'ELIGIBLE', 'research status changed')
    return scope


def validate_source(identity, summary, pool, metrics, pairs):
    for key, value in IDENTITY.items():
        require(identity.get(key) == value, 'Stage8 identity mismatch: ' + key)
    for key, value in EXPECTED.items():
        require(type(summary.get(key)) is type(value) and summary[key] == value,
                'Stage8 hard gate: ' + key)
    validate_families(pool)
    ids = [p['CandidateID'] for p in pool['Candidates']]
    require(identity['candidate_count'] == 9 and identity['candidate_ids'] == ids,
            'identity candidate order mismatch')
    require(len(metrics) == 36 and [(r['CandidateID'], r['Period']) for r in metrics] ==
            [(c, period) for c in ids for period in PERIODS], 'candidate-period rows mismatch')
    require(len(pairs) == 144 and [(r['Period'], r['CandidateA'], r['CandidateB']) for r in pairs] ==
            [(p, a, b) for p in PERIODS for i, a in enumerate(ids) for b in ids[i+1:]],
            'pairwise rows mismatch')


def audit_archive(archive, spec=None):
    """Snapshot every required artifact once; ZIP inventory is never scientific input."""
    archive = Path(archive).resolve()
    require(archive.is_dir(), 'formal Stage8 archive inaccessible')
    ids = [*GBP[:7], AJ, GBP[7]]
    names = {
        'identity.json', 'effective_config.json', 'stage7_input_audit.json',
        'm1_input_audit.json', 'deployment_eligibility_audit.json', 'progress.json',
        'checkpoints.json', 'stage8_trade_ledger.csv.gz', 'stage8_diagnostics.csv.gz',
        'stage8_candidate_period_metrics.csv.gz', 'stage8_pairwise_metrics.csv.gz',
        'stage8_summary.json', 'stage8_review.json', 'stage8_review.zip',
        'stage8_candidate_pool.json', 'stage8_deployment_eligibility.json',
        *(f'shards/{c}.json' for c in ids),
        *(f'matrix_{p}_{m}.csv' for p in PERIODS for m in
          ('ActualExposureJaccard', 'LossJaccard', 'PearsonR', 'SpearmanR', 'TradeJaccard'))}
    actual = {p.relative_to(archive).as_posix() for p in archive.rglob('*') if p.is_file()}
    require(actual == names, 'archive file inventory mismatch; do not repair')
    blobs = {n: (archive/n).read_bytes() for n in sorted(names)}
    hashes = {n: digest(b) for n, b in blobs.items()}
    if spec is not None:
        require(spec['FileSHA256'] == hashes, 'formal archive exact-byte hash mismatch')
        require(spec['ExpectedSummary'] == EXPECTED and spec['Stage8Identity'] == IDENTITY,
                'source spec policy mismatch')
    for name, expected, local in (
        ('effective_config.json', CONFIG_SHA, 'research_inputs/b6/stage8_config.json'),
        ('stage8_candidate_pool.json', POOL_SHA, 'research_inputs/b6/stage8_candidate_pool.json'),
        ('stage8_deployment_eligibility.json', ELIGIBILITY_SHA, 'research_inputs/b6/stage8_deployment_eligibility.json')):
        require(hashes[name] == expected and blobs[name] == (ROOT/local).read_bytes(),
                'frozen Stage8 artifact mismatch: ' + name)
    j = lambda n: read_json(blobs[n])
    identity, summary, pool = j('identity.json'), j('stage8_summary.json'), j('stage8_candidate_pool.json')
    metrics = csv_rows(blobs['stage8_candidate_period_metrics.csv.gz'], True)
    pairs = csv_rows(blobs['stage8_pairwise_metrics.csv.gz'], True)
    validate_source(identity, summary, pool, metrics, pairs)
    config = j('effective_config.json')
    require(identity['runtime'] == config['formal_runtime'] and
            identity['calendar_sha256'] == config['calendar']['SHA256'] and
            identity['stage7_code_sha'] == config['stage7_code_sha'] and
            identity['scope'] == 'POST_VALIDATION_STRUCTURAL_ANALYSIS', 'runtime identity mismatch')
    progress = j('progress.json')
    require(progress == {**summary, 'CompletedJobs': 9, 'ExpectedJobs': 9}, 'incomplete progress')
    review = j('stage8_review.json')
    review_identity = {k: v for k, v in identity.items() if k != 'inputs'}
    review_identity['M1InputCount'] = 56
    require(review['Summary'] == summary and review['Identity'] == review_identity, 'review mismatch')
    manifest_path = ROOT/config['m1_manifest']['Manifest']
    require(digest(manifest_path.read_bytes()) == config['m1_manifest']['ManifestSHA256'], 'M1 metadata manifest mismatch')
    metadata = [{k: r[k] for k in ('Filename', 'SHA256')} for r in csv_rows(manifest_path.read_bytes())]
    m1_audit = j('m1_input_audit.json')
    require(len(metadata) == 56 and identity['inputs'] == metadata and
            m1_audit['Inputs'] == metadata and m1_audit['Status'] == 'PASS' and
            m1_audit['FileCount'] == 56 and m1_audit['ManifestSHA256'] == config['m1_manifest']['ManifestSHA256'],
            'saved M1 metadata audit mismatch')
    for name, local in (('stage7_input_audit.json', 'results/b6/stage8_freeze/stage7_input_audit.json'),
                        ('deployment_eligibility_audit.json', 'results/b6/stage8_freeze/deployment_eligibility_audit.json')):
        require(blobs[name] == (ROOT/local).read_bytes(), 'frozen audit mismatch: ' + name)
    checkpoints = j('checkpoints.json')
    require(checkpoints == {c: hashes[f'shards/{c}.json'] for c in ids}, 'checkpoint/shard hashes mismatch')
    for point in pool['Candidates']:
        require(j('shards/' + point['CandidateID'] + '.json')['candidate'] == point, 'shard conditions changed')
    ledger = csv_rows(blobs['stage8_trade_ledger.csv.gz'], True)
    require(len(ledger) == summary['TradeLedgerRows'] == 3043, 'ledger inventory mismatch')
    for name in names:
        if name.startswith('matrix_'):
            matrix = list(csv.reader(io.StringIO(blobs[name].decode('utf-8'))))
            require(matrix[0][1:] == ids and [r[0] for r in matrix[1:]] == ids
                    and all(len(r) == 10 for r in matrix), 'matrix identity/shape mismatch')
    with zipfile.ZipFile(io.BytesIO(blobs['stage8_review.zip'])) as z:
        inventory = [{'Name': i.filename, 'Bytes': i.file_size, 'CRC32': i.CRC} for i in sorted(z.infolist(), key=lambda i: i.filename)]
    source_spec = dict(schema='b6-stage9-source-spec-v1', Stage8Identity=IDENTITY,
                       ExpectedSummary=EXPECTED, CandidateIDs=ids, FileSHA256=hashes,
                       RequiredFiles=sorted(names), PerformanceSource='stage8_candidate_period_metrics.csv.gz',
                       ReviewZIPScientificSource=False)
    audit = dict(schema='b6-stage9-input-audit-v1', Status='PASS', FormalRoot=str(archive),
                 Identity=identity, Summary=summary, FileSHA256=hashes, FileCount=len(hashes),
                 CheckpointsVerified=9, MatrixInventoryVerified=20, ReviewZIPInventory=inventory,
                 ReviewZIPScientificSource=False, M1MetadataOnly=True, M1Read=False,
                 ReplayExecuted=False, CandidateTradeRecomputed=False, CorrelationRecomputed=False)
    evidence = dict(schema='b6-stage9-source-evidence-v1', SourceFile='stage8_candidate_period_metrics.csv.gz',
                    SourceSHA256=hashes['stage8_candidate_period_metrics.csv.gz'],
                    CandidatePeriodRows=metrics,
                    PairRowIdentities=[{k: r[k] for k in ('Period', 'CandidateA', 'CandidateB')} for r in pairs])
    return source_spec, audit, pool, evidence
