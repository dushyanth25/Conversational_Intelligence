import os

import yaml

WORKFLOW_FILE = os.path.join(
    os.path.dirname(__file__), 
    "../../../workflows/argo/conversation-intelligence-workflow.yaml"
)

def test_workflow_valid_yaml():
    with open(WORKFLOW_FILE, 'r') as f:
        data = yaml.safe_load(f)
    assert data is not None
    assert data['kind'] == 'WorkflowTemplate'
    assert data['metadata']['name'] == 'conversation-pipeline-template'

def test_workflow_parameters():
    with open(WORKFLOW_FILE, 'r') as f:
        data = yaml.safe_load(f)
        
    parameters = {p['name'] for p in data['spec']['arguments']['parameters']}
    expected = {
        'audio_path', 'prompt_sheet', 'call_id', 'parallel_workers', 
        'parameters_per_batch', 'language', 'enable_vad', 'enable_speaker_tagging', 'gpu_count'
    }
    assert expected.issubset(parameters)

def test_workflow_dependencies():
    with open(WORKFLOW_FILE, 'r') as f:
        data = yaml.safe_load(f)
        
    # Find dag
    dag = next(t['dag'] for t in data['spec']['templates'] if 'dag' in t)
    tasks = {t['name']: t for t in dag['tasks']}
    
    assert 'preprocess' in tasks['vad'].get('dependencies', [])
    assert 'preprocess' in tasks['diarization'].get('dependencies', [])
    assert 'vad' in tasks['transcription'].get('dependencies', [])
    assert 'transcription' in tasks['alignment'].get('dependencies', [])
    assert 'diarization' in tasks['alignment'].get('dependencies', [])
    assert 'alignment' in tasks['speaker-tagging'].get('dependencies', [])
    assert 'speaker-tagging' in tasks['csv-generation'].get('dependencies', [])
    assert 'csv-generation' in tasks['prompt-parsing'].get('dependencies', [])
    assert 'prompt-parsing' in tasks['batch-creation'].get('dependencies', [])
    assert 'batch-creation' in tasks['insight-processing'].get('dependencies', [])
    assert 'insight-processing' in tasks['aggregation'].get('dependencies', [])
    assert 'aggregation' in tasks['persistence'].get('dependencies', [])

def test_workflow_gpu_requirements():
    with open(WORKFLOW_FILE, 'r') as f:
        data = yaml.safe_load(f)
        
    templates = {t['name']: t for t in data['spec']['templates']}
    
    # ASR and Diarization should have GPU configurable
    assert 'nvidia.com/gpu' in templates['transcription-task']['container']['resources']['requests']
    assert 'nvidia.com/gpu' in templates['diarization-task']['container']['resources']['requests']
    
    # Insights should NOT have GPU
    insight_resources = templates['insight-processing-task']['container'].get('resources', {}).get('requests', {})
    assert 'nvidia.com/gpu' not in insight_resources
