import os

import yaml

WORKFLOW_FILE = os.path.join(
    os.path.dirname(__file__), 
    "../../../workflows/argo/conversation-intelligence-workflow.yaml"
)

def test_workflow_has_ttl():
    with open(WORKFLOW_FILE, 'r') as f:
        data = yaml.safe_load(f)
    
    assert 'ttlStrategy' in data['spec']
    assert data['spec']['ttlStrategy']['secondsAfterCompletion'] == 86400
    assert data['spec']['activeDeadlineSeconds'] == 14400

def test_workflow_tasks_have_resources():
    with open(WORKFLOW_FILE, 'r') as f:
        data = yaml.safe_load(f)
        
    for template in data['spec']['templates']:
        if 'container' in template:
            assert 'resources' in template['container']
            assert 'requests' in template['container']['resources']
            assert 'limits' in template['container']['resources']

def test_workflow_tasks_have_retries():
    with open(WORKFLOW_FILE, 'r') as f:
        data = yaml.safe_load(f)
        
    for template in data['spec']['templates']:
        if 'container' in template:
            assert 'retryStrategy' in template
            assert 'limit' in template['retryStrategy']
            assert 'activeDeadlineSeconds' in template

def test_gpu_isolation():
    with open(WORKFLOW_FILE, 'r') as f:
        data = yaml.safe_load(f)
        
    templates = {t['name']: t for t in data['spec']['templates']}
    
    asr = templates['transcription-task']['container']['resources']
    assert 'nvidia.com/gpu' in asr['requests']
    assert 'nvidia.com/gpu' in asr['limits']
    
    groq = templates['insight-processing-task']['container']['resources']
    assert 'nvidia.com/gpu' not in groq['requests']
    assert 'nvidia.com/gpu' not in groq['limits']
