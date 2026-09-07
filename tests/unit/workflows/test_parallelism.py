import os

import yaml

WORKFLOW_FILE = os.path.join(
    os.path.dirname(__file__), 
    "../../../workflows/argo/conversation-intelligence-workflow.yaml"
)
BATCH_TEMPLATE_FILE = os.path.join(
    os.path.dirname(__file__), 
    "../../../workflows/argo/insight-batch-template.yaml"
)

def test_workflow_fan_out():
    with open(WORKFLOW_FILE, 'r') as f:
        data = yaml.safe_load(f)
        
    dag = next(t['dag'] for t in data['spec']['templates'] if 'dag' in t)
    tasks = {t['name']: t for t in dag['tasks']}
    
    insight_task = tasks['insight-processing']
    assert 'withParam' in insight_task
    assert insight_task['withParam'] == "{{tasks.batch-creation.outputs.parameters.batch-list}}"
    
def test_batch_template_fan_out():
    with open(BATCH_TEMPLATE_FILE, 'r') as f:
        data = yaml.safe_load(f)
        
    dag = next(t['dag'] for t in data['spec']['templates'] if 'dag' in t)
    tasks = {t['name']: t for t in dag['tasks']}
    
    insight_task = tasks['parallel-process']
    assert 'withParam' in insight_task
    assert insight_task['withParam'] == "{{tasks.fetch-batches.outputs.parameters.batch-list}}"

def test_no_gpu_in_insight_processing():
    with open(WORKFLOW_FILE, 'r') as f:
        data = yaml.safe_load(f)
        
    templates = {t['name']: t for t in data['spec']['templates']}
    insight_resources = templates['insight-processing-task']['container'].get('resources', {}).get('requests', {})
    assert 'nvidia.com/gpu' not in insight_resources

def test_batch_output_parameter():
    with open(WORKFLOW_FILE, 'r') as f:
        data = yaml.safe_load(f)
        
    templates = {t['name']: t for t in data['spec']['templates']}
    batch_creation = templates['batch-creation-task']
    assert 'outputs' in batch_creation
    assert batch_creation['outputs']['parameters'][0]['name'] == 'batch-list'
